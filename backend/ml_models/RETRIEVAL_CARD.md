# DeceptiScan Retrieval Card — Phase 2 Stage 1: LIAR Corpus + pgvector

## Overview

This document describes the retrieval-augmented layer added in Phase 2, Stage 1.
Given a submitted claim or article, the system retrieves the top-3 most semantically
similar statements from the LIAR training corpus and returns them alongside the
DistilBERT classifier output, providing contextual grounding for the classification.

---

## Corpus Source

| Field | Value |
|---|---|
| **Source** | LIAR dataset (Wang, 2017) — training split only |
| **Corpus table** | `claim_embeddings` (PostgreSQL + pgvector) |
| **Corpus size** | ~8,200 rows (see §Build below for exact count) |
| **Label mapping** | Same binary scheme as the classifier: `reliable` = {true, mostly-true}, `unreliable` = {pants-fire, false, barely-true}; `half-true` dropped |
| **Split used** | `train` split only — the exact same split used to fine-tune the DistilBERT classifier |

### ⚠ Circularity Disclosure

**The retrieval corpus is built from the same LIAR training split used to fine-tune
the DistilBERT classifier.** This is intentional for Stage 1 — it proves that the
pgvector embedding pipeline works end-to-end using data already in hand.

**What this means in practice:**
- Similar claims surfaced are *labeled training examples*, not independently
  fact-checked claims from a separate source.
- The system can surface a LIAR training statement that is nearly identical to the
  input, but that statement's label (`reliable`/`unreliable`) comes from the same
  PolitiFact expert annotations used to train the classifier. It is not an
  *independent* verification signal.
- There is a risk that high-similarity training examples are retrieved for claims
  the classifier has already learned to recognize — making the retrieval layer
  appear more confirmatory than it actually is.

**Stage 2 (Google Fact Check Tools API — not yet built) is what will make the
retrieval layer a genuinely independent verification signal.** It queries live,
externally fact-checked claims that are not part of the training data, closing the
circularity gap. Until Stage 2 is implemented, the `similar_claims` field in the
API response should be presented to users with explicit disclosure that the matched
claims are from the classifier's training data.

---

## Embedding Model

| Field | Value |
|---|---|
| **Model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Dimension** | 384 |
| **Normalization** | L2-normalized (cosine similarity = dot product) |
| **Device** | CPU (fully offline once cached by HuggingFace) |
| **Size** | ~80 MB |
| **Purpose** | Semantic embedding only — NOT the DistilBERT classifier |

This is a **different model** from the DistilBERT classifier in `ml_service.py`.
The classifier scores P(reliable); the embedding model encodes semantic meaning for
similarity search. The two are entirely independent.

---

## Similarity Metric

pgvector **cosine distance** (`<=>` operator), converted to cosine similarity:

```
similarity_score = 1 - cosine_distance
```

Range: 0 (orthogonal/unrelated) to 1 (identical). Results are returned in
descending similarity order. Only results at or above the threshold are returned.

---

## Similarity Threshold

### Empirical Test

To determine a meaningful similarity cutoff, `ml_training/threshold_test.py` was
run against 20 held-out statements from the LIAR **test** split (not in the
training corpus). For each statement, the top-3 cosine similarity scores against
the training corpus were recorded.

### Score Distribution

```
Empirical Distribution (N=51 results across 20 LIAR test-split queries):
  Max    : 0.9833  (Exact/near-identical statement matches)
  Min    : 0.4604
  Mean   : 0.6133
  P90    : 0.7922  (Top 10% of matches score above 0.7922)
  P75    : 0.7009  (Top 25% of matches score above 0.7009)
  P50    : 0.5649  (Median match score)
  P25    : 0.5044  (75% of valid matches score above 0.5044)
  P10    : 0.4872  (Bottom 10% score below 0.4872)
```

### Chosen Threshold

**Chosen threshold: `SIMILARITY_THRESHOLD = 0.45`**

**Empirical Justification:**
- **Scores ≥ 0.75:** Direct claim matches or near-identical rewrites (e.g. "Obamacare is the biggest tax increase in history" → 0.9833).
- **Scores 0.50 – 0.74:** Strongly related topical claims (e.g. Keystone XL job numbers → 0.7550; Unemployment rates → 0.8108; Tax rates → 0.8076).
- **Scores 0.46 – 0.49:** Weakly related background context.
- **Scores < 0.45:** Nearest-neighbor noise (unrelated statements). Setting `SIMILARITY_THRESHOLD = 0.45` cleanly filters out unrelated noise while retaining high and moderate confidence matches.
- Returning `similar_claims: []` when no claims exceed 0.45 prevents surfacing misleading or irrelevant context to end users.

---

## Corpus Build

To rebuild the corpus from scratch (e.g., after retraining the classifier):

```bash
cd d:/DeceptiScan/backend
# Ensure pgvector extension is enabled and migration 002 applied:
flask db upgrade
# Build corpus (idempotent — truncates and rebuilds):
DATABASE_URL=postgresql://deceptiscan:password@localhost:5432/deceptiscan \
    python ml_training/build_retrieval_corpus.py
```

The script will print `Total rows inserted: N` at the end.

---

## API Integration

The retrieval layer is integrated into `POST /api/v1/analyze` as a non-fatal
secondary step:

```json
{
  "authenticityScore": 62.3,
  "classification": "mixed",
  "similar_claims": [
    {
      "statement_text": "Says the president signed a bill raising taxes on the middle class.",
      "label": "unreliable",
      "similarity_score": 0.71
    },
    ...
  ],
  "retrieval_status": "ok"
}
```

**Failure behavior:**
- If the retrieval service is unavailable (DB down, pgvector missing, embedding
  model not loaded), `similar_claims` is `null` and `retrieval_status` is
  `"unavailable"`. The classifier result is still returned normally.
- An empty list (`[]`) means retrieval succeeded but no claims exceeded the
  similarity threshold — not an error.
- `null` + `"unavailable"` means retrieval failed entirely — treat as a degraded
  response.

---

## Stage 2 Gap

The Google Fact Check Tools API integration (Stage 2) is **not built in Phase 2**.
When implemented, it will:
- Query live, independently fact-checked claims from Google's Fact Check database
- Return claims that are NOT from the LIAR training data, closing the circularity
  gap described above
- Be added as an additional retrieval source alongside (or replacing) the LIAR
  training corpus for production use

Until Stage 2 is complete, the `similar_claims` field should be clearly labeled
in the UI as "similar training examples" rather than "independent fact-checks".
The frontend wiring for this display is also not yet implemented (Phase 3 gap).
