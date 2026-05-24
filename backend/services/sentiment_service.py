import re

try:
    from backend.services.aggregation_service import aggregate_daily_sentiment
    from backend.services.cleaning_service import clean_articles
    from backend.services.finbert_service import analyze_sentiment
    from backend.services.news_service import fetch_news_headlines
except ModuleNotFoundError:
    from services.aggregation_service import aggregate_daily_sentiment
    from services.cleaning_service import clean_articles
    from services.finbert_service import analyze_sentiment
    from services.news_service import fetch_news_headlines

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,20}$")


def get_sentiment_records(symbol: str):
    normalized_symbol = validate_symbol(symbol)
    articles = fetch_news_headlines(normalized_symbol)
    cleaned_articles = clean_articles(articles)

    if not cleaned_articles:
        return []

    scored_articles = analyze_sentiment(cleaned_articles)
    return aggregate_daily_sentiment(scored_articles)


def validate_symbol(symbol: str) -> str:
    normalized_symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized_symbol):
        raise ValueError("Invalid symbol")

    return normalized_symbol
