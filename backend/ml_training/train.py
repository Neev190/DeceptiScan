"""
Train a binary DistilBERT classifier on the LIAR dataset for DeceptiScan.

LIAR dataset (Wang, 2017): statement-level political claims with 6 truthfulness labels.
We binarize to: reliable = {mostly-true, true}, unreliable = {pants-fire, false, barely-true}.
The ambiguous label "half-true" (~22% of data) is dropped — it genuinely straddles the boundary
and including it as either class degrades calibration.

Usage:
    cd d:/DeceptiScan/backend
    python ml_training/train.py

Outputs:
    backend/ml_models/checkpoint/   — best model + tokenizer (safetensors format)
    backend/ml_models/metrics.json  — accuracy, precision, recall, F1, confusion matrix
"""
# Bootstrap: ensure D:\pylibs (short-path ML install) takes priority before any other import.
import sys as _sys
_PYLIBS = r"D:\pylibs"
if _PYLIBS in _sys.path:
    _sys.path.remove(_PYLIBS)
_sys.path.insert(0, _PYLIBS)

import os
import sys
import json
import logging
import time
from pathlib import Path

import numpy as np
import torch
import transformers
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    set_seed,
)

# CPU Parallelism optimization
if not torch.cuda.is_available():
    num_cpus = os.cpu_count() or 4
    torch.set_num_threads(min(8, num_cpus))

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("deceptiscan.train")

# ---------------------------------------------------------------------------
# Paths — relative to d:/DeceptiScan/backend/
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
CHECKPOINT_DIR = BACKEND_DIR / "ml_models" / "checkpoint"
METRICS_PATH = BACKEND_DIR / "ml_models" / "metrics.json"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Model / training config
# ---------------------------------------------------------------------------
MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 64           # LIAR statements median ~18 words; max ~45 words
NUM_EPOCHS = 1            # 1 epoch converges on 8.1k samples in ~3.5 mins with batch 32
BATCH_SIZE = 32
LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01
WARMUP_RATIO = 0.1
SEED = 42

# Label mapping — 6 LIAR labels → binary
# 0 = unreliable, 1 = reliable
LIAR_LABEL_MAP = {
    "pants-fire": 0,
    "false":      0,
    "barely-true": 0,
    # "half-true" → dropped (ambiguous)
    "mostly-true": 1,
    "true":        1,
}
ID2LABEL = {0: "unreliable", 1: "reliable"}
LABEL2ID = {"unreliable": 0, "reliable": 1}


def load_and_prepare_dataset():
    logger.info("Downloading LIAR dataset from Hugging Face Hub ...")
    raw = load_dataset("liar", trust_remote_code=True)
    logger.info(f"Train: {len(raw['train'])}, Validation: {len(raw['validation'])}, Test: {len(raw['test'])}")

    label_feature = raw["train"].features["label"]

    def binarize(example):
        val = example["label"]
        if isinstance(val, int):
            label_str = label_feature.int2str(val)
        else:
            label_str = str(val)

        if label_str not in LIAR_LABEL_MAP:
            return {"binary_label": -1}
        return {"binary_label": LIAR_LABEL_MAP[label_str]}

    raw = raw.map(binarize)

    # Drop half-true examples (binary_label == -1)
    original_counts = {split: len(raw[split]) for split in raw}
    raw = raw.filter(lambda x: x["binary_label"] != -1)
    filtered_counts = {split: len(raw[split]) for split in raw}
    for split in raw:
        dropped = original_counts[split] - filtered_counts[split]
        logger.info(f"[{split}] {original_counts[split]} -> {filtered_counts[split]} after dropping half-true ({dropped} dropped)")

    return raw


def tokenize_dataset(raw_dataset):
    logger.info(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(
            batch["statement"],
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length",
        )

    logger.info("Tokenizing ...")
    tokenized = raw_dataset.map(tokenize, batched=True, batch_size=512)
    tokenized = tokenized.rename_column("binary_label", "labels")
    tokenized.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

    return tokenized, tokenizer


def compute_metrics(eval_pred):
    from sklearn.metrics import (
        accuracy_score, precision_recall_fscore_support, confusion_matrix
    )

    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)

    acc = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="macro", zero_division=0
    )
    cm = confusion_matrix(labels, predictions).tolist()

    return {
        "accuracy": round(float(acc), 4),
        "precision_macro": round(float(precision), 4),
        "recall_macro": round(float(recall), 4),
        "f1_macro": round(float(f1), 4),
        "confusion_matrix": cm,
    }


def train(tokenized_dataset, tokenizer):
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        set_seed,
    )

    set_seed(SEED)

    logger.info(f"Loading base model: {MODEL_NAME}")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    use_fp16 = torch.cuda.is_available()
    logger.info(f"CUDA available: {torch.cuda.is_available()} — fp16: {use_fp16}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("Training on CPU — this will take approximately 2-4 hours for 3 epochs")

    training_args = TrainingArguments(
        output_dir=str(CHECKPOINT_DIR),
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_steps=150,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        logging_steps=50,
        fp16=use_fp16,
        seed=SEED,
        report_to="none",
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
        compute_metrics=compute_metrics,
        processing_class=tokenizer,
    )

    logger.info("Starting training ...")
    t0 = time.time()
    train_result = trainer.train()
    elapsed = time.time() - t0
    logger.info(f"Training complete in {elapsed/60:.1f} minutes")

    return trainer, train_result


def evaluate_on_test(trainer, tokenized_dataset):
    logger.info("Evaluating on LIAR test split ...")
    test_metrics = trainer.evaluate(tokenized_dataset["test"], metric_key_prefix="test")
    logger.info(f"Test results: {json.dumps(test_metrics, indent=2)}")
    return test_metrics


def save_outputs(trainer, tokenizer, train_result, test_metrics):
    logger.info(f"Saving model + tokenizer to {CHECKPOINT_DIR}")
    trainer.save_model(str(CHECKPOINT_DIR))
    tokenizer.save_pretrained(str(CHECKPOINT_DIR))

    # Write label config explicitly (belt-and-suspenders)
    config_patch = {
        "id2label": {str(k): v for k, v in ID2LABEL.items()},
        "label2id": LABEL2ID,
    }
    config_path = CHECKPOINT_DIR / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
        cfg.update(config_patch)
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=2)

    metrics_payload = {
        "model_name": "distilbert-liar-v1",
        "base_model": MODEL_NAME,
        "dataset": "liar",
        "label_mapping": {
            "reliable": ["mostly-true", "true"],
            "unreliable": ["pants-fire", "false", "barely-true"],
            "dropped": ["half-true"],
        },
        "training_config": {
            "num_epochs": NUM_EPOCHS,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "warmup_ratio": WARMUP_RATIO,
            "max_length": MAX_LENGTH,
            "seed": SEED,
        },
        "train_metrics": {
            k: v for k, v in train_result.metrics.items()
        },
        "test_metrics": test_metrics,
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=2)

    logger.info(f"Metrics written to {METRICS_PATH}")
    logger.info("=" * 60)
    logger.info("FINAL TEST METRICS")
    logger.info("=" * 60)
    for key, val in test_metrics.items():
        if key != "test_confusion_matrix":
            logger.info(f"  {key}: {val}")
    if "test_confusion_matrix" in test_metrics:
        cm = test_metrics["test_confusion_matrix"]
        logger.info("  Confusion matrix (rows=actual, cols=predicted):")
        logger.info(f"    unreliable: {cm[0]}")
        logger.info(f"    reliable:   {cm[1]}")
    logger.info("=" * 60)


def main():
    logger.info("DeceptiScan — DistilBERT fine-tuning on LIAR dataset")
    logger.info(f"Checkpoint will be saved to: {CHECKPOINT_DIR}")
    logger.info(f"Metrics will be saved to:    {METRICS_PATH}")

    raw_dataset = load_and_prepare_dataset()
    tokenized_dataset, tokenizer = tokenize_dataset(raw_dataset)
    trainer, train_result = train(tokenized_dataset, tokenizer)
    test_metrics = evaluate_on_test(trainer, tokenized_dataset)
    save_outputs(trainer, tokenizer, train_result, test_metrics)

    logger.info("Done! Run the Flask backend — ml_service.py will load from checkpoint automatically.")


if __name__ == "__main__":
    main()
