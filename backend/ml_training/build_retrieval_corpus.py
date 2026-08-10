"""
Build the LIAR-derived retrieval corpus for DeceptiScan Phase 2.

Loads the SAME LIAR training split used by train.py (via shared
load_and_prepare_dataset()), embeds each statement with
sentence-transformers/all-MiniLM-L6-v2, and inserts the results into
the claim_embeddings table.

Usage:
    cd d:/DeceptiScan/backend
    DATABASE_URL=postgresql://deceptiscan:password@localhost:5432/deceptiscan \\
        python ml_training/build_retrieval_corpus.py

Prerequisites:
    1. Migration 002_retrieval_corpus must have been applied (flask db upgrade)
    2. sentence-transformers and pgvector must be installed
    3. The database must be reachable

This script is idempotent: it truncates claim_embeddings before inserting,
so re-running after any corpus change is safe.
"""
# Bootstrap: ensure D:\\pylibs (short-path ML install) takes priority.
import sys as _sys
_PYLIBS = r"D:\pylibs"
if _PYLIBS in _sys.path:
    _sys.path.remove(_PYLIBS)
_sys.path.insert(0, _PYLIBS)

import logging
import os
import sys
import time
from pathlib import Path

# Add backend/ to sys.path so we can import app, models, services
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(1, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("deceptiscan.build_corpus")

# Corpus ingestion config
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 64      # Efficient on CPU for 384-dim; tune down if OOM
INSERT_CHUNK = 50   # 50 rows per chunk prevents Neon proxy SQL statement parameter limit issues
LIAR_SPLIT = "train"  # Must match the split train.py trains on (tokenized_dataset["train"])

def _save_chunk_with_retry(db, chunk, retries=3):
    for attempt in range(1, retries + 1):
        try:
            db.session.bulk_save_objects(chunk)
            db.session.commit()
            return
        except Exception as e:
            db.session.rollback()
            if attempt == retries:
                raise e
            logger.warning(f"  Chunk insert attempt {attempt} failed ({e}). Retrying in 2s...")
            time.sleep(2)


def build_corpus():
    """Main entry point for corpus ingestion."""
    logger.info("=" * 60)
    logger.info("DeceptiScan — Phase 2 retrieval corpus build")
    logger.info(f"Embedding model : {EMBEDDING_MODEL_NAME}")
    logger.info(f"Embedding dim   : {EMBEDDING_DIM}")
    logger.info(f"LIAR split      : {LIAR_SPLIT}")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. Load LIAR training split — reuse train.py's function verbatim
    # ------------------------------------------------------------------
    logger.info("Loading LIAR dataset via train.load_and_prepare_dataset()...")
    from ml_training.train import load_and_prepare_dataset
    raw_dataset = load_and_prepare_dataset()

    train_data = raw_dataset[LIAR_SPLIT]
    total = len(train_data)
    logger.info(f"LIAR {LIAR_SPLIT} split size (after half-true filter): {total} examples")

    # Extract statements and binary labels
    # binary_label: 0 = unreliable, 1 = reliable (from train.LIAR_LABEL_MAP)
    statements = [ex["statement"] for ex in train_data]
    labels = ["reliable" if ex["binary_label"] == 1 else "unreliable"
              for ex in train_data]

    # ------------------------------------------------------------------
    # 2. Load embedding model
    # ------------------------------------------------------------------
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info("Embedding model loaded.")

    # ------------------------------------------------------------------
    # 3. Embed all training statements
    # ------------------------------------------------------------------
    logger.info(f"Embedding {total} statements in batches of {BATCH_SIZE}...")
    t0 = time.time()
    embeddings = model.encode(
        statements,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,   # cosine similarity = dot product
        show_progress_bar=True,
    )
    elapsed = time.time() - t0
    logger.info(f"Embedding complete in {elapsed:.1f}s. Shape: {embeddings.shape}")

    # ------------------------------------------------------------------
    # 4. Insert into database
    # ------------------------------------------------------------------
    logger.info("Connecting to database and inserting corpus...")

    from app import create_app, db
    from models.claim_embedding import ClaimEmbedding

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://deceptiscan:password@localhost:5432/deceptiscan"
    )
    if "client_encoding" not in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{sep}client_encoding=utf8"
    os.environ["DATABASE_URL"] = database_url

    app = create_app()

    with app.app_context():
        # Session-level connection init: encoding + fail-fast timeout.
        # statement_timeout causes any locked/hung query (TRUNCATE, INSERT, etc.)
        # to raise "ERROR: canceling statement due to statement timeout" after
        # 30 s instead of blocking silently until the process is killed manually.
        db.session.execute(db.text("SET client_encoding = 'UTF8';"))
        db.session.execute(db.text("SET statement_timeout = '30s';"))
        logger.info("Session GUCs set: client_encoding=UTF8, statement_timeout=30s")

        # Truncate first (idempotent re-runs).
        logger.info("Truncating existing claim_embeddings rows...")
        db.session.execute(db.text("SET statement_timeout = '20s';"))
        t0 = time.time()
        db.session.execute(db.text("TRUNCATE TABLE claim_embeddings;"))
        db.session.commit()
        logger.info(f"TRUNCATE completed in {time.time() - t0:.2f}s")

        # Drop IVFFlat index before bulk load to prevent per-batch index update overhead
        logger.info("Dropping vector index prior to bulk insert...")
        db.session.execute(db.text("DROP INDEX IF EXISTS idx_claim_embeddings_embedding;"))
        db.session.commit()

        db.session.execute(db.text("SET statement_timeout = '30s';"))

        rows_inserted = 0
        chunk = []

        for i, (stmt, label, emb) in enumerate(zip(statements, labels, embeddings)):
            # Clean statement text to pure ASCII to prevent Windows psycopg2 CP1252 charmap errors
            clean_stmt = stmt.encode('ascii', errors='ignore').decode('ascii').strip()
            if not clean_stmt:
                clean_stmt = stmt.strip()
            chunk.append(
                ClaimEmbedding(
                    statement_text=clean_stmt,
                    label=label,
                    embedding=emb.tolist(),
                )
            )

            if len(chunk) >= INSERT_CHUNK:
                _save_chunk_with_retry(db, chunk)
                rows_inserted += len(chunk)
                if rows_inserted % 500 == 0 or rows_inserted == total:
                    logger.info(f"  Inserted {rows_inserted}/{total} rows...")
                chunk = []

        # Flush remainder
        if chunk:
            _save_chunk_with_retry(db, chunk)
            rows_inserted += len(chunk)
            logger.info(f"  Inserted {rows_inserted}/{total} rows...")

        # Recreate IVFFlat vector index over complete dataset
        logger.info("Rebuilding IVFFlat vector index over inserted corpus...")
        db.session.execute(db.text("SET statement_timeout = '120s';"))
        t_idx = time.time()
        db.session.execute(db.text("""
            CREATE INDEX idx_claim_embeddings_embedding
            ON claim_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))
        db.session.commit()
        logger.info(f"IVFFlat index rebuilt in {time.time() - t_idx:.2f}s")

    logger.info("=" * 60)
    logger.info(f"Corpus build complete. Total rows inserted: {rows_inserted}")
    logger.info("=" * 60)
    return rows_inserted


if __name__ == "__main__":
    rows = build_corpus()
    sys.exit(0 if rows > 0 else 1)
