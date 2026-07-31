"""
Property-based tests for ML Service.

Tests invariants and properties that should hold for all valid inputs.
Uses Hypothesis for property-based testing.

Inference-dependent tests are guarded by CHECKPOINT_EXISTS so the property
suite can run in CI without a trained checkpoint (e.g., for preprocessing tests).
All property invariants (score bounds, confidence bounds, threshold consistency)
are preserved exactly as specified — none are weakened.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from pathlib import Path
from services.ml_service import MLService, AnalysisResult, SentenceAnalysis, CHECKPOINT_PATH

CHECKPOINT_EXISTS = CHECKPOINT_PATH.exists()
requires_checkpoint = pytest.mark.skipif(
    not CHECKPOINT_EXISTS,
    reason=f"Model checkpoint not found at {CHECKPOINT_PATH}. Run `python ml_training/train.py` first.",
)


class TestMLServicePreprocessingProperties:
    """Property tests for preprocessing — no checkpoint required."""

    def setup_method(self):
        self.ml_service = MLService()

    @given(st.text(min_size=1, max_size=200))
    @settings(max_examples=30)
    def test_preprocessing_idempotent(self, text):
        """
        Property: Preprocessing should be idempotent (applying twice gives same result).
        Validates: Text preprocessing correctness
        """
        cleaned_once = self.ml_service.preprocess(text)
        cleaned_twice = self.ml_service.preprocess(cleaned_once)
        assert cleaned_once == cleaned_twice, "Preprocessing should be idempotent"

    @given(st.sampled_from(["", " ", "  ", "\t", "\n", "   \n\t  "]))
    @settings(max_examples=10)
    def test_empty_preprocessing_returns_empty(self, text):
        """Empty/whitespace input should preprocess to empty string."""
        result = self.ml_service.preprocess(text)
        assert result == "" or result.strip() == ""


@requires_checkpoint
class TestMLServiceProperties:
    """Property-based tests for ML Service invariants — requires checkpoint."""

    def setup_method(self):
        self.ml_service = MLService()
        self.ml_service.load_model()

    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=30, deadline=None)
    def test_authenticity_score_boundaries(self, text):
        """
        Property: Authenticity score should always be between 0 and 100.
        Validates: Requirements 1.2, 3.4, 3.5, 3.6
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 0)

        result = self.ml_service.analyze(text)

        assert isinstance(result.authenticity_score, (int, float))
        assert 0 <= result.authenticity_score <= 100, (
            f"Score {result.authenticity_score} outside valid range [0, 100]"
        )

    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=30, deadline=None)
    def test_confidence_boundaries(self, text):
        """
        Property: Confidence should always be between 0 and 1.
        Validates: Requirements 1.2, 4.1
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 0)

        result = self.ml_service.analyze(text)

        assert isinstance(result.confidence, (int, float))
        assert 0 <= result.confidence <= 1, (
            f"Confidence {result.confidence} outside valid range [0, 1]"
        )

        for sentence_result in result.sentence_analysis:
            assert 0 <= sentence_result.confidence <= 1, (
                f"Sentence confidence {sentence_result.confidence} outside valid range"
            )

    @given(st.text(min_size=10, max_size=500))
    @settings(max_examples=30, deadline=None)
    def test_classification_threshold_consistency(self, text):
        """
        Property: Classification should be consistent with authenticity score thresholds.
        Validates: Requirements 3.4, 3.5, 3.6

        This property must hold for ALL non-unknown results:
          score >= 75  → "reliable"
          40 <= score < 75 → "mixed"
          score < 40   → "unreliable"
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 10)

        result = self.ml_service.analyze(text)

        # Skip unknown classifications (low confidence is a valid override)
        assume(result.classification != "unknown")

        score = result.authenticity_score
        classification = result.classification

        if score >= 75:
            assert classification == "reliable", (
                f"Score {score} should be 'reliable' but got '{classification}'"
            )
        elif 40 <= score < 75:
            assert classification == "mixed", (
                f"Score {score} should be 'mixed' but got '{classification}'"
            )
        else:
            assert classification == "unreliable", (
                f"Score {score} should be 'unreliable' but got '{classification}'"
            )

    @given(st.text(min_size=20, max_size=300))
    @settings(max_examples=20, deadline=None)
    def test_sentence_coverage(self, text):
        """
        Property: All sentences from input should appear in analysis results.
        Validates: Requirements 1.4
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 20)

        original_sentences = self.ml_service.extract_sentences(cleaned)
        assume(len(original_sentences) > 0)

        result = self.ml_service.analyze(text)

        analyzed_texts = [s.text for s in result.sentence_analysis]
        for original in original_sentences:
            found = any(
                original.strip() in analyzed or analyzed in original.strip()
                for analyzed in analyzed_texts
            )
            assert found, f"Original sentence '{original}' not found in analysis results"

    @given(st.text(min_size=5, max_size=200))
    @settings(max_examples=30, deadline=None)
    def test_sentence_score_boundaries(self, text):
        """
        Property: All sentence scores should be between 0 and 100.
        Validates: Requirements 1.4
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 5)

        result = self.ml_service.analyze(text)

        for sentence_result in result.sentence_analysis:
            assert 0 <= sentence_result.score <= 100, (
                f"Sentence score {sentence_result.score} outside valid range [0, 100]"
            )

    @given(st.text(min_size=10, max_size=300))
    @settings(max_examples=20, deadline=None)
    def test_low_confidence_unknown_classification(self, text):
        """
        Property: When confidence is below threshold, classification should be 'unknown'.
        Validates: Requirements 4.1, 4.2
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 10)

        result = self.ml_service.analyze(text)

        if result.confidence < self.ml_service.LOW_CONFIDENCE_THRESHOLD:
            assert result.classification == "unknown", (
                f"Low confidence {result.confidence} should result in 'unknown' classification, "
                f"got '{result.classification}'"
            )

    @given(st.text(min_size=1, max_size=500))
    @settings(max_examples=30, deadline=None)
    def test_analysis_completeness(self, text):
        """
        Property: Analysis results should always contain required fields.
        Validates: Requirements 3.1, 3.2, 3.3
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 0)

        result = self.ml_service.analyze(text)

        assert hasattr(result, 'authenticity_score')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'classification')
        assert hasattr(result, 'sentence_analysis')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'model_version')

        assert isinstance(result.authenticity_score, (int, float))
        assert isinstance(result.confidence, (int, float))
        assert isinstance(result.classification, str)
        assert isinstance(result.sentence_analysis, list)
        assert isinstance(result.processing_time_ms, (int, float))
        assert isinstance(result.model_version, str)

        assert result.processing_time_ms >= 0

        valid_classifications = ["reliable", "mixed", "unreliable", "unknown"]
        assert result.classification in valid_classifications

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=20, deadline=None)
    def test_deterministic_results(self, text):
        """
        Property: Same input should produce identical results.
        Real DistilBERT inference runs in eval mode with no dropout — fully deterministic.
        Validates: Analysis determinism
        """
        cleaned = self.ml_service.preprocess(text)
        assume(len(cleaned.strip()) > 0)

        result1 = self.ml_service.analyze(text)
        result2 = self.ml_service.analyze(text)

        assert result1.authenticity_score == result2.authenticity_score
        assert result1.confidence == result2.confidence
        assert result1.classification == result2.classification
        assert len(result1.sentence_analysis) == len(result2.sentence_analysis)

        for s1, s2 in zip(result1.sentence_analysis, result2.sentence_analysis):
            assert s1.score == s2.score
            assert s1.confidence == s2.confidence
            assert s1.is_suspicious == s2.is_suspicious

    suspicious_words = st.sampled_from([
        "shocking", "unbelievable", "breaking", "secret", "exposed",
        "everyone knows", "obviously",
    ])

    @given(st.text(min_size=10, max_size=100), suspicious_words)
    @settings(max_examples=20, deadline=None)
    def test_flag_detection_consistency(self, base_text, suspicious_word):
        """
        Property: Text containing suspicious keywords should be flagged or scored as suspicious.
        Validates: Flag detection accuracy

        Note: The real model decides score; keyword detection flags the text via _detect_flags.
        Either flags detected OR is_suspicious=True satisfies this property.
        """
        suspicious_text = f"{base_text} This is {suspicious_word} information!"

        result = self.ml_service.analyze(suspicious_text)

        has_flags = any(len(s.flags) > 0 for s in result.sentence_analysis)
        has_suspicious = any(s.is_suspicious for s in result.sentence_analysis)

        assert has_flags or has_suspicious, (
            f"Text with '{suspicious_word}' should trigger flags or suspicion"
        )

    empty_or_whitespace = st.sampled_from(["", " ", "  ", "\t", "\n", "\r\n", "   \t\n  "])

    @given(empty_or_whitespace)
    @settings(max_examples=20, deadline=None)
    def test_empty_input_handling(self, text):
        """
        Property: Empty or whitespace-only input should return safe defaults.
        Validates: Input validation and error handling
        """
        result = self.ml_service.analyze(text)

        assert result.authenticity_score == 50.0
        assert result.confidence == 0.0
        assert result.classification == "unknown"
        assert len(result.sentence_analysis) == 0
        assert result.processing_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])