# SAMVAD AI — Risk Classifier Realistic Validation & Calibration Report
**Generated on**: `2026-09-15T08:05:53.373551+00:00`  
**Model**: `ai4bharat/IndicBERTv2-MLM-only + MLP Head`  
**Validation Dataset Size**: 84 unseen natural human complaints  
**Adversarial Cases**: 24 challenging edge cases  

## 1. Executive Summary

- **Overall Accuracy**: **89.29%**
- **Macro F1-Score**: **0.8939** (Precision: 0.898, Recall: 0.8929)
- **Expected Calibration Error (ECE)**: **0.054**
- **Adversarial Benchmark Pass Rate**: **19/24 (79.2%)**

## 2. Per-Class Detailed Metrics

| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **`LOW`** | 1.0000 | 1.0000 | 1.0000 | 21 |
| **`MODERATE`** | 1.0000 | 0.9524 | 0.9756 | 21 |
| **`HIGH`** | 0.7500 | 0.8571 | 0.8000 | 21 |
| **`CRITICAL`** | 0.8421 | 0.7619 | 0.8000 | 21 |

### Confusion Matrix

| Ground Truth \ Predicted | LOW | MODERATE | HIGH | CRITICAL |
|---|---|---|---|---|
| **`LOW`** | 21 | 0 | 0 | 0 |
| **`MODERATE`** | 0 | 20 | 1 | 0 |
| **`HIGH`** | 0 | 0 | 18 | 3 |
| **`CRITICAL`** | 0 | 0 | 5 | 16 |

## 3. Per-Language Performance Breakdown

| Language Style | Accuracy | Macro-Precision | Macro-Recall | Macro-F1 |
|---|---|---|---|---|
| **English** | 100.0% | 1.0000 | 1.0000 | 1.0000 |
| **Hindi** | 93.8% | 0.9500 | 0.9375 | 0.9365 |
| **Hinglish** | 91.7% | 0.9375 | 0.9167 | 0.9143 |
| **Marathi** | 87.5% | 0.8750 | 0.8750 | 0.8750 |
| **Mixed** | 83.3% | 0.9000 | 0.8333 | 0.8125 |
| **Romanized Marathi** | 75.0% | 0.7500 | 0.7500 | 0.7429 |

## 4. Confidence Analysis & Calibration (ECE)

Expected Calibration Error: **0.054**

| Confidence Bucket | Sample Count | Average Confidence | Empirical Accuracy | Calibration Gap |
|---|---|---|---|---|
| `0.50–0.59` | 8 | 0.5322 | 0.2500 | 0.2822 |
| `0.60–0.69` | 6 | 0.6249 | 0.6667 | 0.0417 |
| `0.70–0.79` | 1 | 0.7824 | 1.0000 | 0.2176 |
| `0.80–0.89` | 3 | 0.8659 | 0.6667 | 0.1993 |
| `0.90–0.99` | 44 | 0.9726 | 1.0000 | 0.0274 |
| `1.00` | 22 | 0.9998 | 1.0000 | 0.0002 |

## 5. Safety Under-Classification Risk

- **HIGH Cases Predicted as MODERATE or LOW**: **0 / 21**
- **CRITICAL Cases Predicted as HIGH, MODERATE, or LOW**: **5 / 21**

### Instances of CRITICAL Under-classification:
- *[VAL-073]* "Ghar ke bahar armed men khade hain aur wo door break karne ki koshish kar rahe hain, urgent help bhejo." → Predicted: **`HIGH`** (Confidence: 0.4215)
- *[VAL-077]* "काही लोकांनी माझ्या घरावर दगडफेक केली आहे आणि ते दरवाजा तोडण्याचा प्रयत्न करत आहेत." → Predicted: **`HIGH`** (Confidence: 0.8281)
- *[VAL-079]* "Mala atta safe vatat nahiye ya jagevar, konitari mala attack karel ashi bhiti vat-te." → Predicted: **`HIGH`** (Confidence: 0.5874)
- *[VAL-082]* "I do not feel safe right now, door ke bahar log shivigol de rahe hain and threatening to burn the place." → Predicted: **`HIGH`** (Confidence: 0.5477)
- *[VAL-084]* "Meri jaan khatre mein hai, te lok weapon ghevun aale ahet, save me right now." → Predicted: **`HIGH`** (Confidence: 0.5802)

## 6. Classifier vs SVI Disagreement Analysis

- **Exact Tier Agreement (`MATCH`)**: 24 (28.6%)
- **Classifier Higher Tier (`CLASSIFIER_HIGHER`)**: 60 (71.4%)
- **SVI Formula Higher Tier (`SVI_HIGHER`)**: 0 (0.0%)

## 7. Adversarial Test Results Summary

Passed: **19 / 24 (79.2%)**

| Case ID | Challenge Type | Text Excerpt | Expected Risk | Final Prediction | Pass? |
|---|---|---|---|---|---|
| `ADV-01` | affirmative_safe_declaration | I feel safe now.... | `LOW` | `LOW` | ✅ PASS |
| `ADV-02` | past_fear_resolved | I was frightened earlier during the confronta... | `LOW` | `LOW` | ✅ PASS |
| `ADV-03` | negation_of_unsafe | I have no reason to feel unsafe here, I just ... | `LOW` | `HIGH` | ❌ FAIL |
| `ADV-04` | technical_word_pressure | What is the maximum water pressure limit reco... | `LOW` | `LOW` | ✅ PASS |
| `ADV-05` | hindi_affirmative_safe | मैं अब पूरी तरह से सुरक्षित हूँ, बस शिकायत का... | `LOW` | `LOW` | ✅ PASS |
| `ADV-06` | hindi_idiomatic_fear_pressure | मैंने बिना किसी डर या दबाव के अपना औपचारिक आव... | `LOW` | `LOW` | ✅ PASS |
| `ADV-07` | marathi_affirmative_safe | मी आता सुरक्षित आहे, पूर्वीची समस्या सुटली अस... | `LOW` | `LOW` | ✅ PASS |
| `ADV-08` | hinglish_affirmative_safe | Main abhi completely safe hoon, police ne com... | `LOW` | `LOW` | ✅ PASS |
| `ADV-09` | polite_framing_acute_distress | Excuse me, I most respectfully submit that I ... | `HIGH` | `HIGH` | ✅ PASS |
| `ADV-10` | polite_framing_severe_vulnerability | आदरणीय महोदय, सविनय निवेदन है कि मेरा मकान खा... | `HIGH` | `HIGH` | ✅ PASS |
| `ADV-11` | ultra_short_safety_statement | Help me I am unsafe.... | `CRITICAL` | `CRITICAL` | ✅ PASS |
| `ADV-12` | short_marathi_safety_cry | वाचवा, माझा जीव धोक्यात आहे!... | `CRITICAL` | `CRITICAL` | ✅ PASS |

*(Remaining adversarial cases detailed in JSON report)*

## 8. Recommendations for Production Calibration

1. **Post-Hoc Temperature Scaling**: Learn a scalar parameter $T > 0$ on validation logits before softmax to align confidence values with empirical error rates.
2. **Dedicated Negation Head / Auxiliary Cue**: Add a negation awareness sub-layer to improve differentiation for statements like *'I have no reason to feel unsafe'*.
3. **Continuous Operator Feedback**: Keep `tier_disagreement` flagged on the human dashboard so operators can submit corrections to periodically fine-tune the classification head.
