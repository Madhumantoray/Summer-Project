"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function SentimentChart({
  data,
  error = "",
  isLoading,
  symbol,
}) {
  const summary = buildSummary(data);

  return (
    <section className="mb-4 overflow-hidden rounded-lg border border-[var(--border-panel)] bg-[var(--surface-chart)] shadow-[var(--shadow-panel)] transition-colors duration-300">
      <div className="flex flex-col gap-3 border-b border-[var(--border-subtle)] px-3 py-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-mono text-xs uppercase tracking-[0.16em] text-[var(--text-secondary)]">
            News Sentiment
          </div>
          <div className="mt-1 text-xs text-[var(--text-muted)]">
            Google News RSS with FinBERT daily aggregation for {symbol}.NS
          </div>
        </div>

        <div className="grid grid-cols-3 overflow-hidden rounded-md border border-[var(--border-subtle)] bg-[var(--surface-raised)]">
          <SummaryCell
            label="Current"
            value={summary.currentLabel}
            tone={summary.currentTone}
          />
          <SummaryCell
            label="Trend"
            value={summary.trendLabel}
            tone={summary.trendTone}
          />
          <SummaryCell
            label="Articles"
            value={summary.articleCount.toString()}
            tone="text-[var(--text-primary)]"
          />
        </div>
      </div>

      <div className="px-3 py-3">
        {isLoading && (
          <PanelMessage
            message="Loading sentiment analysis."
            tone="text-[var(--text-secondary)]"
          />
        )}

        {!isLoading && error && (
          <PanelMessage message={error} tone="text-[var(--accent-negative)]" />
        )}

        {!isLoading && !error && data.length === 0 && (
          <PanelMessage
            message="No news available for this symbol."
            tone="text-[var(--text-secondary)]"
          />
        )}

        {!isLoading && !error && data.length > 0 && (
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 16, right: 18, bottom: 0, left: -18 }}>
                <CartesianGrid stroke="var(--border-subtle)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  minTickGap={28}
                  stroke="var(--text-muted)"
                  tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  domain={[-1, 1]}
                  stroke="var(--text-muted)"
                  tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                  tickLine={false}
                />
                <ReferenceLine y={0} stroke="var(--border-control)" />
                <Tooltip content={<SentimentTooltip />} />
                <Line
                  type="monotone"
                  dataKey="avg_sentiment"
                  name="Daily sentiment"
                  dot={false}
                  stroke={
                    summary.latestAvg >= 0
                      ? "var(--accent-positive)"
                      : "var(--accent-negative)"
                  }
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="rolling_sentiment"
                  name="7 day rolling"
                  dot={false}
                  stroke={
                    summary.latestRolling >= 0
                      ? "var(--accent-positive)"
                      : "var(--accent-negative)"
                  }
                  strokeDasharray="5 4"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </section>
  );
}

function SummaryCell({ label, tone, value }) {
  return (
    <div className="min-w-[88px] border-r border-[var(--border-subtle)] px-3 py-2 last:border-r-0">
      <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--text-muted)]">
        {label}
      </div>
      <div className={`mt-1 truncate font-mono text-xs font-semibold ${tone}`}>
        {value}
      </div>
    </div>
  );
}

function PanelMessage({ message, tone }) {
  return (
    <div className={`rounded-md border border-[var(--border-subtle)] bg-[var(--surface-raised)] px-3 py-3 text-sm ${tone}`}>
      {message}
    </div>
  );
}

function SentimentTooltip({ active, payload, label }) {
  if (!active || !payload?.length) {
    return null;
  }

  const point = payload[0]?.payload;

  return (
    <div className="rounded-md border border-[var(--border-control)] bg-[var(--surface-raised)] px-3 py-2 text-xs shadow-[var(--shadow-panel)]">
      <div className="mb-1 font-mono text-[var(--text-primary)]">{label}</div>
      <div className="text-[var(--text-secondary)]">
        Daily: {Number(point.avg_sentiment).toFixed(2)}
      </div>
      <div className="text-[var(--text-secondary)]">
        Rolling: {Number(point.rolling_sentiment).toFixed(2)}
      </div>
      <div className="text-[var(--text-muted)]">Articles: {point.article_count}</div>
    </div>
  );
}

function buildSummary(data) {
  if (data.length === 0) {
    return {
      articleCount: 0,
      currentLabel: "-",
      currentTone: "text-[var(--text-muted)]",
      latestAvg: 0,
      latestRolling: 0,
      trendLabel: "-",
      trendTone: "text-[var(--text-muted)]",
    };
  }

  const latest = data[data.length - 1];
  const previous = data[data.length - 2];
  const latestAvg = Number(latest.avg_sentiment);
  const latestRolling = Number(latest.rolling_sentiment);
  const previousRolling = previous ? Number(previous.rolling_sentiment) : latestRolling;
  const articleCount = data.reduce(
    (total, point) => total + Number(point.article_count),
    0,
  );

  return {
    articleCount,
    currentLabel: latestAvg > 0.05 ? "Positive" : latestAvg < -0.05 ? "Negative" : "Neutral",
    currentTone:
      latestAvg > 0.05
        ? "text-[var(--accent-positive)]"
        : latestAvg < -0.05
          ? "text-[var(--accent-negative)]"
          : "text-[var(--text-secondary)]",
    latestAvg,
    latestRolling,
    trendLabel:
      latestRolling > previousRolling
        ? "Improving"
        : latestRolling < previousRolling
          ? "Weakening"
          : "Flat",
    trendTone:
      latestRolling >= previousRolling
        ? "text-[var(--accent-positive)]"
        : "text-[var(--accent-negative)]",
  };
}
