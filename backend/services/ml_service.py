"""
ML Service for DeceptiScan misinformation detection.

Loads a fine-tuned DistilBERT binary classifier (reliable / unreliable)
trained on the LIAR dataset. The checkpoint must exist at:
    backend/ml_models/checkpoint/

To generate the checkpoint, run once:
    cd backend && python ml_training/train.py

Score derivation:
    sentence authenticity_score = P(reliable) * 100
    sentence confidence          = max(P(reliable), P(unreliable))

Classification thresholds (per spec requirements.md §3.4-3.6):
    reliable   : authenticity_score >= 75  (i.e. P(reliable) >= 0.75)
    mixed      : 40 <= authenticity_score < 75
    unreliable : authenticity_score < 40
    unknown    : overall confidence < 0.3
"""
# Bootstrap: ensure D:\pylibs (short-path ML install) takes priority.
# Windows MAX_PATH prevents pip from installing transformers at the default site-packages.
import sys as _sys
_PYLIBS = r"D:\pylibs"
if _PYLIBS in _sys.path:
    _sys.path.remove(_PYLIBS)
_sys.path.insert(0, _PYLIBS)

import re
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from huggingface_hub import snapshot_download

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Checkpoint path — relative to this file's location
# ---------------------------------------------------------------------------
_SERVICE_DIR = Path(__file__).resolve().parent
CHECKPOINT_PATH = _SERVICE_DIR.parent / "ml_models" / "checkpoint"
HF_MODEL_REPO = "Yakuza190/deceptiscan-distilbert-liar"


# ---------------------------------------------------------------------------
# Data classes (public interface — unchanged from mock)
# ---------------------------------------------------------------------------
@dataclass
class ClassificationResult:
    """Result of classifying a single sentence."""
    text: str
    label: str          # "reliable" | "unreliable"
    confidence: float   # 0-1
    probabilities: dict = field(default_factory=dict)
    category: str = "factual"


@dataclass
class SentenceAnalysis:
    """Detailed analysis of a single sentence."""
    index: int
    text: str
    is_suspicious: bool
    score: float        # 0-100
    confidence: float   # 0-1
    category: str
    flags: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class AnalysisResult:
    """Complete analysis result for an article."""
    authenticity_score: float   # 0-100
    confidence: float           # 0-1
    classification: str         # "reliable" | "mixed" | "unreliable" | "unknown"
    sentence_analysis: list[SentenceAnalysis] = field(default_factory=list)
    processing_time_ms: float = 0
    model_version: str = "distilbert-liar-v1"


# ---------------------------------------------------------------------------
# MLService
# ---------------------------------------------------------------------------
class MLService:
    """
    ML Service for text analysis using a fine-tuned DistilBERT classifier.

    Provides:
    - Text preprocessing
    - Sentence extraction
    - Real DistilBERT inference (loaded from checkpoint)
    - Authenticity score calculation
    """

    MODEL_VERSION = "distilbert-liar-v1"
    MAX_SEQUENCE_LENGTH = 128   # matches training; LIAR statements are short
    BATCH_SIZE = 16

    # Confidence threshold for low-confidence classification
    LOW_CONFIDENCE_THRESHOLD = 0.3

    # Classification thresholds (per requirements.md §3.4-3.6)
    RELIABLE_THRESHOLD = 75
    MIXED_LOWER = 40

    # Flag keywords — legitimate secondary signal for explanation / UI flags
    SENSATIONALISM_KEYWORDS = [
        'shocking', 'unbelievable', 'must see', 'breaking', 'urgent',
        'exposed', 'revealed', 'secret', 'scandal', 'breaking news',
    ]
    LOGICAL_FALLACY_KEYWORDS = [
        'everyone knows', 'obviously', 'clearly', 'everyone says',
        "they don't want you to know", 'wake up', 'the truth about',
    ]
    LOADED_LANGUAGE_KEYWORDS = [
        'evil', 'disgusting', 'horrible', 'terrible', 'amazing',
        'incredible', 'outrageous', 'pathetic', 'brilliant', 'stupid',
    ]

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_loaded = False

    # ------------------------------------------------------------------
    # Public interface (unchanged from mock)
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._model_loaded

    def load_model(self) -> bool:
        """
        Load the fine-tuned DistilBERT model and tokenizer from disk.

        Returns:
            True on success.

        Raises:
            RuntimeError: If the checkpoint directory is missing or corrupted.
                          NEVER silently falls back to mock / random output.
        """
        if self._model_loaded:
            return True

        has_local_files = (
            CHECKPOINT_PATH.exists()
            and (CHECKPOINT_PATH / "config.json").exists()
            and (
                (CHECKPOINT_PATH / "model.safetensors").exists()
                or (CHECKPOINT_PATH / "pytorch_model.bin").exists()
            )
        )

        try:
            # Lazy import so Flask starts without requiring torch
            from transformers import (
                AutoTokenizer,
                AutoModelForSequenceClassification,
            )
            import torch

            if not has_local_files:
                logger.info(
                    f"Local checkpoint not found at {CHECKPOINT_PATH}. "
                    f"Auto-fetching model from Hugging Face Hub ({HF_MODEL_REPO})..."
                )
                CHECKPOINT_PATH.mkdir(parents=True, exist_ok=True)
                snapshot_download(
                    repo_id=HF_MODEL_REPO,
                    local_dir=str(CHECKPOINT_PATH),
                )
                logger.info(f"Model auto-downloaded and saved to {CHECKPOINT_PATH}")

            logger.info(f"Loading tokenizer from {CHECKPOINT_PATH}")
            self._tokenizer = AutoTokenizer.from_pretrained(str(CHECKPOINT_PATH))

            logger.info(f"Loading model from {CHECKPOINT_PATH}")
            self._model = AutoModelForSequenceClassification.from_pretrained(
                str(CHECKPOINT_PATH)
            )

            # Always run inference in eval mode (no dropout, deterministic)
            self._model.eval()

            # Move to GPU if available
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(self._device)

            logger.info(
                f"DistilBERT model loaded successfully on {self._device}. "
                f"Labels: {self._model.config.id2label}"
            )
            self._model_loaded = True
            return True

        except Exception as e:
            self._model = None
            self._tokenizer = None
            self._model_loaded = False
            raise RuntimeError(
                f"Failed to load ML model from {CHECKPOINT_PATH}: {e}"
            ) from e

    def unload_model(self):
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        logger.info("ML model unloaded")

    def analyze(self, text: str) -> AnalysisResult:
        """
        Main entry point for text analysis.

        Args:
            text: The article text to analyze.

        Returns:
            AnalysisResult with authenticity score and sentence-level analysis.

        Raises:
            RuntimeError: If the model is not loaded.
        """
        start_time = time.time()

        if not self._model_loaded:
            self.load_model()

        cleaned_text = self.preprocess(text)
        sentences = self.extract_sentences(cleaned_text)

        if not sentences:
            return AnalysisResult(
                authenticity_score=50.0,
                confidence=0.0,
                classification="unknown",
                sentence_analysis=[],
                processing_time_ms=(time.time() - start_time) * 1000,
                model_version=self.MODEL_VERSION,
            )

        sentence_analysis = []
        for i, sentence in enumerate(sentences):
            result = self.classify_sentence(sentence)
            result.index = i
            sentence_analysis.append(result)

        authenticity_score = self.calculate_authenticity_score(sentence_analysis)
        avg_confidence = (
            sum(s.confidence for s in sentence_analysis) / len(sentence_analysis)
        )
        classification = self._determine_classification(authenticity_score, avg_confidence)

        return AnalysisResult(
            authenticity_score=authenticity_score,
            confidence=round(avg_confidence, 4),
            classification=classification,
            sentence_analysis=sentence_analysis,
            processing_time_ms=(time.time() - start_time) * 1000,
            model_version=self.MODEL_VERSION,
        )

    def preprocess(self, text: str) -> str:
        """Clean and normalize input text."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:\'""-]', '', text)
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        return text.strip()

    def extract_sentences(self, text: str) -> list[str]:
        """Split text into analyzable sentences."""
        if not text:
            return []
        sentences = re.split(
            r'(?<=[.!?])\s+(?=[A-Z])|'
            r'(?<=[.!?])$',
            text,
        )
        result = []
        for sentence in sentences:
            sentence = sentence.strip().strip('.,!?;:\'"- ')
            if sentence and len(sentence) > 5:
                result.append(sentence)
        return result

    def classify_sentence(self, sentence: str) -> SentenceAnalysis:
        """Classify an individual sentence using the DistilBERT model."""
        if not self._model_loaded:
            self.load_model()

        try:
            return self._run_inference(sentence)
        except Exception as e:
            logger.error(f"Inference error on sentence: {e}")
            # Propagate — do NOT silently return fake/default scores
            raise RuntimeError(f"ML inference failed: {e}") from e

    # ------------------------------------------------------------------
    # Private: real inference
    # ------------------------------------------------------------------

    def _run_inference(self, sentence: str) -> SentenceAnalysis:
        """
        Run real DistilBERT inference on a single sentence.

        Score derivation:
            authenticity_score = P(reliable) * 100
            confidence         = max(P(reliable), P(unreliable))

        No hash(), no random.seed(), no keyword-driven scoring.
        Keyword flags are a secondary annotation signal only.
        """
        import torch

        inputs = self._tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_SEQUENCE_LENGTH,
            padding="max_length",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)

        probs = torch.softmax(outputs.logits, dim=-1).squeeze().cpu().tolist()

        # Determine which index corresponds to each label
        id2label = self._model.config.id2label  # e.g. {0: "unreliable", 1: "reliable"}
        reliable_idx = next(
            idx for idx, lbl in id2label.items() if lbl.lower() == "reliable"
        )
        unreliable_idx = next(
            idx for idx, lbl in id2label.items() if lbl.lower() == "unreliable"
        )

        p_reliable = float(probs[reliable_idx])
        p_unreliable = float(probs[unreliable_idx])

        score = round(p_reliable * 100, 1)
        confidence = round(max(p_reliable, p_unreliable), 4)
        is_suspicious = score < 50.0

        probabilities = {
            "reliable": round(p_reliable, 4),
            "unreliable": round(p_unreliable, 4),
        }

        flags = self._detect_flags(sentence)
        category = self._categorize_sentence(sentence)
        label = "reliable" if p_reliable >= p_unreliable else "unreliable"
        explanation = self._generate_explanation(label, confidence, category, flags)

        return SentenceAnalysis(
            index=0,
            text=sentence,
            is_suspicious=is_suspicious,
            score=score,
            confidence=confidence,
            category=category,
            flags=flags,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # Secondary annotation helpers (keyword flags, categorization)
    # These are NOT used for scoring — only for explanation / UI display.
    # ------------------------------------------------------------------

    def _detect_flags(self, sentence: str) -> list[str]:
        """Detect rhetorical flags in sentence text (secondary signal only)."""
        sentence_lower = sentence.lower()
        flags = []

        if any(kw in sentence_lower for kw in self.SENSATIONALISM_KEYWORDS):
            flags.append('sensationalism')

        if any(kw in sentence_lower for kw in self.LOGICAL_FALLACY_KEYWORDS):
            flags.append('logical_fallacy')

        if any(kw in sentence_lower for kw in self.LOADED_LANGUAGE_KEYWORDS):
            flags.append('loaded_language')

        claim_indicators = [
            'report shows', 'studies show', 'research suggests',
            'scientists say', 'experts warn', 'officials say',
        ]
        if any(ind in sentence_lower for ind in claim_indicators):
            flags.append('unverified_claim')

        return flags

    def _categorize_sentence(self, sentence: str) -> str:
        """Categorize sentence as factual / opinion / claim / context."""
        sentence_lower = sentence.lower()

        opinion_markers = ['i think', 'i believe', 'in my opinion', 'i feel',
                           'it seems', 'probably', 'might be', 'could be']
        if any(m in sentence_lower for m in opinion_markers):
            return "opinion"

        claim_markers = ['said', 'stated', 'announced', 'claimed', 'reported',
                         'according to', 'sources say', 'officials say']
        if any(m in sentence_lower for m in claim_markers):
            return "claim"

        factual_markers = ['percent', '%', 'data', 'statistics', 'study',
                           'research', 'survey', 'census', 'report']
        if any(m in sentence_lower for m in factual_markers):
            return "factual"

        return "context"

    def _generate_explanation(
        self, label: str, confidence: float, category: str, flags: list[str]
    ) -> str:
        """Generate human-readable explanation for the classification."""
        parts = []

        if label == "reliable":
            parts.append("This sentence appears to be reliable")
            if category == "factual":
                parts.append("based on factual content")
            elif category == "context":
                parts.append("as it provides background information")
        else:
            parts.append("This sentence may contain unreliable information")
            if flags:
                flag_names = {
                    'sensationalism': 'sensationalist language',
                    'logical_fallacy': 'potential logical fallacy',
                    'loaded_language': 'emotionally charged language',
                    'unverified_claim': 'unverified claims',
                }
                flag_texts = [flag_names.get(f, f) for f in flags]
                parts.append(f"due to: {', '.join(flag_texts)}")

        if confidence < 0.5:
            parts.append("(low confidence)")

        return ". ".join(parts) + "."

    # ------------------------------------------------------------------
    # Score aggregation and classification (unchanged logic)
    # ------------------------------------------------------------------

    def calculate_authenticity_score(
        self, sentence_results: list[SentenceAnalysis]
    ) -> float:
        """Calculate overall authenticity score weighted by sentence length."""
        if not sentence_results:
            return 50.0

        weights = [max(1, len(r.text.split())) for r in sentence_results]
        total_weight = sum(weights)

        weighted_score = sum(
            r.score * w for r, w in zip(sentence_results, weights)
        ) / total_weight

        # Penalty: >30% suspicious sentences
        suspicious_count = sum(1 for r in sentence_results if r.is_suspicious)
        suspension_ratio = suspicious_count / len(sentence_results)
        if suspension_ratio > 0.3:
            penalty = 10 * (suspension_ratio - 0.3)
            weighted_score = max(0, weighted_score - penalty)

        # Penalty: flagged sentences
        total_flags = sum(len(r.flags) for r in sentence_results)
        if total_flags > 0:
            flag_penalty = min(5, total_flags * 0.5)
            weighted_score = max(0, weighted_score - flag_penalty)

        return round(weighted_score, 1)

    def _determine_classification(
        self, authenticity_score: float, confidence: float
    ) -> str:
        """Determine classification based on score and confidence."""
        if confidence < self.LOW_CONFIDENCE_THRESHOLD:
            return "unknown"
        if authenticity_score >= self.RELIABLE_THRESHOLD:
            return "reliable"
        if authenticity_score >= self.MIXED_LOWER:
            return "mixed"
        return "unreliable"


# ---------------------------------------------------------------------------
# Global service instance
# ---------------------------------------------------------------------------
_ml_service: Optional[MLService] = None


def get_ml_service() -> MLService:
    """Get the global ML service instance (singleton)."""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService()
    return _ml_service


def init_ml_service() -> bool:
    """Initialize the ML service and load the model. Raises on failure."""
    service = get_ml_service()
    return service.load_model()


def unload_ml_service():
    """Unload the ML service to free GPU/CPU memory."""
    global _ml_service
    if _ml_service is not None:
        _ml_service.unload_model()
        _ml_service = None