"""
SAMVAD AI — IndicBERT Risk Classifier Evaluation Suite
Computes test metrics (accuracy, precision, recall, F1, macro-F1, per-class metrics, confusion matrix)
on the unseen held-out test set and evaluates natural unseen paraphrases for generalization.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("samvad.eval")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

TEST_PATH = DATA_DIR / "test.json"
CACHE_PATH = DATA_DIR / "embeddings_cache.pt"
CHECKPOINT_PATH = MODELS_DIR / "risk_classifier_head.pt"
METADATA_PATH = MODELS_DIR / "risk_classifier_metadata.json"
EVAL_RESULTS_PATH = MODELS_DIR / "risk_classifier_evaluation.json"

CLASSES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}


class IndicBERTRiskClassifier(nn.Module):
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


# Generalization test cases: completely unseen paraphrases with different wording
UNSEEN_PARAPHRASES = [
    # 1. Ordinary information request
    {
        "text": "Could you kindly guide me through the stages of tracking my grievance status online?",
        "expected_risk": "LOW",
        "category": "ordinary_info_request",
        "description": "Polite procedural tracking paraphrase",
    },
    # 2. Ordinary document question in Hindi
    {
        "text": "प्रणाम महोदय, क्या आप बता सकते हैं कि प्रमाणपत्र नवीनीकरण के लिए कौन से कागजात लगेंगे?",
        "expected_risk": "LOW",
        "category": "ordinary_info_request",
        "description": "Polite Hindi procedural documentation inquiry",
    },
    # 3. Sustained stress / feeling overwhelmed
    {
        "text": "It feels like an insurmountable hill right now and the unending paperwork is wearing me down.",
        "expected_risk": "MODERATE",
        "category": "sustained_stress",
        "description": "Metaphorical indirect emotional fatigue and coping burden",
    },
    # 4. Sustained stress in Marathi
    {
        "text": "या प्रकरणाचा माझ्या मनावर खूप ताण येत आहे आणि सततची चिंता सहन होत नाहीये.",
        "expected_risk": "MODERATE",
        "category": "sustained_stress",
        "description": "Sustained mental strain and enduring worry in Marathi",
    },
    # 5. Request for emotional / counseling support in Hinglish
    {
        "text": "Mujhe guidance chahiye kyonki situation se dimaag par bohot load pad raha hai roz roz.",
        "expected_risk": "MODERATE",
        "category": "support_request",
        "description": "Daily mental load seeking counseling guidance",
    },
    # 6. Serious distress / extreme fear
    {
        "text": "I am shivering from dread, I have nobody to turn to and I cannot endure this torment anymore.",
        "expected_risk": "HIGH",
        "category": "extreme_fear_isolation",
        "description": "Intense somatic dread, isolation, and collapse of endurance",
    },
    # 7. High vulnerability in Hindi
    {
        "text": "मेरे पास छत नहीं बची है और मैं इस ठंड में अपने बीमार बच्चे के साथ सड़क पर आ गया हूँ।",
        "expected_risk": "HIGH",
        "category": "acute_vulnerability",
        "description": "Acute homelessness and infant vulnerability",
    },
    # 8. High distress in Romanized Marathi
    {
        "text": "Mala khup bhiti vatat ahe, amche sarva kahi thap zale ahe ani amhi asahay jhalo ahot.",
        "expected_risk": "HIGH",
        "category": "extreme_vulnerability",
        "description": "Paralyzing helplessness and devastation in Romanized Marathi",
    },
    # 9. Acute safety crisis statement
    {
        "text": "I do not feel safe in my own dwelling right now, please send emergency intervention immediately.",
        "expected_risk": "CRITICAL",
        "category": "safety_concern",
        "description": "Immediate domestic safety concern demanding emergency help",
    },
    # 10. Safety inability paraphrase in Marathi
    {
        "text": "मला भीती वाटते की या परिस्थितीत मी स्वतःला सुरक्षित ठेवू शकणार नाही, कृपया त्वरित वाचवा.",
        "expected_risk": "CRITICAL",
        "category": "safety_concern",
        "description": "Inability to maintain personal safety with rescue plea in Marathi",
    },
]


def load_model() -> IndicBERTRiskClassifier:
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Trained checkpoint not found at {CHECKPOINT_PATH}")
    model = IndicBERTRiskClassifier()
    state_dict = torch.load(CHECKPOINT_PATH, weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def evaluate_test_set():
    if not TEST_PATH.exists():
        raise FileNotFoundError(f"Test split not found at {TEST_PATH}")
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        test_items = json.load(f)

    if not CACHE_PATH.exists():
        raise FileNotFoundError(f"Embeddings cache not found at {CACHE_PATH}")
    cache = torch.load(CACHE_PATH, weights_only=False)

    model = load_model()

    y_true = []
    y_pred = []
    y_probs = []

    with torch.no_grad():
        for item in test_items:
            text_id = item["id"]
            emb = cache[text_id].unsqueeze(0)
            logits = model(emb)[0]
            probs = F.softmax(logits, dim=-1).cpu().tolist()
            pred_idx = int(torch.argmax(logits).item())
            target_idx = CLASS_TO_IDX[item["risk_level"]]

            y_true.append(target_idx)
            y_pred.append(pred_idx)
            y_probs.append(probs)

    # 1. Confusion Matrix (4x4)
    num_classes = len(CLASSES)
    cm = [[0 for _ in range(num_classes)] for _ in range(num_classes)]
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1

    # 2. Overall Accuracy
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true) if len(y_true) > 0 else 0.0

    # 3. Per-class metrics
    per_class = {}
    f1_list = []
    for idx, class_name in enumerate(CLASSES):
        tp = cm[idx][idx]
        fp = sum(cm[r][idx] for r in range(num_classes) if r != idx)
        fn = sum(cm[idx][c] for c in range(num_classes) if c != idx)
        support = sum(cm[idx])

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        f1_list.append(f1)

        per_class[class_name] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    macro_f1 = sum(f1_list) / len(f1_list)

    # Print Report
    print("=" * 80)
    print("SAMVAD AI — IndicBERT Risk Classifier Evaluation Report (Held-Out Test Set)")
    print("=" * 80)
    print(f"Test Set Size: {len(test_items)} unseen samples")
    print(f"Overall Accuracy: {round(accuracy * 100, 2)}%")
    print(f"Macro F1 Score:   {round(macro_f1, 4)}\n")

    print("-" * 80)
    print(f"{'Class':<12} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 80)
    for c in CLASSES:
        metrics = per_class[c]
        print(f"{c:<12} | {metrics['precision']:<10.4f} | {metrics['recall']:<10.4f} | {metrics['f1']:<10.4f} | {metrics['support']:<8}")
    print("-" * 80)

    print("\nConfusion Matrix (Rows = Ground Truth, Columns = Predicted):")
    print(f"{'':<12} | {'LOW':<8} | {'MODERATE':<8} | {'HIGH':<8} | {'CRITICAL':<8}")
    print("-" * 55)
    for idx, c in enumerate(CLASSES):
        row = cm[idx]
        print(f"{c:<12} | {row[0]:<8} | {row[1]:<8} | {row[2]:<8} | {row[3]:<8}")

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": cm,
        "classes": CLASSES,
        "test_sample_count": len(test_items),
    }


def evaluate_generalization():
    print("\n" + "=" * 80)
    print("SAMVAD AI — Generalization Tests on Unseen Natural Paraphrases")
    print("=" * 80)

    try:
        from indicbert_service import indicbert_service
    except ImportError:
        from .indicbert_service import indicbert_service

    indicbert_service.load_model()
    model = load_model()

    paraphrase_results = []
    correct_count = 0

    for idx, test_case in enumerate(UNSEEN_PARAPHRASES, 1):
        text = test_case["text"]
        expected = test_case["expected_risk"]
        t = indicbert_service.get_embedding_tensor(text)
        if t is None:
            norm_emb = torch.zeros(768)
        else:
            norm_emb = F.normalize(t.unsqueeze(0), p=2, dim=1)[0]

        with torch.no_grad():
            logits = model(norm_emb.unsqueeze(0))[0]
            probs = F.softmax(logits, dim=-1).cpu().tolist()
            pred_idx = int(torch.argmax(logits).item())
            pred_class = IDX_TO_CLASS[pred_idx]
            conf = round(probs[pred_idx], 4)

        is_match = (pred_class == expected)
        if is_match:
            correct_count += 1

        prob_dict = {c: round(probs[i], 4) for i, c in enumerate(CLASSES)}
        status = "PASS" if is_match else "MISMATCH"

        print(f"\n[GP-{idx:02d}] {status} | Expected: {expected:<8} | Predicted: {pred_class:<8} (Conf: {conf})")
        print(f"       Category: {test_case['category']} — {test_case['description']}")
        print(f"       Text: \"{text[:75]}...\"")
        print(f"       Probabilities: {prob_dict}")

        paraphrase_results.append({
            "id": f"GP-{idx:02d}",
            "text": text,
            "category": test_case["category"],
            "expected": expected,
            "predicted": pred_class,
            "confidence": conf,
            "probabilities": prob_dict,
            "match": is_match,
        })

    gp_acc = correct_count / len(UNSEEN_PARAPHRASES)
    print("\n" + "-" * 80)
    print(f"Generalization Paraphrase Accuracy: {correct_count}/{len(UNSEEN_PARAPHRASES)} ({round(gp_acc * 100, 1)}%)")
    print("-" * 80)

    return {
        "paraphrase_count": len(UNSEEN_PARAPHRASES),
        "matches": correct_count,
        "accuracy": round(gp_acc, 4),
        "cases": paraphrase_results,
    }


def main():
    test_metrics = evaluate_test_set()
    gen_metrics = evaluate_generalization()

    eval_payload = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": "ai4bharat/IndicBERTv2-MLM-only + MLP Head",
        "held_out_test_metrics": test_metrics,
        "generalization_paraphrase_metrics": gen_metrics,
        "scientific_limitation_notice": (
            "This evaluation is performed on a prototype curated benchmark. "
            "It does NOT constitute clinical psychological validation, psychiatric diagnosis, "
            "or autonomous emergency triage. Production deployment requires expert-labelled, "
            "representative multilingual data and independent institutional validation."
        ),
    }

    with open(EVAL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_payload, f, indent=2, ensure_ascii=False)

    print(f"\nSaved evaluation results to: {EVAL_RESULTS_PATH}")


if __name__ == "__main__":
    main()
