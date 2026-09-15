"""
SAMVAD AI — IndicBERT Risk Classifier Training Pipeline
Trains the neural classification head on top of 768-dim IndicBERT embeddings.
Implements stratified splitting, caching, PyTorch training loop, checkpointing, and metadata logging.
"""

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import random
import time
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("samvad.train")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_PATH = DATA_DIR / "complaints_dataset.json"
CACHE_PATH = DATA_DIR / "embeddings_cache.pt"
CHECKPOINT_PATH = MODELS_DIR / "risk_classifier_head.pt"
METADATA_PATH = MODELS_DIR / "risk_classifier_metadata.json"

TRAIN_PATH = DATA_DIR / "train.json"
VAL_PATH = DATA_DIR / "val.json"
TEST_PATH = DATA_DIR / "test.json"

CLASSES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}

RANDOM_SEED = 42


def set_seed(seed: int = 42):
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class IndicBERTRiskClassifier(nn.Module):
    """
    Classification head matching the architecture specified in requirements:
    IndicBERT embedding (768) -> LayerNorm -> Dropout(0.2) -> Linear(768 -> 128) -> GELU -> Dropout(0.1) -> Linear(128 -> 4)
    """

    def __init__(self, input_dim: int = 768, num_classes: int = 4):
        super().__init__()
        self.layer_norm = nn.LayerNorm(input_dim)
        self.dropout1 = nn.Dropout(0.2)
        self.dense1 = nn.Linear(input_dim, 128)
        self.activation = nn.GELU()
        self.dropout2 = nn.Dropout(0.1)
        self.dense2 = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.layer_norm(x)
        x = self.dropout1(x)
        x = self.dense1(x)
        x = self.activation(x)
        x = self.dropout2(x)
        logits = self.dense2(x)
        return logits


class ComplaintDataset(Dataset):
    def __init__(self, items: List[Dict], embeddings_map: Dict[str, torch.Tensor]):
        self.items = items
        self.embeddings_map = embeddings_map

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        text_id = item["id"]
        emb = self.embeddings_map[text_id]
        label = CLASS_TO_IDX[item["risk_level"]]
        return emb, torch.tensor(label, dtype=torch.long)


def stratified_split(
    dataset: List[Dict],
    train_ratio: float = 0.75,
    val_ratio: float = 0.15,
    test_ratio: float = 0.10,
    seed: int = 42,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Split dataset stratified by risk_level to ensure balanced class distributions in train, val, and test.
    """
    rng = random.Random(seed)
    by_class: Dict[str, List[Dict]] = {c: [] for c in CLASSES}
    for item in dataset:
        by_class[item["risk_level"]].append(item)

    train_set, val_set, test_set = [], [], []

    for c, items in by_class.items():
        shuffled = list(items)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        # remainder goes to test
        train_set.extend(shuffled[:n_train])
        val_set.extend(shuffled[n_train : n_train + n_val])
        test_set.extend(shuffled[n_train + n_val :])

    rng.shuffle(train_set)
    rng.shuffle(val_set)
    rng.shuffle(test_set)
    return train_set, val_set, test_set


def compute_or_load_embeddings(dataset: List[Dict]) -> Dict[str, torch.Tensor]:
    """
    Pre-computes and caches 768-dim normalized IndicBERT embeddings for the dataset.
    """
    if CACHE_PATH.exists():
        logger.info("Loading cached embeddings from %s ...", CACHE_PATH)
        cache = torch.load(CACHE_PATH, weights_only=False)
        # Check if all IDs in dataset are present in cache
        if all(item["id"] in cache for item in dataset):
            logger.info("All %d embeddings loaded from cache.", len(dataset))
            return cache

    logger.info("Computing embeddings using IndicBERT for %d items...", len(dataset))
    try:
        from indicbert_service import indicbert_service
    except ImportError:
        from .indicbert_service import indicbert_service

    indicbert_service.load_model()
    embeddings_map = {}

    for idx, item in enumerate(dataset, 1):
        t = indicbert_service.get_embedding_tensor(item["text"])
        if t is None:
            raise RuntimeError(f"Could not compute embedding for item {item['id']}")
        # L2 normalize
        norm_t = F.normalize(t.unsqueeze(0), p=2, dim=1)[0]
        embeddings_map[item["id"]] = norm_t.cpu()
        if idx % 50 == 0 or idx == len(dataset):
            logger.info("Embedded %d / %d items", idx, len(dataset))

    torch.save(embeddings_map, CACHE_PATH)
    logger.info("Saved embeddings cache to %s", CACHE_PATH)
    return embeddings_map


def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module) -> Tuple[float, float, float]:
    """
    Compute loss, accuracy, and macro F1 on a dataset loader.
    """
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for embeddings, labels in loader:
            outputs = model(embeddings)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * len(labels)
            preds = torch.argmax(outputs, dim=-1)
            correct += (preds == labels).sum().item()
            total += len(labels)
            all_preds.extend(preds.cpu().tolist())
            all_targets.extend(labels.cpu().tolist())

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)

    # Calculate macro F1
    f1s = []
    for c in range(len(CLASSES)):
        tp = sum(1 for p, t in zip(all_preds, all_targets) if p == c and t == c)
        fp = sum(1 for p, t in zip(all_preds, all_targets) if p == c and t != c)
        fn = sum(1 for p, t in zip(all_preds, all_targets) if p != c and t == c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        f1s.append(f1)

    macro_f1 = sum(f1s) / len(f1s)
    return avg_loss, acc, macro_f1


def train():
    set_seed(RANDOM_SEED)
    logger.info("Starting SAMVAD AI Risk Classifier Training...")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        full_dataset = json.load(f)

    logger.info("Dataset loaded: %d examples.", len(full_dataset))

    # Stratified split: 75% train, 15% val, 10% test
    train_set, val_set, test_set = stratified_split(
        full_dataset,
        train_ratio=0.75,
        val_ratio=0.15,
        test_ratio=0.10,
        seed=RANDOM_SEED,
    )

    logger.info("Split sizes: Train=%d, Val=%d, Test=%d", len(train_set), len(val_set), len(test_set))

    # Save splits
    with open(TRAIN_PATH, "w", encoding="utf-8") as f:
        json.dump(train_set, f, indent=2, ensure_ascii=False)
    with open(VAL_PATH, "w", encoding="utf-8") as f:
        json.dump(val_set, f, indent=2, ensure_ascii=False)
    with open(TEST_PATH, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)

    # Compute or load embeddings
    embeddings_map = compute_or_load_embeddings(full_dataset)

    train_dataset = ComplaintDataset(train_set, embeddings_map)
    val_dataset = ComplaintDataset(val_set, embeddings_map)
    test_dataset = ComplaintDataset(test_set, embeddings_map)

    batch_size = 16
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=len(val_dataset), shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=len(test_dataset), shuffle=False)

    # Build model
    model = IndicBERTRiskClassifier(input_dim=768, num_classes=4)
    criterion = nn.CrossEntropyLoss()
    learning_rate = 0.001
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=5)

    max_epochs = 60
    best_val_f1 = -1.0
    best_weights = None
    best_epoch = 0

    logger.info("Beginning training loop (%d epochs)...", max_epochs)
    for epoch in range(1, max_epochs + 1):
        model.train()
        running_loss = 0.0
        for embeddings, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(embeddings)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * len(labels)

        train_loss = running_loss / len(train_dataset)
        val_loss, val_acc, val_f1 = evaluate(model, val_loader, criterion)
        scheduler.step(val_f1)

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 10 == 0 or epoch == max_epochs:
            logger.info(
                "Epoch %3d/%3d | Train Loss: %.4f | Val Loss: %.4f | Val Acc: %.2f%% | Val Macro-F1: %.4f (Best: %.4f @ epoch %d)",
                epoch,
                max_epochs,
                train_loss,
                val_loss,
                val_acc * 100,
                val_f1,
                best_val_f1,
                best_epoch,
            )

    logger.info("Training complete. Best epoch: %d with Val Macro-F1: %.4f", best_epoch, best_val_f1)

    # Save best checkpoint
    torch.save(best_weights, CHECKPOINT_PATH)
    logger.info("Saved trained checkpoint to: %s", CHECKPOINT_PATH)

    # Evaluate best model on test set
    model.load_state_dict(best_weights)
    val_loss, val_acc, val_f1 = evaluate(model, val_loader, criterion)
    test_loss, test_acc, test_f1 = evaluate(model, test_loader, criterion)

    logger.info("Final Test Performance: Loss: %.4f | Acc: %.2f%% | Macro-F1: %.4f", test_loss, test_acc * 100, test_f1)

    metadata = {
        "model_name": "ai4bharat/IndicBERTv2-MLM-only + MLP Head",
        "architecture": "LayerNorm(768) -> Dropout(0.2) -> Linear(768, 128) -> GELU -> Dropout(0.1) -> Linear(128, 4)",
        "dataset_size": len(full_dataset),
        "train_count": len(train_set),
        "val_count": len(val_set),
        "test_count": len(test_set),
        "random_seed": RANDOM_SEED,
        "epochs_trained": max_epochs,
        "best_epoch": best_epoch,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "class_mapping": CLASS_TO_IDX,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "validation_metrics": {
            "loss": round(val_loss, 4),
            "accuracy": round(val_acc, 4),
            "macro_f1": round(val_f1, 4),
        },
        "test_metrics": {
            "loss": round(test_loss, 4),
            "accuracy": round(test_acc, 4),
            "macro_f1": round(test_f1, 4),
        },
        "disclaimer": (
            "Prototype AI risk classifier for human operator decision-support. "
            "Not clinically validated for psychiatric assessment or autonomous triage."
        ),
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Saved metadata to: %s", METADATA_PATH)
    return metadata


if __name__ == "__main__":
    train()
