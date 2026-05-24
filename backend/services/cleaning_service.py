import html
import re

SOURCE_SUFFIX_PATTERN = re.compile(r"\s+-\s+[^-]+$")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_headline(headline: str) -> str:
    cleaned = html.unescape(headline)
    cleaned = SOURCE_SUFFIX_PATTERN.sub("", cleaned)
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned)
    return cleaned.strip()


def clean_articles(articles):
    cleaned_articles = []

    for article in articles:
        headline = clean_headline(article["headline"])
        if not headline:
            continue

        cleaned_articles.append(
            {
                "headline": headline,
                "published_date": article["published_date"],
            }
        )

    return cleaned_articles
