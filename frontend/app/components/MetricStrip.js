export default function MetricStrip({ returns, symbol }) {
  const isPositive = Number(returns?.percent ?? 0) >= 0;

  return (
    <div className="grid min-w-[280px] grid-cols-3 overflow-hidden rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] transition-colors duration-300">
      <MetricCell label="Ticker" value={`${symbol}.NS`} tone="text-[var(--text-primary)]" />
      <MetricCell
        label="Return"
        value={returns ? `${returns.percent}%` : "-"}
        tone={isPositive ? "text-[var(--accent-positive)]" : "text-[var(--accent-negative)]"}
      />
      <MetricCell
        label="Close"
        value={returns ? returns.last : "-"}
        tone="text-[var(--text-primary)]"
        detail={returns ? `${returns.first} to ${returns.last}` : ""}
      />
    </div>
  );
}

function MetricCell({ detail, label, tone, value }) {
  return (
    <div className="border-r border-[var(--border-subtle)] px-3 py-2 last:border-r-0">
      <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-[var(--text-muted)]">
        {label}
      </div>
      <div className={`mt-1 truncate font-mono text-sm font-semibold ${tone}`}>
        {value}
      </div>
      {detail && <div className="mt-0.5 truncate text-[10px] text-[var(--text-muted)]">{detail}</div>}
    </div>
  );
}
