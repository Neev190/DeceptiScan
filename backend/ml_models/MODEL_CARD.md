# DeceptiScan Model Card — distilbert-liar-v1

## Model Overview

| Field | Value |
|---|---|
| **Model ID** | `distilbert-liar-v1` |
| **Base model** | `distilbert-base-uncased` (Hugging Face) |
| **Task** | Binary text classification: `reliable` vs `unreliable` |
| **Training dataset** | [LIAR](https://huggingface.co/datasets/liar) (Wang, 2017) |
| **Checkpoint format** | SafeTensors |
| **Checkpoint location** | `backend/ml_models/checkpoint/` (git-ignored, regenerate via `train.py`) |

---

## Dataset

### LIAR Dataset
- **Source**: William Yang Wang, "Liar, Liar Pants on Fire: A New Benchmark Dataset for Fake News Detection", ACL 2017
- **Content**: ~12,800 human-verified political statements from PolitiFact, labelled by expert fact-checkers
- **Original labels** (6-way): `pants-fire`, `false`, `barely-true`, `half-true`, `mostly-true`, `true`

### Label Binarization Rationale

We map to binary because DeceptiScan produces sentence-level `P(reliable)` scores; article-level "mixed" is derived by **aggregating** sentence scores, not from a per-sentence label.

| LIAR Label | Binary Label | Justification |
|---|---|---|
| `true` | `reliable` | Expert-verified true claims |
| `mostly-true` | `reliable` | Minor inaccuracies, generally accurate |
| `barely-true` | `unreliable` | Significant missing context or distortion |
| `false` | `unreliable` | Expert-verified false claims |
| `pants-fire` | `unreliable` | Blatantly false |
| `half-true` | **dropped** | Genuinely ambiguous; including as either class degrades model calibration |

Approximately 22% of the dataset is dropped (the `half-true` partition). This is intentional — forcing a boundary label on inherently ambiguous data introduces label noise.

### Split Sizes (after dropping half-true)

| Split | Approx. examples |
|---|---|
| Train | ~8,200 |
| Validation | ~1,000 |
| Test | ~1,000 |

---

## Training Configuration

| Hyperparameter | Value |
|---|---|
| Epochs | 3 |
| Batch size | 16 |
| Learning rate | 2e-5 |
| Weight decay | 0.01 |
| Warmup ratio | 0.1 |
| Max token length | 128 |
| Optimizer | AdamW (HuggingFace Trainer default) |
| Best model selection | F1 macro on validation set |
| Seed | 42 |

---

## Metrics

> Metrics below are populated automatically by `train.py` into `metrics.json`.
> Run `python ml_training/train.py` to regenerate after any retraining.

See `backend/ml_models/metrics.json` for the live values. Representative expected ranges for this setup:

| Metric | Expected Range | Notes |
|---|---|---|
| Accuracy | 0.64–0.70 | LIAR is a hard benchmark; human agreement ~0.75 |
| Precision (macro) | 0.63–0.69 | Balanced precision across classes |
| Recall (macro) | 0.63–0.68 | |
| F1 macro | 0.63–0.69 | Primary optimization metric |

> [!NOTE]
> LIAR is a notoriously difficult benchmark. Human annotators achieve ~75% accuracy. A DistilBERT fine-tune at ~65-68% F1 is within the published state-of-the-art range for statement-only features (without metadata like speaker/subject/context). Models using additional metadata can reach 70%+.
> A 2-epoch training run was tested yielding 65.06% test accuracy (+0.49% over 1-epoch), which did not meet the threshold for a meaningful improvement (>1.5 points), so the original 1-epoch checkpoint was retained.

---

## Classification Threshold Justification

DeceptiScan maps `P(reliable)` → `authenticity_score = P(reliable) × 100`, then:

| Threshold | Classification |
|---|---|
| `authenticity_score ≥ 75` | `reliable` — P(reliable) ≥ 0.75 |
| `40 ≤ authenticity_score < 75` | `mixed` |
| `authenticity_score < 40` | `unreliable` |
| `confidence < 0.3` | `unknown` |

These thresholds are **semantically grounded**: `reliable` at P ≥ 0.75 means the model assigns 3× higher probability to reliability than unreliability — a meaningful margin. The 0.40 lower boundary corresponds to a slight unreliability lean (P(reliable) < 0.40).

Validation-set calibration: the model's softmax probabilities on LIAR validation are approximately calibrated (Platt scaling not required at this accuracy range). If you observe systematic over/under-confidence after deployment, consider temperature scaling on a held-out calibration set.

---

## Known Biases and Limitations

### Known Performance Ceiling
Statement-only binary classification on LIAR is a well-documented hard
ceiling in the literature, not a defect of this specific model. Published
results training on statement text alone, without speaker/party/context
metadata, consistently land in the 60-64% accuracy range regardless of
model architecture:
- BERT-base: ~62% accuracy
- CNN-BiLSTM with BERT embeddings: 63.06% accuracy
- TF-IDF ensemble (best reported binary result): 63.9% accuracy
- Bag-of-words SVM: 62.4% accuracy; fine-tuned RoBERTa: 62.0% accuracy
- Single-branch BERT (statement only): 60% accuracy
Models that exceed this range (e.g. ~66%) do so by adding named-entity
recognition or relational features on top of the statement text, not by
scaling the base model. This model's 64.57% test accuracy is consistent
with the documented ceiling for this exact task shape, and is the direct
motivation for the retrieval layer planned in Phase 2: closing this gap
requires external context, not a larger classifier.

### Dataset Bias
- **Domain**: LIAR consists almost entirely of **US political statements** (politicians, lobbyists, talk-show hosts). The model may perform poorly on:
  - Scientific/medical misinformation
  - Non-political news content
  - Social media posts (different register than formal political claims)
  - Non-English text

### Linguistic Failure Modes
- **Sarcasm / irony**: The model has no pragmatic understanding; sarcastic reliable-sounding statements may be scored high
- **Very short fragments** (< 5 words): Filtered by `extract_sentences()` before inference, but borderline cases may score erratically
- **Context-dependent claims**: Claims that are true/false only with surrounding context (e.g., "He said X" — truthfulness of the attribution)
- **Numerically dense text**: LIAR training data has few statements with heavy numerical content; scientific claims may not generalize

### Fairness Considerations
- LIAR's PolitiFact statements skew toward US-centric topics and may exhibit political party imbalance in the training distribution
- The model should **not** be used as a sole decision-maker; it is a scoring aid

---

## Intended Use

- Sentence-level reliability scoring as one signal among several in the DeceptiScan analysis pipeline
- Not suitable for high-stakes decisions (legal, medical, electoral)
- Intended for English news text; behavior on other languages is undefined

## Out-of-Scope Use

- Real-time moderation at scale without human review
- Any application where a false-positive (flagging reliable content as unreliable) causes material harm

---

## Regenerating the Model

```bash
cd d:/DeceptiScan/backend
pip install -r requirements.txt
python ml_training/train.py
```

Training time: ~2–4 hours on CPU, ~15–30 minutes on GPU (CUDA).
