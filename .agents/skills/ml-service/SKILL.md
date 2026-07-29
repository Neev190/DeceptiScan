---
name: ml-service
description: Implement and maintain the DistilBERT-based ML service for misinformation detection, including retry logic and low-confidence handling.
---

## ML Service — DeceptiScan

### Status
- Currently a **mock implementation** at `backend/services/ml_service.py`
- Real DistilBERT integration is **Task 12** (not yet started)
- Low confidence handling is **Task 13** (not yet started)
- ML retry logic is **Task 14** (not yet started)

### Expected Interface

```python
class MLService:
    async def analyze(text: str) -> AnalysisResult
    async def preprocess(text: str) -> list[str]
    async def extract_sentences(text: str) -> list[Sentence]
    async def classify_sentence(sentence: str) -> ClassificationResult
    async def calculate_authenticity_score(sentence_results) -> float
```

### Classification Output

```python
@dataclass
class ClassificationResult:
    text: str
    label: str              # "reliable" | "unreliable" | "neutral"
    confidence: float       # 0–1
    probabilities: dict     # {label: probability}
    features: list[str]     # Key features influencing classification
    category: str           # Type of content
```

### Model Details (from design.md)
- **Model:** `distilbert-base-uncased` fine-tuned on fake news datasets
- **Max sequence length:** 512 tokens
- **Batch size:** 16
- **Input:** English news article text (max 50,000 chars)
- **Output per sentence:** score (0–100), confidence (0–1), flags[], explanation

### Dependency Versions
```txt
transformers==4.35.0
torch==2.1.0
sentencepiece==0.1.99
numpy==1.26.0
```

### Score Calculation
- Per-sentence scores are averaged (weighted by confidence)
- Final `authenticityScore` = 0–100 integer
- Classification thresholds: reliable ≥75, mixed 40–74, unreliable <40

### Low Confidence (Task 13)
- If model confidence < 0.3 → classification = `"unknown"`
- Include `warning` field in response
- Frontend shows disclaimer instead of red/green highlighting

### Retry Logic (Task 14)
- Max 3 attempts with exponential backoff
- Error code: `ANALYSIS_FAILED`
- Include `retryAfter` (seconds) in error details

### Recency-Based Routing (Task 27)
- Future feature: detect "new" content (no cache hit + recent dates)
- Route through external fact-check APIs (Google Fact Check Tools)
- Fallback to news search if no match
- Return `unverified_style_estimate` label for new unverifiable content

### Current Mock Implementation

The mock at `services/ml_service.py` returns deterministic results for testing:

```python
# Current behavior:
# - Splits text on sentence boundaries
# - Returns random-appearing but deterministic scores
# - Uses fixed categories and flags
# - ProcessingTime is simulated

# To be replaced with real DistilBERT inference when Task 12 is implemented
```
