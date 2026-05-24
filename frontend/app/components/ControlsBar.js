"use client";

import { useState } from "react";

const TIMEFRAMES = ["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"];

export default function ControlsBar({
  filters,
  isLineChart,
  isLoading,
  onApplyFilters,
  onToggleChartMode,
}) {
  const [draftFilters, setDraftFilters] = useState(filters);
  const maxDate = new Date().toISOString().split("T")[0];

  function updateDraft(key, value) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function applyFilters(event) {
    event.preventDefault();
    onApplyFilters({
      ...draftFilters,
      symbol: draftFilters.symbol.trim().toUpperCase() || filters.symbol,
    });
  }

  function resetDates() {
    const nextFilters = { ...draftFilters, startDate: "", endDate: "" };
    setDraftFilters(nextFilters);
    onApplyFilters(nextFilters);
  }

  return (
    <form
      onSubmit={applyFilters}
      className="my-4 grid gap-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] p-3 transition-colors duration-300 xl:grid-cols-[minmax(150px,220px)_auto_auto_auto_auto_auto] xl:items-end"
    >
      <label className="control-field">
        <span>Symbol</span>
        <input
          type="text"
          value={draftFilters.symbol}
          onChange={(event) => updateDraft("symbol", event.target.value.toUpperCase())}
          placeholder="RELIANCE"
          className="input-control font-mono"
        />
      </label>

      <label className="control-field">
        <span>Timeframe</span>
        <select
          value={draftFilters.timeframe}
          onChange={(event) => updateDraft("timeframe", event.target.value)}
          className="input-control min-w-[110px]"
        >
          {TIMEFRAMES.map((timeframe) => (
            <option key={timeframe}>{timeframe}</option>
          ))}
        </select>
      </label>

      <label className="control-field">
        <span>Start</span>
        <input
          type="date"
          max={maxDate}
          value={draftFilters.startDate}
          onChange={(event) => updateDraft("startDate", event.target.value)}
          className="input-control"
        />
      </label>

      <label className="control-field">
        <span>End</span>
        <input
          type="date"
          max={maxDate}
          value={draftFilters.endDate}
          onChange={(event) => updateDraft("endDate", event.target.value)}
          className="input-control"
        />
      </label>

      <div className="flex items-end gap-2">
        <button type="submit" disabled={isLoading} className="button-primary">
          {isLoading ? "Loading" : "Show"}
        </button>
        <button type="button" onClick={resetDates} className="button-secondary">
          Reset Dates
        </button>
      </div>

      <div className="flex items-end">
        <div className="inline-flex h-10 rounded-md border border-[var(--border-control)] bg-[var(--surface-control)] p-0.5">
          <button
            type="button"
            onClick={isLineChart ? onToggleChartMode : undefined}
            className={`segmented-button ${!isLineChart ? "segmented-button-active" : ""}`}
          >
            Candle
          </button>
          <button
            type="button"
            onClick={!isLineChart ? onToggleChartMode : undefined}
            className={`segmented-button ${isLineChart ? "segmented-button-active" : ""}`}
          >
            Line
          </button>
        </div>
      </div>
    </form>
  );
}
