"use client";

export default function HypothesisPanel({ analysisData, isLoading, error }) {
  if (isLoading) {
    return (
      <div className="mt-4 p-4 text-center text-[var(--text-muted)]">
        Loading analysis...
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 p-4 text-center text-[var(--accent-negative)]">
        {error}
      </div>
    );
  }

  if (!analysisData) {
    return null;
  }

  const { event_study, correlation, regression, data_points } = analysisData;

  const renderPValue = (p) => {
    if (p === null || p === undefined) return "N/A";
    if (p < 0.01)
      return (
        <span className="text-[var(--accent-positive)]">
          ** (p={p.toFixed(3)})
        </span>
      );
    if (p < 0.05)
      return (
        <span className="text-[var(--accent-positive)]">
          * (p={p.toFixed(3)})
        </span>
      );
    return <span className="text-[var(--text-muted)]">(p={p.toFixed(3)})</span>;
  };

  return (
    <div className="mt-6 flex flex-col gap-6">
      <div className="border-b border-[var(--border-subtle)] pb-2">
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">
          Research Analysis Dashboard
        </h2>
        <p className="text-sm text-[var(--text-secondary)]">
          Based on {data_points} sentiment observation days with computed forward
          returns.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--border-panel)] bg-[var(--surface-chart)] p-4 shadow-[var(--shadow-panel)]">
          <h3 className="mb-4 border-b border-[var(--border-subtle)] pb-2 font-mono text-sm uppercase tracking-wider text-[var(--text-secondary)]">
            Event Study: Returns After Extreme Sentiment
          </h3>

          <div className="mb-4">
            <h4 className="mb-2 text-sm font-semibold text-[var(--accent-negative)]">
              After Top 10% Negative Days (n={event_study.negative_events.count})
            </h4>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)]">
                  <th className="py-2 font-medium">1-Day</th>
                  <th className="py-2 font-medium">3-Day</th>
                  <th className="py-2 font-medium">7-Day</th>
                  <th className="py-2 font-medium">30-Day</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="py-2">
                    {(event_study.negative_events.avg_return_1d * 100).toFixed(2)}%
                  </td>
                  <td className="py-2">
                    {(event_study.negative_events.avg_return_3d * 100).toFixed(2)}%
                  </td>
                  <td className="py-2">
                    {(event_study.negative_events.avg_return_7d * 100).toFixed(2)}%
                  </td>
                  <td className="py-2">
                    {(event_study.negative_events.avg_return_30d * 100).toFixed(2)}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div>
            <h4 className="mb-2 text-sm font-semibold text-[var(--accent-positive)]">
              After Top 10% Positive Days (n={event_study.positive_events.count})
            </h4>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)]">
                  <th className="py-2 font-medium">1-Day</th>
                  <th className="py-2 font-medium">3-Day</th>
                  <th className="py-2 font-medium">7-Day</th>
                  <th className="py-2 font-medium">30-Day</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="py-2">
                    {(event_study.positive_events.avg_return_1d * 100).toFixed(2)}%
                  </td>
                  <td className="py-2">
                    {(event_study.positive_events.avg_return_3d * 100).toFixed(2)}%
                  </td>
                  <td className="py-2">
                    {(event_study.positive_events.avg_return_7d * 100).toFixed(2)}%
                  </td>
                  <td className="py-2">
                    {(event_study.positive_events.avg_return_30d * 100).toFixed(2)}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-[var(--border-panel)] bg-[var(--surface-chart)] p-4 shadow-[var(--shadow-panel)]">
            <h3 className="mb-4 border-b border-[var(--border-subtle)] pb-2 font-mono text-sm uppercase tracking-wider text-[var(--text-secondary)]">
              Correlation (Pearson)
            </h3>
            <ul className="space-y-2 text-sm">
              <li className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span>Sentiment ↔ 1d Return:</span>
                <span>
                  {correlation.Return_1d.pearson_r?.toFixed(3)}{" "}
                  {renderPValue(correlation.Return_1d.p_value)}
                </span>
              </li>
              <li className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span>Sentiment ↔ 3d Return:</span>
                <span>
                  {correlation.Return_3d.pearson_r?.toFixed(3)}{" "}
                  {renderPValue(correlation.Return_3d.p_value)}
                </span>
              </li>
              <li className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                <span>Sentiment ↔ 7d Return:</span>
                <span>
                  {correlation.Return_7d.pearson_r?.toFixed(3)}{" "}
                  {renderPValue(correlation.Return_7d.p_value)}
                </span>
              </li>
              <li className="flex justify-between">
                <span>Sentiment ↔ 30d Return:</span>
                <span>
                  {correlation.Return_30d.pearson_r?.toFixed(3)}{" "}
                  {renderPValue(correlation.Return_30d.p_value)}
                </span>
              </li>
            </ul>
          </div>

          {regression && (
            <div className="rounded-xl border border-[var(--border-panel)] bg-[var(--surface-chart)] p-4 shadow-[var(--shadow-panel)]">
              <h3 className="mb-4 border-b border-[var(--border-subtle)] pb-2 font-mono text-sm uppercase tracking-wider text-[var(--text-secondary)]">
                OLS Regression (7d Return)
              </h3>
              <ul className="space-y-2 text-sm">
                <li className="flex justify-between border-b border-[var(--border-subtle)] pb-1">
                  <span>R-Squared:</span>
                  <span>{regression.rsquared.toFixed(4)}</span>
                </li>
                <li className="flex justify-between">
                  <span>Sentiment Coef:</span>
                  <span>
                    {regression.coef_sentiment.toFixed(4)}{" "}
                    {renderPValue(regression.p_value)}
                  </span>
                </li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

