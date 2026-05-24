"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import ChartWorkspace from "./components/ChartWorkspace";
import ControlsBar from "./components/ControlsBar";
import MetricStrip from "./components/MetricStrip";
import StatusMessage from "./components/StatusMessage";
import ThemeToggle from "./components/ThemeToggle";
import { useSentimentData } from "./hooks/useSentimentData";
import { useStockData } from "./hooks/useStockData";
import { useThemeMode } from "./hooks/useThemeMode";
import { calculateReturns } from "./lib/marketData";

const DEFAULT_SYMBOL = "RELIANCE";
const DEFAULT_TIMEFRAME = "1Y";
const SentimentChart = dynamic(() => import("./components/SentimentChart"), {
  ssr: false,
  loading: () => <SentimentChartShell message="Preparing sentiment panel." />,
});

export default function Home() {
  const { themeMode, toggleTheme } = useThemeMode();
  const [filters, setFilters] = useState({
    symbol: DEFAULT_SYMBOL,
    timeframe: DEFAULT_TIMEFRAME,
    startDate: "",
    endDate: "",
  });
  const [isLineChart, setIsLineChart] = useState(false);
  const [hoverData, setHoverData] = useState(null);

  const { data, error, isLoading } = useStockData(filters);
  const shouldLoadSentiment = !isLoading;
  const {
    data: sentimentData,
    error: sentimentError,
    isLoading: isSentimentLoading,
  } = useSentimentData(filters.symbol, shouldLoadSentiment);
  const returns = useMemo(() => calculateReturns(data), [data]);

  return (
    <main className="min-h-screen bg-[var(--surface-page)] text-[var(--text-primary)] transition-colors duration-300">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px] flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-[var(--border-subtle)] pb-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <div className="mb-2 flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-[var(--accent-positive)] shadow-[0_0_0_4px_var(--accent-positive-soft)]" />
              <span className="font-mono text-xs uppercase tracking-[0.18em] text-[var(--text-muted)]">
                NSE Equity Research
              </span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
              Stock Research
            </h1>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
              Price action, volume, RSI, MACD and period return in one compact
              research workspace.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <MetricStrip returns={returns} symbol={filters.symbol} />
            <ThemeToggle onToggle={toggleTheme} />
          </div>
        </header>

        <ControlsBar
          key={`${filters.symbol}-${filters.timeframe}-${filters.startDate}-${filters.endDate}`}
          filters={filters}
          isLineChart={isLineChart}
          isLoading={isLoading}
          onApplyFilters={(nextFilters) => {
            setFilters(nextFilters);
            setHoverData(null);
          }}
          onToggleChartMode={() => setIsLineChart((current) => !current)}
        />

        <StatusMessage error={error} isLoading={isLoading} hasData={data.length > 0} />

        <ChartWorkspace
          data={data}
          hoverData={hoverData}
          isLineChart={isLineChart}
          isLoading={isLoading}
          themeMode={themeMode}
          onHoverData={setHoverData}
        />

        <SentimentChart
          data={shouldLoadSentiment ? sentimentData : []}
          error={sentimentError}
          isLoading={isSentimentLoading || !shouldLoadSentiment}
          symbol={filters.symbol}
        />
      </div>
    </main>
  );
}

function SentimentChartShell({ message }) {
  return (
    <section className="mb-4 overflow-hidden rounded-lg border border-[var(--border-panel)] bg-[var(--surface-chart)] shadow-[var(--shadow-panel)] transition-colors duration-300">
      <div className="border-b border-[var(--border-subtle)] px-3 py-3">
        <div className="font-mono text-xs uppercase tracking-[0.16em] text-[var(--text-secondary)]">
          News Sentiment
        </div>
        <div className="mt-1 text-xs text-[var(--text-muted)]">
          Google News RSS with FinBERT daily aggregation
        </div>
      </div>
      <div className="px-3 py-3">
        <div className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-raised)] px-3 py-3 text-sm text-[var(--text-secondary)]">
          {message}
        </div>
      </div>
    </section>
  );
}
