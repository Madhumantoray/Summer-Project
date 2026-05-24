from functools import lru_cache

MODEL_NAME = "ProsusAI/finbert"


@lru_cache(maxsize=1)
def get_finbert_pipeline():
    try:
        from transformers import pipeline
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "transformers is required for FinBERT sentiment analysis"
        ) from exc

    try:
        return pipeline("text-classification", model=MODEL_NAME, tokenizer=MODEL_NAME)
    except Exception as exc:
        raise RuntimeError(
            "Unable to load ProsusAI/finbert. Check internet access and installed torch/transformers packages."
        ) from exc


def analyze_sentiment(articles):
    if not articles:
        return []

    classifier = get_finbert_pipeline()
    headlines = [article["headline"] for article in articles]
    try:
        predictions = classifier(headlines, truncation=True)
    except Exception as exc:
        raise RuntimeError("Unable to run FinBERT sentiment inference") from exc

    scored_articles = []
    for article, prediction in zip(articles, predictions):
        label = prediction["label"].lower()
        confidence = float(prediction["score"])

        if label == "positive":
            sentiment_score = confidence
        elif label == "negative":
            sentiment_score = -confidence
        else:
            sentiment_score = 0.0

        scored_articles.append(
            {
                "headline": article["headline"],
                "published_date": article["published_date"],
                "label": label,
                "confidence": confidence,
                "sentiment_score": sentiment_score,
            }
        )

    return scored_articles
