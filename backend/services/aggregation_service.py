import pandas as pd


def aggregate_daily_sentiment(scored_articles):
    if not scored_articles:
        return []

    df = pd.DataFrame(scored_articles)
    grouped = (
        df.groupby("published_date")
        .agg(
            avg_sentiment=("sentiment_score", "mean"),
            article_count=("sentiment_score", "count"),
        )
        .reset_index()
        .rename(columns={"published_date": "date"})
        .sort_values("date")
    )

    grouped["rolling_sentiment"] = (
        grouped["avg_sentiment"].rolling(window=7, min_periods=1).mean()
    )
    grouped["avg_sentiment"] = grouped["avg_sentiment"].round(4)
    grouped["rolling_sentiment"] = grouped["rolling_sentiment"].round(4)

    return grouped[
        ["date", "avg_sentiment", "rolling_sentiment", "article_count"]
    ].to_dict(orient="records")
