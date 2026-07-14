"use client";

import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

function mean(values) {
  if (!values.length) return 0;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function pearson(xs, ys) {
  if (xs.length !== ys.length || xs.length < 3) return null;
  const xMean = mean(xs);
  const yMean = mean(ys);
  let num = 0;
  let denomX = 0;
  let denomY = 0;
  for (let i = 0; i < xs.length; i += 1) {
    const dx = xs[i] - xMean;
    const dy = ys[i] - yMean;
    num += dx * dy;
    denomX += dx * dx;
    denomY += dy * dy;
  }
  const denom = Math.sqrt(denomX * denomY);
  if (!denom) return null;
  return num / denom;
}

function quantile(sortedValues, q) {
  if (!sortedValues.length) return null;
  const pos = (sortedValues.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sortedValues[base + 1] === undefined) return sortedValues[base];
  return sortedValues[base] + rest * (sortedValues[base + 1] - sortedValues[base]);
}

function studentT_CDF(t, df) {
  if (df <= 0) return 0.5;
  const x = t * (1 - 1 / (4 * df)) / Math.sqrt(1 + (t * t) / (2 * df));
  const z = Math.abs(x);
  const p = 1.0 / (1.0 + 0.2316419 * z);
  const prob = 1.0 - 0.3989422804 * Math.exp(-0.5 * z * z) * p * 
      (0.31938153 + p * (-0.356563782 + p * (1.781477937 + p * (-1.821255978 + 1.330274429 * p))));
  return t > 0 ? prob : 1 - prob;
}

function calculatePValue(r, n) {
  if (n <= 2 || r === 1 || r === -1) return 0;
  const t = r * Math.sqrt((n - 2) / (1 - r * r));
  const cdf = studentT_CDF(t, n - 2);
  return 2 * (1 - cdf);
}

function buildEventStudy(rows) {
  const usable = rows.filter((r) => typeof r.sentiment_score === "number");
  if (usable.length < 3) {
    return {
      event_study: {
        positive_events: { count: 0, avg_return_1d: 0, avg_return_3d: 0, avg_return_7d: 0, avg_return_30d: 0 },
        negative_events: { count: 0, avg_return_1d: 0, avg_return_3d: 0, avg_return_7d: 0, avg_return_30d: 0 },
      },
      thresholds: { pos: null, neg: null },
      usableCount: usable.length,
    };
  }

  const scores = usable.map((r) => r.sentiment_score).slice().sort((a, b) => a - b);
  const thresholdPos = quantile(scores, 0.9);
  const thresholdNeg = quantile(scores, 0.1);

  const pos = usable.filter((r) => r.sentiment_score >= thresholdPos);
  const neg = usable.filter((r) => r.sentiment_score <= thresholdNeg);

  const avg = (subset, key) =>
    mean(
      subset
        .map((r) => r[key])
        .filter((v) => typeof v === "number"),
    );

  return {
    event_study: {
      positive_events: {
        count: pos.length,
        avg_return_1d: avg(pos, "future_return_1d"),
        avg_return_3d: avg(pos, "future_return_3d"),
        avg_return_7d: avg(pos, "future_return_7d"),
        avg_return_30d: avg(pos, "future_return_30d"),
      },
      negative_events: {
        count: neg.length,
        avg_return_1d: avg(neg, "future_return_1d"),
        avg_return_3d: avg(neg, "future_return_3d"),
        avg_return_7d: avg(neg, "future_return_7d"),
        avg_return_30d: avg(neg, "future_return_30d"),
      },
    },
    thresholds: { pos: thresholdPos, neg: thresholdNeg },
    usableCount: usable.length,
  };
}

function buildCorrelation(rows) {
  const usable = rows.filter((r) => typeof r.sentiment_score === "number");
  const horizons = [
    ["Return_1d", "future_return_1d"],
    ["Return_3d", "future_return_3d"],
    ["Return_7d", "future_return_7d"],
    ["Return_30d", "future_return_30d"],
  ];

  const out = {};
  for (const [label, key] of horizons) {
    const pairs = usable
      .filter((r) => typeof r[key] === "number")
      .map((r) => [r.sentiment_score, r[key]]);
    const xs = pairs.map((p) => p[0]);
    const ys = pairs.map((p) => p[1]);
    const r = pearson(xs, ys);
    const p = r !== null ? calculatePValue(r, xs.length) : null;
    out[label] = { pearson_r: r, p_value: p };
  }
  return out;
}

export function useAnalysisData(symbol) {
  const [rows, setRows] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!symbol) return undefined;
    const controller = new AbortController();

    async function load() {
      setIsLoading(true);
      setError("");
      try {
        const response = await axios.get(
          `${API_BASE_URL}/research/metrics/${encodeURIComponent(symbol)}`,
          { signal: controller.signal, timeout: 30000 },
        );

        const payload = response.data;
        if (!Array.isArray(payload)) {
          setRows([]);
          setError(payload?.error || "No research metrics available.");
          return;
        }

        setRows(payload);
      } catch (err) {
        if (axios.isCancel(err) || err.name === "CanceledError") {
          return;
        }
        setRows([]);
        setError("Unable to load research metrics. Run the daily pipeline first.");
      } finally {
        setIsLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [symbol]);

  const analysisData = useMemo(() => {
    if (!rows.length) return null;
    const { event_study, usableCount } = buildEventStudy(rows);
    const correlation = buildCorrelation(rows);
    return {
      event_study,
      correlation,
      regression: null,
      data_points: usableCount,
    };
  }, [rows]);

  return { analysisData, isLoading, error };
}

