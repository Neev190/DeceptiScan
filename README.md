# DeceptiScan

DeceptiScan is a web-based misinformation detection tool using NLP (DistilBERT) to analyze news content. It provides sentence-level flagging of suspicious claims and an overall authenticity score (0–100).

## Model Checkpoint

The fine-tuned DistilBERT model checkpoint automatically downloads from Hugging Face Hub (`Yakuza190/deceptiscan-distilbert-liar`) on the first run of the backend ML service. No manual training step or weight download is required to run or demo the application.

## Roadmap

- [x] DistilBERT classifier (Phase 1) — binary reliable/unreliable sentence-level scoring
- [x] Retrieval-augmented layer — Stage 1: pgvector + LIAR training corpus (Phase 2)
- [ ] Retrieval-augmented layer — Stage 2: Google Fact Check Tools API (planned)
- [ ] Frontend wiring for similar_claims display (planned)
