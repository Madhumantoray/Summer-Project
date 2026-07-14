export function buildSentimentLineData(data) {
  if (!data || !Array.isArray(data)) return [];

  return data
    .map((item) => {
      // GitHub main returns:
      // { date, avg_sentiment, rolling_sentiment, article_count }
      if (item.time !== undefined && item.value !== undefined) {
        return {
          time: item.time,
          value: Number(item.value),
        };
      }

      const time = item.time ?? item.date;
      const value = item.value ?? item.avg_sentiment ?? item.sentiment_score ?? item.score;

      if (!time || typeof value !== "number" || Number.isNaN(Number(value))) {
        return null;
      }

      return {
        time,
        value: Number(value),
      };
    })
    .filter(Boolean);
}

