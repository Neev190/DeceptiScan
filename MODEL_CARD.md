# Model Card

## Model Overview

**Base Architecture**: DistilBERT (`distilbert-base-uncased`) fine-tuned on the LIAR dataset  
**Task**: Binary text classification for authenticity/reliability scoring  
**Reported Accuracy**: 64.57% on LIAR test split (verified from `backend/ml_models/metrics.json`)  
**Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (used for retrieval of similar claims)

The model produces binary classifications (`reliable` vs `unreliable`) for individual sentences, which are aggregated to generate article-level authenticity scores from 0-100.

## Training Data

**Dataset**: LIAR (Wang, 2017) - ~12,800 human-verified political statements from PolitiFact  
**Original Labels**: 6-way classification (`pants-fire`, `false`, `barely-true`, `half-true`, `mostly-true`, `true`)  
**Label Mapping**: Binarized to `reliable` (`mostly-true`, `true`) and `unreliable` (`pants-fire`, `false`, `barely-true`)  
**Dropped Data**: `half-true` labels (~22% of dataset) excluded as genuinely ambiguous  

**Preprocessing**: Text truncated to 64 tokens maximum. Claims sanitized to remove injection patterns before downstream processing.

## Intended Use and Limitations

**Designed For**: 
- Sentence-level reliability scoring in news content analysis
- Supporting evidence in content authenticity evaluation workflows
- Portfolio/demonstration of misinformation detection techniques

**NOT Designed For**:
- Ground-truth fact-checking or professional verification substitute  
- High-stakes decisions (legal, medical, electoral) without human oversight
- Real-time content moderation at scale without review
- Non-English text analysis (undefined behavior)

**Accuracy Limitations**: 64.57% accuracy means approximately 1 in 3 predictions may be incorrect. This represents the documented performance ceiling for statement-only classification on LIAR without additional metadata features.

**Project Context**: This is a portfolio/demonstration project, not a production fact-checking system suitable for critical decision-making.

## Adversarial/Sensitivity Evaluation

**Methodology**: Systematic sensitivity analysis using matched content pairs to measure model consistency under input variations.

**Results**: 
- Mean Score Delta: -2.48 points
- Maximum Absolute Delta: 3.7 points  
- Both values under 15-point stability threshold
- Model Determinism: Control group standard deviation = 0.0 (fully deterministic)

**Important**: Results represent sensitivity analysis, not bias testing. No causal claims about fairness or discrimination are made - this measures technical consistency only.

## Known Limitations

**Accuracy Ceiling**: 64.57% accuracy represents approximately 1 in 3 incorrect predictions. This performance level is consistent with published literature for statement-only classification on LIAR dataset without additional metadata.

**Domain Specificity**: LIAR consists of US political statements from PolitiFact. Model may perform poorly on:
- Scientific/medical misinformation  
- Non-political news content
- Social media posts with different language register
- Content outside the temporal scope of LIAR training data

**Linguistic Limitations**:
- No understanding of sarcasm or irony
- Context-dependent claims requiring external information for verification
- Limited performance on very short text fragments (< 5 words)
- Undefined behavior on non-English content

**Training Recency**: Model knowledge bounded by LIAR dataset content, not current events or recent claims.

## Technical Details

**Training Configuration** (verified from `metrics.json`):
- Epochs: 1
- Batch Size: 32  
- Learning Rate: 2e-5
- Weight Decay: 0.01
- Warmup Ratio: 0.1
- Max Sequence Length: 64 tokens
- Seed: 42

**Performance Metrics**:
- Test Accuracy: 0.6457 (64.57%)
- Precision (macro): 0.6418
- Recall (macro): 0.6378  
- F1 (macro): 0.6382
- Majority Class Baseline: 0.5472

**Test Confusion Matrix**:
```
                    Predicted
                Unreliable  Reliable
Actual Unreliable    401      155
Actual Reliable      205      255
```

**Model Checkpoint**: Automatically downloads from Hugging Face Hub (`Yakuza190/deceptiscan-distilbert-liar`) on first backend initialization.