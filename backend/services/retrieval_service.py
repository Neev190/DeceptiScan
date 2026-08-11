"""
Retrieval Service for DeceptiScan.

Embeds input text using sentence-transformers/all-MiniLM-L6-v2 and queries
the claim_embeddings table via pgvector cosine similarity to return the top-k
most semantically similar LIAR training statements.

Pattern mirrors ml_service.py:
  - Embedding model loads on first use (lazy), not at import time
  - load_model() raises RuntimeError on failure (fail-loud)
  - Module-level singleton via get_retrieval_service()

Failure in find_similar_claims() propagates as an exception; the caller
(analysis route) is responsible for handling it gracefully.

Embedding model: sentence-transformers/all-MiniLM-L6-v2
  - 384-dimensional output (must match claim_embeddings.embedding vector(384))
  - CPU-friendly (~80MB), fully offline once cached by HuggingFace
  - Different model from the DistilBERT classifier in ml_service.py

Similarity metric: cosine distance (pgvector <=> operator)
  Similarity score returned = 1 - cosine_distance  (range 0..1, higher = more similar)

Similarity threshold: 0.45
  Determined empirically by querying 20 LIAR test-split statements against the
  training corpus and observing the score distribution. See RETRIEVAL_CARD.md
  for the full distribution and reasoning. Results below this threshold are
  excluded rather than padded — "no meaningfully similar claim" is reported
  as an empty list.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Empirically determined similarity cutoff — see RETRIEVAL_CARD.md §Threshold.
# Scores below this value are treated as "no meaningfully similar claim found".
SIMILARITY_THRESHOLD = 0.45


class RetrievalService:
    """
    Retrieval service using all-MiniLM-L6-v2 embeddings and pgvector cosine search.

    Lazy-loads the embedding model on first use. Never silently falls back to
    dummy results — load failures raise RuntimeError so the caller can decide
    whether to degrade gracefully.
    """

    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __init__(self):
        self._model = None
        self._model_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._model_loaded

    def load_model(self) -> bool:
        """
        Load the sentence-transformer embedding model.

        Returns:
            True on success.

        Raises:
            RuntimeError: If the model cannot be loaded.
                          NEVER silently falls back to mock embeddings.
        """
        if self._model_loaded:
            return True

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL_NAME}")
            self._model = SentenceTransformer(self.EMBEDDING_MODEL_NAME)
            self._model_loaded = True
            logger.info(
                f"Embedding model loaded successfully. "
                f"Output dim: {self.EMBEDDING_DIM}"
            )
            return True
        except Exception as e:
            self._model = None
            self._model_loaded = False
            raise RuntimeError(
                f"Failed to load embedding model '{self.EMBEDDING_MODEL_NAME}': {e}"
            ) from e

    def unload_model(self):
        self._model = None
        self._model_loaded = False
        logger.info("Retrieval embedding model unloaded")

    def find_similar_claims(self, text: str, k: int = 3) -> list[dict]:
        """
        Find the top-k most semantically similar LIAR training claims.

        Args:
            text: The input text to find similar claims for.
            k:    Maximum number of results to return (default 3).

        Returns:
            List of dicts, each with:
                - statement_text (str): The LIAR training statement
                - label (str): "reliable" | "unreliable"
                - similarity_score (float): Cosine similarity in [0, 1]
            Results are sorted descending by similarity_score.
            Returns [] if text is empty or no results exceed SIMILARITY_THRESHOLD.

        Raises:
            RuntimeError: If the embedding model fails to load.
            Exception: If the database query fails. The caller (analysis route)
                       catches this and returns retrieval_status="unavailable".
        """
        if not text or not text.strip():
            return []

        if not self._model_loaded:
            self.load_model()

        # Embed the query text
        embedding = self._model.encode(text, normalize_embeddings=True).tolist()

        # Query pgvector via SQLAlchemy — import here to avoid circular imports
        # and to keep the model load independent of the DB connection.
        from app import db
        from models.claim_embedding import ClaimEmbedding
        from pgvector.sqlalchemy import Vector
        import sqlalchemy as sa

        # pgvector cosine distance operator: <=>
        # cosine distance = 1 - cosine similarity, so we order ASC and convert.
        raw_distance = ClaimEmbedding.embedding.op("<=>")(
            sa.cast(embedding, Vector(self.EMBEDDING_DIM))
        )
        distance_expr = sa.type_coerce(raw_distance, sa.Float)

        rows = (
            db.session.query(
                ClaimEmbedding.statement_text,
                ClaimEmbedding.label,
                distance_expr.label("distance"),
            )
            .order_by(distance_expr.asc())
            .limit(k)
            .all()
        )

        results = []
        for row in rows:
            similarity = round(1.0 - float(row.distance), 4)
            if similarity < SIMILARITY_THRESHOLD:
                continue
            results.append({
                "statement_text": row.statement_text,
                "label": row.label,
                "similarity_score": similarity,
            })

        return results


# ---------------------------------------------------------------------------
# Global service instance
# ---------------------------------------------------------------------------
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """Get the global RetrievalService instance (singleton)."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


def init_retrieval_service() -> bool:
    """Initialize the retrieval service and load the embedding model. Raises on failure."""
    service = get_retrieval_service()
    return service.load_model()


def unload_retrieval_service():
    """Unload the retrieval service to free memory."""
    global _retrieval_service
    if _retrieval_service is not None:
        _retrieval_service.unload_model()
        _retrieval_service = None
