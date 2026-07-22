export function buildSentimentLineData(data) {
  if (!data || !Array.isArray(data)) return [];

  return data
    .map((item) => {
      let time = item.time ?? item.date;
      const value =
        item.value ??
        item.avg_sentiment ??
        item.sentiment_score ??
        item.score;

      if (typeof time === "string") {
        time = time.split("T")[0];
      }

      if (!time || value == null || Number.isNaN(Number(value))) {
        return null;
      }

      return {
        time,
        value: Number(value),
      };
    })
    .filter(Boolean);
}
