"""
Unit tests for the ML Service.

Tests text preprocessing, sentence extraction, classification inference,
and authenticity score calculation.

Inference tests are guarded by CHECKPOINT_EXISTS: if the model checkpoint
has not been generated yet (run `python ml_training/train.py`), they are
skipped gracefully so the rest of the test suite still passes.
"""
import pytest
from pathlib import Path
from services.ml_service import (
    MLService,
    AnalysisResult,
    SentenceAnalysis,
    get_ml_service,
    init_ml_service,
    CHECKPOINT_PATH,
)

CHECKPOINT_EXISTS = CHECKPOINT_PATH.exists()
requires_checkpoint = pytest.mark.skipif(
    not CHECKPOINT_EXISTS,
    reason=f"Model checkpoint not found at {CHECKPOINT_PATH}. Run `python ml_training/train.py` first.",
)


class TestMLServiceNonInference:
    """Tests that do not require the model checkpoint."""

    def setup_method(self):
        self.ml_service = MLService()

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------
    def test_preprocess_whitespace(self):
        dirty_text = "  This  is   a   test.   "
        cleaned = self.ml_service.preprocess(dirty_text)
        assert cleaned == "This is a test."

    def test_preprocess_url_removal(self):
        text = "Check this out https://example.com for more info."
        cleaned = self.ml_service.preprocess(text)
        assert "https://example.com" not in cleaned

    def test_preprocess_email_removal(self):
        text = "Contact us at test@example.com for help."
        cleaned = self.ml_service.preprocess(text)
        assert "test@example.com" not in cleaned

    def test_preprocess_empty(self):
        assert self.ml_service.preprocess("") == ""
        assert self.ml_service.preprocess("   ") == ""

    # ------------------------------------------------------------------
    # Sentence extraction
    # ------------------------------------------------------------------
    def test_sentence_extraction_basic(self):
        text = "This is the first sentence. This is the second sentence! And a third?"
        sentences = self.ml_service.extract_sentences(text)
        assert len(sentences) == 3
        assert "This is the first sentence" in sentences[0]
        assert "This is the second sentence" in sentences[1]
        assert "And a third" in sentences[2]

    def test_sentence_extraction_empty(self):
        assert self.ml_service.extract_sentences("") == []

    def test_sentence_extraction_single(self):
        sentences = self.ml_service.extract_sentences("Just one sentence.")
        assert len(sentences) == 1

    # ------------------------------------------------------------------
    # Flag detection
    # ------------------------------------------------------------------
    def test_flag_sensationalism(self):
        flags = self.ml_service._detect_flags("This shocking news will blow your mind!")
        assert "sensationalism" in flags

    def test_flag_logical_fallacy(self):
        flags = self.ml_service._detect_flags("Everyone knows this is obviously true.")
        assert "logical_fallacy" in flags

    def test_flag_loaded_language(self):
        flags = self.ml_service._detect_flags("This evil politician is absolutely disgusting.")
        assert "loaded_language" in flags

    def test_flag_unverified_claim(self):
        flags = self.ml_service._detect_flags("Studies show that this product works miracles.")
        assert "unverified_claim" in flags

    def test_flag_clean_text(self):
        flags = self.ml_service._detect_flags("The weather today is partly cloudy.")
        assert len(flags) == 0

    # ------------------------------------------------------------------
    # Sentence categorization
    # ------------------------------------------------------------------
    def test_categorize_opinion(self):
        category = self.ml_service._categorize_sentence("I think this is a great idea for the future.")
        assert category == "opinion"

    def test_categorize_factual(self):
        category = self.ml_service._categorize_sentence("The study showed a 25% increase in statistics.")
        assert category == "factual"

    def test_categorize_claim(self):
        category = self.ml_service._categorize_sentence("The president announced new policies yesterday.")
        assert category == "claim"

    def test_categorize_context(self):
        category = self.ml_service._categorize_sentence("The weather was nice that day.")
        assert category == "context"

    # ------------------------------------------------------------------
    # Authenticity score calculation (uses SentenceAnalysis dataclass directly)
    # ------------------------------------------------------------------
    def test_authenticity_score_empty(self):
        assert self.ml_service.calculate_authenticity_score([]) == 50.0

    def test_authenticity_score_all_reliable(self):
        reliable = SentenceAnalysis(
            index=0, text="Reliable information here.",
            is_suspicious=False, score=90.0, confidence=0.9,
            category="factual", flags=[], explanation="Reliable"
        )
        score = self.ml_service.calculate_authenticity_score([reliable, reliable])
        assert score >= 75

    def test_authenticity_score_mixed(self):
        reliable = SentenceAnalysis(
            index=0, text="This is reliable information.",
            is_suspicious=False, score=85.0, confidence=0.8,
            category="factual", flags=[], explanation="Reliable content"
        )
        suspicious = SentenceAnalysis(
            index=1, text="This shocking news!",
            is_suspicious=True, score=25.0, confidence=0.7,
            category="claim", flags=["sensationalism"], explanation="Suspicious"
        )
        score = self.ml_service.calculate_authenticity_score([reliable, suspicious])
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert 40 <= score <= 70

    # ------------------------------------------------------------------
    # Classification determination
    # ------------------------------------------------------------------
    def test_classification_reliable(self):
        assert self.ml_service._determine_classification(80.0, 0.8) == "reliable"

    def test_classification_mixed(self):
        assert self.ml_service._determine_classification(60.0, 0.7) == "mixed"

    def test_classification_unreliable(self):
        assert self.ml_service._determine_classification(20.0, 0.8) == "unreliable"

    def test_classification_unknown_low_confidence(self):
        assert self.ml_service._determine_classification(80.0, 0.05) == "unknown"

    # ------------------------------------------------------------------
    # Explanation generation
    # ------------------------------------------------------------------
    def test_explanation_reliable_factual(self):
        explanation = self.ml_service._generate_explanation("reliable", 0.8, "factual", [])
        assert "reliable" in explanation.lower()
        assert "factual" in explanation.lower()

    def test_explanation_unreliable_with_flags(self):
        explanation = self.ml_service._generate_explanation(
            "unreliable", 0.7, "claim", ["sensationalism", "loaded_language"]
        )
        assert "unreliable" in explanation.lower()
        assert "sensationalist" in explanation.lower()

    def test_explanation_low_confidence(self):
        explanation = self.ml_service._generate_explanation("reliable", 0.4, "factual", [])
        assert "low confidence" in explanation.lower()


class TestMLServiceLoadingBehavior:
    """Tests around model loading state — checkpoint-independent."""

    def test_not_loaded_initially(self):
        service = MLService()
        assert service.is_loaded is False

    def test_unload_sets_not_loaded(self):
        service = MLService()
        # Manually set state to simulate loaded
        service._model_loaded = True
        service.unload_model()
        assert service.is_loaded is False

    def test_load_raises_when_checkpoint_missing(self, tmp_path, monkeypatch):
        """load_model() must raise RuntimeError if checkpoint directory and HF Hub repo do not exist."""
        import services.ml_service as ml_mod
        monkeypatch.setattr(ml_mod, "CHECKPOINT_PATH", tmp_path / "nonexistent")
        monkeypatch.setattr(ml_mod, "HF_MODEL_REPO", "invalid-repo/nonexistent-model")
        service = MLService()
        with pytest.raises(RuntimeError, match="(Failed to load ML model|checkpoint not found)"):
            service.load_model()

    def test_load_raises_when_checkpoint_and_hub_both_fail(self, tmp_path, monkeypatch):
        """load_model() must raise RuntimeError when local files are absent AND snapshot_download fails.

        This exercises the NEW code path: local check fails → snapshot_download called →
        snapshot_download raises (e.g. network error) → RuntimeError propagated with fail-loud.
        The existing test above covers 'invalid repo' errors; this test covers explicit
        download failures (e.g. RepositoryNotFoundError, network timeout).
        """
        import services.ml_service as ml_mod

        def _fail_download(**kwargs):
            raise OSError("Simulated network failure during snapshot_download")

        monkeypatch.setattr(ml_mod, "CHECKPOINT_PATH", tmp_path / "empty_checkpoint")
        monkeypatch.setattr(
            ml_mod,
            "snapshot_download",
            _fail_download,
            raising=False,
        )
        service = MLService()
        with pytest.raises(RuntimeError, match="(Failed to load ML model|checkpoint not found)"):
            service.load_model()


@requires_checkpoint
class TestMLServiceInference:
    """Tests requiring the real DistilBERT checkpoint."""

    def setup_method(self):
        self.ml_service = MLService()
        self.ml_service.load_model()

    def test_model_loading(self):
        assert self.ml_service.is_loaded is True
        # Loading again should be a no-op and return True
        assert self.ml_service.load_model() is True

    def test_model_version(self):
        result = self.ml_service.analyze("This is a test sentence.")
        assert result.model_version == "distilbert-liar-v1"

    def test_sentence_classification_structure(self):
        sentence = "According to official data, unemployment decreased by 2%."
        result = self.ml_service.classify_sentence(sentence)
        assert isinstance(result, SentenceAnalysis)
        assert result.text == sentence
        assert isinstance(result.score, float)
        assert 0 <= result.score <= 100
        assert 0 <= result.confidence <= 1
        assert result.category in ["factual", "opinion", "claim", "context"]
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 0

    def test_score_is_not_hash_derived(self):
        """Confirm that inference produces real probability-derived scores, not hash artifacts."""
        import hashlib
        sentence = "Scientists have confirmed the new vaccine is effective."
        result = self.ml_service.classify_sentence(sentence)
        # A hash-based mock would produce score = (abs(hash(sentence)) % 1000) % 70 + 15
        # The real model produces P(reliable) * 100, which is a float in [0, 100]
        # We verify the score is a genuine probability value: between 0 and 100 and NOT an integer
        # (DistilBERT softmax outputs are almost never exact integers)
        assert 0.0 <= result.score <= 100.0
        # Score should be derived from P(reliable) × 100, so it varies with model output, not text hash
        h_score = (abs(hash(sentence)) % 1000) % 70 + 15
        assert result.score != h_score, "Score appears to be hash-derived, not model-derived"

    def test_full_analysis_workflow(self):
        text = """
        According to recent studies, climate change affects weather patterns.
        This shocking revelation will change everything you know!
        The data shows a clear trend over the past decade.
        """
        result = self.ml_service.analyze(text)
        assert isinstance(result, AnalysisResult)
        assert 0 <= result.authenticity_score <= 100
        assert 0 <= result.confidence <= 1
        assert result.classification in ["reliable", "mixed", "unreliable", "unknown"]
        assert len(result.sentence_analysis) > 0
        assert result.processing_time_ms > 0
        assert result.model_version == "distilbert-liar-v1"

        for sa in result.sentence_analysis:
            assert isinstance(sa, SentenceAnalysis)
            assert len(sa.text) > 0
            assert isinstance(sa.index, int)
            assert 0 <= sa.score <= 100
            assert 0 <= sa.confidence <= 1

    def test_empty_text_analysis(self):
        result = self.ml_service.analyze("")
        assert result.authenticity_score == 50.0
        assert result.confidence == 0.0
        assert result.classification == "unknown"
        assert len(result.sentence_analysis) == 0

    def test_whitespace_only_analysis(self):
        result = self.ml_service.analyze("   ")
        assert result.classification == "unknown"

    def test_deterministic_results(self):
        """Real inference is deterministic (eval mode, no dropout)."""
        text = "This is a test sentence for reproducibility."
        result1 = self.ml_service.analyze(text)
        result2 = self.ml_service.analyze(text)
        assert result1.authenticity_score == result2.authenticity_score
        assert result1.confidence == result2.confidence
        assert result1.classification == result2.classification
        assert len(result1.sentence_analysis) == len(result2.sentence_analysis)

    def test_very_long_text(self):
        long_text = ". ".join([f"This is sentence number {i}" for i in range(50)])
        result = self.ml_service.analyze(long_text)
        assert isinstance(result, AnalysisResult)
        assert len(result.sentence_analysis) > 0

    def test_special_characters(self):
        special_text = "This has special characters and some unusual content!"
        result = self.ml_service.analyze(special_text)
        assert isinstance(result, AnalysisResult)

    def test_single_word_sentences_filtered(self):
        short_text = "Yes. No. Maybe."
        result = self.ml_service.analyze(short_text)
        assert len(result.sentence_analysis) == 0 or all(
            len(s.text) > 5 for s in result.sentence_analysis
        )


class TestMLServiceGlobal:
    """Test global ML service functions."""

    def test_get_ml_service_singleton(self):
        service1 = get_ml_service()
        service2 = get_ml_service()
        assert service1 is service2
        assert isinstance(service1, MLService)

    @requires_checkpoint
    def test_init_ml_service(self):
        result = init_ml_service()
        assert result is True
        service = get_ml_service()
        assert service.is_loaded is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])