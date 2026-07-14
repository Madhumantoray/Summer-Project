"use client";

export default function NewsPanel({ news }) {
  if (!news || news.length === 0) {
    return (
      <div className="mt-4 rounded-xl border border-[var(--border-panel)] bg-[var(--surface-chart)] p-6 text-center text-[var(--text-muted)]">
        No recent news found for this symbol.
      </div>
    );
  }

  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-[var(--border-panel)] bg-[var(--surface-chart)] shadow-[var(--shadow-panel)]">
      <div className="border-b border-[var(--border-subtle)] px-4 py-3">
        <h3 className="font-mono text-xs uppercase tracking-[0.16em] text-[var(--text-secondary)]">
          Recent News & Sentiment
        </h3>
      </div>
      <div className="max-h-[400px] overflow-y-auto p-4">
        <ul className="flex flex-col gap-4">
          {news.map((item, idx) => {
            const isPositive = item.sentiment_label === "positive";
            const isNegative = item.sentiment_label === "negative";
            const badgeClass = isPositive
              ? "bg-[var(--accent-positive)]/20 text-[var(--accent-positive)]"
              : isNegative
                ? "bg-[var(--accent-negative)]/20 text-[var(--accent-negative)]"
                : "bg-[var(--accent-info)]/20 text-[var(--accent-info)]";

            return (
              <li
                key={`${item.published_at || "unknown"}-${idx}`}
                className="flex flex-col gap-1 border-b border-[var(--border-subtle)] pb-4 last:border-0 last:pb-0"
              >
                <div className="text-sm font-medium text-[var(--text-primary)]">
                  {item.headline || "Untitled"}
                </div>
                <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                  <span>{item.source || "google_news_rss"}</span>
                  <span>•</span>
                  <span>
                    {item.published_at ? new Date(item.published_at).toLocaleDateString() : "Unknown date"}
                  </span>
                  <span>•</span>
                  <span className={`rounded-full px-2 py-0.5 ${badgeClass}`}>
                    {item.sentiment_label || "unknown"}{" "}
                    {typeof item.sentiment_confidence === "number"
                      ? `(${Math.round(item.sentiment_confidence * 100)}%)`
                      : ""}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

