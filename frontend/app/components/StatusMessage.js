export default function StatusMessage({ error, hasData, isLoading }) {
  if (isLoading) {
    return (
      <div className="mb-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-secondary)]">
        Fetching market data and recalculating indicators.
      </div>
    );
  }

  if (error) {
    return (
      <div className="mb-3 rounded-lg border border-[var(--accent-negative-soft)] bg-[var(--surface-error)] px-3 py-2 text-sm text-[var(--accent-negative)]">
        {error}
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="mb-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--text-secondary)]">
        No chart data available for the selected parameters.
      </div>
    );
  }

  return null;
}
