# DeceptiScan

DeceptiScan is a web-based misinformation detection tool using NLP (DistilBERT) to analyze news content. It provides sentence-level flagging of suspicious claims and an overall authenticity score (0–100).

## Model Checkpoint

The fine-tuned DistilBERT model checkpoint automatically downloads from Hugging Face Hub (`Yakuza190/deceptiscan-distilbert-liar`) on the first run of the backend ML service. No manual training step or weight download is required to run or demo the application.
