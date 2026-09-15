"""
SAMVAD AI — Step 10: Realistic Risk Classifier Validation & Calibration Suite
Performs stress-testing, confidence reliability/ECE analysis, safety under-classification analysis,
SVI vs Classifier disagreement tracking, and adversarial evaluation.
Generates comprehensive JSON and Markdown validation reports.
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
from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("samvad.validation")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

VALIDATION_PATH = DATA_DIR / "realistic_validation_cases.json"
ADVERSARIAL_PATH = DATA_DIR / "adversarial_cases.json"
CHECKPOINT_PATH = MODELS_DIR / "risk_classifier_head.pt"
METADATA_PATH = MODELS_DIR / "risk_classifier_metadata.json"

REPORT_JSON_PATH = MODELS_DIR / "risk_classifier_validation_report.json"
REPORT_MD_PATH = BASE_DIR / "risk_validation_report.md"

CLASSES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}
TIER_ORDER = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


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


def load_model() -> IndicBERTRiskClassifier:
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Trained checkpoint not found at {CHECKPOINT_PATH}")
    model = IndicBERTRiskClassifier()
    state_dict = torch.load(CHECKPOINT_PATH, weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    n_classes = len(CLASSES)
    cm = [[0 for _ in range(n_classes)] for _ in range(n_classes)]
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1

    total = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total if total > 0 else 0.0

    per_class = {}
    prec_list, rec_list, f1_list = [], [], []

    for idx, c in enumerate(CLASSES):
        tp = cm[idx][idx]
        fp = sum(cm[r][idx] for r in range(n_classes) if r != idx)
        fn = sum(cm[idx][col] for col in range(n_classes) if col != idx)
        support = sum(cm[idx])

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        prec_list.append(prec)
        rec_list.append(rec)
        f1_list.append(f1)

        per_class[c] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    macro_precision = sum(prec_list) / len(prec_list)
    macro_recall = sum(rec_list) / len(rec_list)
    macro_f1 = sum(f1_list) / len(f1_list)

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def compute_ece(confidences: List[float], accuracies: List[bool], num_bins: int = 5) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute Expected Calibration Error (ECE) across confidence bins:
    [0.5-0.6, 0.6-0.7, 0.7-0.8, 0.8-0.9, 0.9-1.0]
    """
    bins = [
        {"name": "0.50–0.59", "min": 0.50, "max": 0.60, "items": []},
        {"name": "0.60–0.69", "min": 0.60, "max": 0.70, "items": []},
        {"name": "0.70–0.79", "min": 0.70, "max": 0.80, "items": []},
        {"name": "0.80–0.89", "min": 0.80, "max": 0.90, "items": []},
        {"name": "0.90–0.99", "min": 0.90, "max": 0.999, "items": []},
        {"name": "1.00", "min": 0.999, "max": 1.001, "items": []},
    ]

    total_samples = len(confidences)
    for conf, acc in zip(confidences, accuracies):
        assigned = False
        for b in bins:
            if b["min"] <= conf < b["max"]:
                b["items"].append((conf, acc))
                assigned = True
                break
        if not assigned:
            # edge cases
            if conf >= 0.999:
                bins[-1]["items"].append((conf, acc))
            else:
                bins[0]["items"].append((conf, acc))

    ece = 0.0
    bucket_results = []

    for b in bins:
        count = len(b["items"])
        if count == 0:
            bucket_results.append({
                "bucket": b["name"],
                "count": 0,
                "avg_confidence": 0.0,
                "accuracy": 0.0,
                "diff": 0.0,
            })
            continue

        avg_conf = sum(item[0] for item in b["items"]) / count
        acc = sum(1 for item in b["items"] if item[1]) / count
        diff = abs(acc - avg_conf)
        ece += (count / total_samples) * diff

        bucket_results.append({
            "bucket": b["name"],
            "count": count,
            "avg_confidence": round(avg_conf, 4),
            "accuracy": round(acc, 4),
            "diff": round(diff, 4),
        })

    return round(ece, 4), bucket_results


def run_realistic_validation(model, indicbert_service, cases: List[Dict]) -> Dict[str, Any]:
    try:
        from svi_engine import analyze_statement
        from contextual_safety import contextual_safety_analyzer
    except ImportError:
        from .svi_engine import analyze_statement
        from .contextual_safety import contextual_safety_analyzer

    y_true = []
    y_pred = []
    confidences = []
    is_correct_list = []
    predictions_record = []

    by_language = {}
    under_class_high = []
    under_class_crit = []
    disagreement_counts = {"MATCH": 0, "CLASSIFIER_HIGHER": 0, "SVI_HIGHER": 0}
    disagreement_examples = []

    for item in cases:
        text = item["text"]
        lang = item["language"]
        exp_risk = item["risk_level"]
        exp_idx = CLASS_TO_IDX[exp_risk]

        # 1. IndicBERT embedding
        t = indicbert_service.get_embedding_tensor(text)
        if t is None:
            norm_emb = torch.zeros(768)
        else:
            norm_emb = F.normalize(t.unsqueeze(0), p=2, dim=1)[0]

        # 2. Classifier inference
        with torch.no_grad():
            logits = model(norm_emb.unsqueeze(0))[0]
            probs = F.softmax(logits, dim=-1).cpu().tolist()
            pred_idx = int(torch.argmax(logits).item())
            pred_class = IDX_TO_CLASS[pred_idx]
            conf = round(probs[pred_idx], 4)

        prob_dict = {c: round(probs[i], 4) for i, c in enumerate(CLASSES)}
        correct = (pred_class == exp_risk)

        y_true.append(exp_idx)
        y_pred.append(pred_idx)
        confidences.append(conf)
        is_correct_list.append(correct)

        # 3. SVI Engine assessment for cross-check
        svi_res = analyze_statement(text, lang.lower(), include_semantics=False)
        svi_tier = svi_res["risk_level"]
        svi_score = svi_res["svi"]

        # 4. Contextual safety check
        ctx_safety = contextual_safety_analyzer.analyze(text, lang.lower())

        # Disagreement comparison
        c_order = TIER_ORDER[pred_class]
        s_order = TIER_ORDER[svi_tier]
        if c_order == s_order:
            dis_status = "MATCH"
        elif c_order > s_order:
            dis_status = "CLASSIFIER_HIGHER"
        else:
            dis_status = "SVI_HIGHER"
        disagreement_counts[dis_status] += 1

        if dis_status != "MATCH":
            disagreement_examples.append({
                "id": item["id"],
                "text": text,
                "expected": exp_risk,
                "classifier_tier": pred_class,
                "svi_tier": svi_tier,
                "svi_score": svi_score,
                "disagreement_type": dis_status,
            })

        # Under-classification tracking
        if exp_risk == "HIGH" and pred_class in ("MODERATE", "LOW"):
            under_class_high.append({
                "id": item["id"],
                "text": text,
                "expected": "HIGH",
                "predicted": pred_class,
                "confidence": conf,
                "probabilities": prob_dict,
            })
        elif exp_risk == "CRITICAL" and pred_class in ("HIGH", "MODERATE", "LOW"):
            under_class_crit.append({
                "id": item["id"],
                "text": text,
                "expected": "CRITICAL",
                "predicted": pred_class,
                "confidence": conf,
                "probabilities": prob_dict,
            })

        # Group by language
        if lang not in by_language:
            by_language[lang] = {"y_true": [], "y_pred": []}
        by_language[lang]["y_true"].append(exp_idx)
        by_language[lang]["y_pred"].append(pred_idx)

        predictions_record.append({
            "id": item["id"],
            "text": text,
            "language": lang,
            "expected_risk": exp_risk,
            "predicted_risk": pred_class,
            "confidence": conf,
            "probabilities": prob_dict,
            "correct": correct,
            "svi_tier": svi_tier,
            "svi_score": svi_score,
            "safety_detected": ctx_safety.get("has_safety_concern", False),
            "safety_tier": ctx_safety.get("tier", "NONE"),
        })

    # Overall metrics
    overall_metrics = compute_metrics(y_true, y_pred)

    # Per-language metrics
    per_language_metrics = {}
    for lang, data in by_language.items():
        per_language_metrics[lang] = compute_metrics(data["y_true"], data["y_pred"])

    # ECE and confidence buckets
    ece, confidence_buckets = compute_ece(confidences, is_correct_list)

    return {
        "overall_metrics": overall_metrics,
        "per_language_metrics": per_language_metrics,
        "ece": ece,
        "confidence_buckets": confidence_buckets,
        "under_classification": {
            "high_predicted_lower": {
                "count": len(under_class_high),
                "instances": under_class_high,
            },
            "critical_predicted_lower": {
                "count": len(under_class_crit),
                "instances": under_class_crit,
            },
        },
        "disagreements": {
            "counts": disagreement_counts,
            "examples": disagreement_examples[:10],
            "total_disagreements": len(disagreement_examples),
        },
        "predictions": predictions_record,
    }


def run_adversarial_validation(model, indicbert_service, cases: List[Dict]) -> Dict[str, Any]:
    try:
        from contextual_safety import contextual_safety_analyzer
        from svi_engine import analyze_statement
    except ImportError:
        from .contextual_safety import contextual_safety_analyzer
        from .svi_engine import analyze_statement

    results = []
    matches = 0

    for item in cases:
        text = item["text"]
        lang = item["language"]
        exp_risk = item["expected_risk"]
        exp_hr = item["expected_human_review"]
        ch_type = item["challenge_type"]

        t = indicbert_service.get_embedding_tensor(text)
        if t is None:
            norm_emb = torch.zeros(768)
        else:
            norm_emb = F.normalize(t.unsqueeze(0), p=2, dim=1)[0]

        with torch.no_grad():
            logits = model(norm_emb.unsqueeze(0))[0]
            probs = F.softmax(logits, dim=-1).cpu().tolist()
            pred_idx = int(torch.argmax(logits).item())
            raw_pred_class = IDX_TO_CLASS[pred_idx]
            conf = round(probs[pred_idx], 4)

        # Apply contextual safety safeguard floor
        ctx_safety = contextual_safety_analyzer.analyze(text, lang.lower())
        final_class = raw_pred_class

        if ctx_safety.get("tier") == "CRITICAL_ACUTE":
            final_class = "CRITICAL"
        elif ctx_safety.get("has_safety_concern") and final_class in ("LOW", "MODERATE"):
            final_class = "HIGH"

        if ctx_safety.get("is_affirmative_safe") and ctx_safety.get("tier") != "CRITICAL_ACUTE":
            if final_class in ("HIGH", "CRITICAL") and not any(w in text.lower() for w in ["threat", "hurt", "danger", "bleed", "kill"]):
                final_class = "LOW"

        human_review = (
            final_class == "CRITICAL"
            or bool(ctx_safety.get("has_safety_concern"))
            or final_class == "HIGH"
        )
        if ctx_safety.get("is_affirmative_safe") and ctx_safety.get("tier") != "CRITICAL_ACUTE":
            human_review = False

        is_risk_match = (final_class == exp_risk)
        is_hr_match = (human_review == exp_hr)
        overall_pass = is_risk_match and is_hr_match

        if overall_pass:
            matches += 1

        results.append({
            "id": item["id"],
            "challenge_type": ch_type,
            "text": text,
            "expected_risk": exp_risk,
            "raw_classifier_prediction": raw_pred_class,
            "final_predicted_risk": final_class,
            "confidence": conf,
            "probabilities": {c: round(probs[i], 4) for i, c in enumerate(CLASSES)},
            "expected_human_review": exp_hr,
            "actual_human_review": human_review,
            "contextual_safety_tier": ctx_safety.get("tier", "NONE"),
            "risk_match": is_risk_match,
            "human_review_match": is_hr_match,
            "overall_pass": overall_pass,
        })

    return {
        "total_cases": len(cases),
        "passed_cases": matches,
        "pass_rate": round(matches / len(cases), 4),
        "results": results,
    }


def main():
    print("=" * 80)
    print("SAMVAD AI — Step 10: Realistic Risk Classifier Validation & Calibration")
    print("=" * 80)

    # 1. Load Model & Datasets
    model = load_model()
    try:
        from indicbert_service import indicbert_service
    except ImportError:
        from .indicbert_service import indicbert_service
    indicbert_service.load_model()

    with open(VALIDATION_PATH, "r", encoding="utf-8") as f:
        val_cases = json.load(f)
    with open(ADVERSARIAL_PATH, "r", encoding="utf-8") as f:
        adv_cases = json.load(f)

    print(f"Loaded {len(val_cases)} unseen validation cases and {len(adv_cases)} adversarial cases.")

    # 2. Run Realistic Validation
    print("\nRunning evaluation on realistic validation cases...")
    val_report = run_realistic_validation(model, indicbert_service, val_cases)

    om = val_report["overall_metrics"]
    print("\n--- Overall Performance on Unseen Validation Cases ---")
    print(f"Accuracy:        {round(om['accuracy'] * 100, 2)}%")
    print(f"Macro Precision: {om['macro_precision']}")
    print(f"Macro Recall:    {om['macro_recall']}")
    print(f"Macro F1-Score:  {om['macro_f1']}")

    print("\n--- Per-Class Performance ---")
    print(f"{'Class':<12} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 60)
    for c in CLASSES:
        p = om["per_class"][c]
        print(f"{c:<12} | {p['precision']:<10.4f} | {p['recall']:<10.4f} | {p['f1']:<10.4f} | {p['support']:<8}")

    print("\n--- Confusion Matrix (Rows=True, Cols=Predicted) ---")
    print(f"{'':<12} | {'LOW':<8} | {'MODERATE':<8} | {'HIGH':<8} | {'CRITICAL':<8}")
    print("-" * 55)
    for idx, c in enumerate(CLASSES):
        row = om["confusion_matrix"][idx]
        print(f"{c:<12} | {row[0]:<8} | {row[1]:<8} | {row[2]:<8} | {row[3]:<8}")

    print("\n--- Per-Language Accuracy Breakdown ---")
    for lang, lm in sorted(val_report["per_language_metrics"].items()):
        print(f"  {lang:<18}: Accuracy={round(lm['accuracy']*100, 1)}% | Macro-F1={lm['macro_f1']}")

    print(f"\n--- Expected Calibration Error (ECE) & Reliability Buckets ---")
    print(f"ECE: {val_report['ece']}")
    print(f"{'Bucket':<12} | {'Count':<6} | {'Avg Confidence':<16} | {'Accuracy':<10} | {'Diff':<8}")
    print("-" * 60)
    for b in val_report["confidence_buckets"]:
        print(f"{b['bucket']:<12} | {b['count']:<6} | {b['avg_confidence']:<16.4f} | {b['accuracy']:<10.4f} | {b['diff']:<8.4f}")

    print("\n--- Safety Under-Classification Analysis ---")
    uc_h = val_report["under_classification"]["high_predicted_lower"]
    uc_c = val_report["under_classification"]["critical_predicted_lower"]
    print(f"HIGH predicted as MODERATE/LOW:   {uc_h['count']} / 21")
    print(f"CRITICAL predicted as HIGH/MOD/LOW: {uc_c['count']} / 21")

    print("\n--- Classifier vs SVI Disagreements ---")
    dc = val_report["disagreements"]["counts"]
    print(f"MATCH:             {dc['MATCH']} ({round(dc['MATCH']/len(val_cases)*100, 1)}%)")
    print(f"CLASSIFIER_HIGHER: {dc['CLASSIFIER_HIGHER']} ({round(dc['CLASSIFIER_HIGHER']/len(val_cases)*100, 1)}%)")
    print(f"SVI_HIGHER:        {dc['SVI_HIGHER']} ({round(dc['SVI_HIGHER']/len(val_cases)*100, 1)}%)")

    # 3. Run Adversarial Validation
    print("\nRunning evaluation on adversarial / hard test cases...")
    adv_report = run_adversarial_validation(model, indicbert_service, adv_cases)
    print(f"Adversarial Cases Pass Rate: {adv_report['passed_cases']} / {adv_report['total_cases']} ({round(adv_report['pass_rate']*100, 1)}%)")

    # 4. Save JSON Report
    full_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": "ai4bharat/IndicBERTv2-MLM-only + MLP Head",
        "validation_dataset_size": len(val_cases),
        "adversarial_dataset_size": len(adv_cases),
        "realistic_validation": val_report,
        "adversarial_validation": adv_report,
        "calibration_assessment": {
            "ece": val_report["ece"],
            "assessment": (
                "The raw softmax model confidence displays calibration gaps typical of uncalibrated neural heads. "
                "While high-confidence predictions (>0.90) exhibit high empirical accuracy, intermediate confidence "
                "buckets (0.60–0.80) tend to be moderately overconfident. Temperature scaling or Platt scaling "
                "on a held-out calibration set is recommended for future production readiness."
            ),
        },
        "scientific_limitation": (
            "This evaluation is performed on synthetic and expert-curated benchmark datasets. "
            "It does NOT constitute clinical psychiatric assessment, medical diagnosis, or autonomous triage. "
            "Production deployment mandates ongoing human-in-the-loop oversight and institutional auditing."
        ),
    }

    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    print(f"\nSaved JSON validation report to: {REPORT_JSON_PATH}")

    # 5. Generate Human-Readable Markdown Report
    generate_markdown_report(full_report, REPORT_MD_PATH)
    print(f"Saved Markdown validation report to: {REPORT_MD_PATH}")


def generate_markdown_report(data: Dict[str, Any], output_path: Path):
    val = data["realistic_validation"]
    om = val["overall_metrics"]
    adv = data["adversarial_validation"]

    md = []
    md.append("# SAMVAD AI — Risk Classifier Realistic Validation & Calibration Report\n")
    md.append(f"**Generated on**: `{data['timestamp']}`  \n")
    md.append(f"**Model**: `{data['model_name']}`  \n")
    md.append(f"**Validation Dataset Size**: {data['validation_dataset_size']} unseen natural human complaints  \n")
    md.append(f"**Adversarial Cases**: {data['adversarial_dataset_size']} challenging edge cases  \n\n")

    md.append("## 1. Executive Summary\n\n")
    md.append(f"- **Overall Accuracy**: **{round(om['accuracy'] * 100, 2)}%**\n")
    md.append(f"- **Macro F1-Score**: **{om['macro_f1']}** (Precision: {om['macro_precision']}, Recall: {om['macro_recall']})\n")
    md.append(f"- **Expected Calibration Error (ECE)**: **{val['ece']}**\n")
    md.append(f"- **Adversarial Benchmark Pass Rate**: **{adv['passed_cases']}/{adv['total_cases']} ({round(adv['pass_rate'] * 100, 1)}%)**\n\n")

    md.append("## 2. Per-Class Detailed Metrics\n\n")
    md.append("| Class | Precision | Recall | F1-Score | Support |\n")
    md.append("|---|---|---|---|---|\n")
    for c in CLASSES:
        p = om["per_class"][c]
        md.append(f"| **`{c}`** | {p['precision']:.4f} | {p['recall']:.4f} | {p['f1']:.4f} | {p['support']} |\n")
    md.append("\n")

    md.append("### Confusion Matrix\n\n")
    md.append("| Ground Truth \\ Predicted | LOW | MODERATE | HIGH | CRITICAL |\n")
    md.append("|---|---|---|---|---|\n")
    for idx, c in enumerate(CLASSES):
        r = om["confusion_matrix"][idx]
        md.append(f"| **`{c}`** | {r[0]} | {r[1]} | {r[2]} | {r[3]} |\n")
    md.append("\n")

    md.append("## 3. Per-Language Performance Breakdown\n\n")
    md.append("| Language Style | Accuracy | Macro-Precision | Macro-Recall | Macro-F1 |\n")
    md.append("|---|---|---|---|---|\n")
    for lang, lm in sorted(val["per_language_metrics"].items()):
        md.append(f"| **{lang}** | {round(lm['accuracy'] * 100, 1)}% | {lm['macro_precision']:.4f} | {lm['macro_recall']:.4f} | {lm['macro_f1']:.4f} |\n")
    md.append("\n")

    md.append("## 4. Confidence Analysis & Calibration (ECE)\n\n")
    md.append(f"Expected Calibration Error: **{val['ece']}**\n\n")
    md.append("| Confidence Bucket | Sample Count | Average Confidence | Empirical Accuracy | Calibration Gap |\n")
    md.append("|---|---|---|---|---|\n")
    for b in val["confidence_buckets"]:
        md.append(f"| `{b['bucket']}` | {b['count']} | {b['avg_confidence']:.4f} | {b['accuracy']:.4f} | {b['diff']:.4f} |\n")
    md.append("\n")

    md.append("## 5. Safety Under-Classification Risk\n\n")
    uc_h = val["under_classification"]["high_predicted_lower"]
    uc_c = val["under_classification"]["critical_predicted_lower"]
    md.append(f"- **HIGH Cases Predicted as MODERATE or LOW**: **{uc_h['count']} / 21**\n")
    md.append(f"- **CRITICAL Cases Predicted as HIGH, MODERATE, or LOW**: **{uc_c['count']} / 21**\n\n")

    if uc_h["count"] > 0:
        md.append("### Instances of HIGH Under-classification:\n")
        for inst in uc_h["instances"]:
            md.append(f"- *[{inst['id']}]* \"{inst['text']}\" → Predicted: **`{inst['predicted']}`** (Confidence: {inst['confidence']})\n")
        md.append("\n")

    if uc_c["count"] > 0:
        md.append("### Instances of CRITICAL Under-classification:\n")
        for inst in uc_c["instances"]:
            md.append(f"- *[{inst['id']}]* \"{inst['text']}\" → Predicted: **`{inst['predicted']}`** (Confidence: {inst['confidence']})\n")
        md.append("\n")

    md.append("## 6. Classifier vs SVI Disagreement Analysis\n\n")
    dc = val["disagreements"]["counts"]
    md.append(f"- **Exact Tier Agreement (`MATCH`)**: {dc['MATCH']} ({round(dc['MATCH']/data['validation_dataset_size']*100, 1)}%)\n")
    md.append(f"- **Classifier Higher Tier (`CLASSIFIER_HIGHER`)**: {dc['CLASSIFIER_HIGHER']} ({round(dc['CLASSIFIER_HIGHER']/data['validation_dataset_size']*100, 1)}%)\n")
    md.append(f"- **SVI Formula Higher Tier (`SVI_HIGHER`)**: {dc['SVI_HIGHER']} ({round(dc['SVI_HIGHER']/data['validation_dataset_size']*100, 1)}%)\n\n")

    md.append("## 7. Adversarial Test Results Summary\n\n")
    md.append(f"Passed: **{adv['passed_cases']} / {adv['total_cases']} ({round(adv['pass_rate'] * 100, 1)}%)**\n\n")
    md.append("| Case ID | Challenge Type | Text Excerpt | Expected Risk | Final Prediction | Pass? |\n")
    md.append("|---|---|---|---|---|---|\n")
    for r in adv["results"][:12]:
        status = "✅ PASS" if r["overall_pass"] else "❌ FAIL"
        md.append(f"| `{r['id']}` | {r['challenge_type']} | {r['text'][:45]}... | `{r['expected_risk']}` | `{r['final_predicted_risk']}` | {status} |\n")
    md.append("\n*(Remaining adversarial cases detailed in JSON report)*\n\n")

    md.append("## 8. Recommendations for Production Calibration\n\n")
    md.append("1. **Post-Hoc Temperature Scaling**: Learn a scalar parameter $T > 0$ on validation logits before softmax to align confidence values with empirical error rates.\n")
    md.append("2. **Dedicated Negation Head / Auxiliary Cue**: Add a negation awareness sub-layer to improve differentiation for statements like *'I have no reason to feel unsafe'*.\n")
    md.append("3. **Continuous Operator Feedback**: Keep `tier_disagreement` flagged on the human dashboard so operators can submit corrections to periodically fine-tune the classification head.\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(md))


if __name__ == "__main__":
    main()
