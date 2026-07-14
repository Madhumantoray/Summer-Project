"use client";

import { useEffect, useMemo, useRef } from "react";
import { createChart } from "lightweight-charts";
import {
  buildCandleData,
  buildLineData,
  buildMacdData,
  buildRsiData,
  buildVolumeData,
  formatHoverData,
} from "../lib/marketData";
import { buildSentimentLineData } from "../lib/sentimentData";
import { chartTheme } from "../lib/theme";

const PRICE_HEIGHT = 620;
const RSI_HEIGHT = 178;
const MACD_HEIGHT = 232;

export default function ChartWorkspace({
  data,
  sentimentData,
  hoverData,
  isLineChart,
  isLoading,
  themeMode,
  onHoverData,
}) {
  const priceChartRef = useRef(null);
  const rsiChartRef = useRef(null);
  const macdChartRef = useRef(null);
  const activeTheme = chartTheme[themeMode];

  const derivedData = useMemo(
    () => ({
      candles: buildCandleData(data),
      line: buildLineData(data),
      volume: buildVolumeData(data),
      rsi: buildRsiData(data),
      macd: buildMacdData(data),
      sentiment: buildSentimentLineData(sentimentData),
    }),
    [data, sentimentData],
  );

  useEffect(() => {
    const priceElement = priceChartRef.current;
    const rsiElement = rsiChartRef.current;
    const macdElement = macdChartRef.current;

    if (!priceElement || !rsiElement || !macdElement || data.length === 0) {
      return undefined;
    }

    const commonOptions = {
      layout: {
        background: { color: activeTheme.background },
        textColor: activeTheme.text,
      },
      grid: {
        vertLines: { color: activeTheme.grid },
        horzLines: { color: activeTheme.grid },
      },
      rightPriceScale: {
        borderColor: activeTheme.border,
      },
      leftPriceScale: {
        visible: true,
        borderColor: activeTheme.border,
      },
      timeScale: {
        borderColor: activeTheme.border,
        timeVisible: true,
      },
      crosshair: {
        mode: 1,
      },
    };

    const priceChart = createChart(priceElement, {
      ...commonOptions,
      width: priceElement.clientWidth,
      height: PRICE_HEIGHT,
    });

    const mainSeries = isLineChart
      ? priceChart.addLineSeries({
          color: activeTheme.line,
          lineWidth: 2,
        })
      : priceChart.addCandlestickSeries({
          upColor: activeTheme.up,
          downColor: activeTheme.down,
          borderUpColor: activeTheme.up,
          borderDownColor: activeTheme.down,
          wickUpColor: activeTheme.up,
          wickDownColor: activeTheme.down,
        });

    if (isLineChart) {
      mainSeries.setData(derivedData.line);
    } else {
      mainSeries.setData(derivedData.candles);
    }

    const volumeSeries = priceChart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    priceChart.priceScale("volume").applyOptions({
      scaleMargins: {
        top: 0.82,
        bottom: 0,
      },
    });

    volumeSeries.setData(derivedData.volume);

    const sentimentSeries = priceChart.addLineSeries({
      color: activeTheme.sentiment,
      lineWidth: 2,
      priceScaleId: "left",
    });
    sentimentSeries.setData(derivedData.sentiment);

    priceChart.subscribeCrosshairMove((param) => {
      if (!param.time) {
        onHoverData(null);
        return;
      }

      let hoverTime = param.time;
      if (typeof hoverTime === "object" && hoverTime !== null) {
        const { year, month, day } = hoverTime;
        hoverTime = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      }

      const pointData = data.find((item) => item.Date === hoverTime || item.Date === param.time);
      onHoverData(pointData ? formatHoverData(pointData) : null);
    });

    const rsiChart = createChart(rsiElement, {
      ...commonOptions,
      width: rsiElement.clientWidth,
      height: RSI_HEIGHT,
    });

    const rsiSeries = rsiChart.addLineSeries({
      color: activeTheme.rsi,
      lineWidth: 2,
    });
    rsiSeries.setData(derivedData.rsi.values);

    const overbought = rsiChart.addLineSeries({
      color: activeTheme.overbought,
      lineWidth: 1,
    });
    overbought.setData(derivedData.rsi.overbought);

    const oversold = rsiChart.addLineSeries({
      color: activeTheme.oversold,
      lineWidth: 1,
    });
    oversold.setData(derivedData.rsi.oversold);

    const macdChart = createChart(macdElement, {
      ...commonOptions,
      width: macdElement.clientWidth,
      height: MACD_HEIGHT,
    });

    const macdSeries = macdChart.addLineSeries({
      color: activeTheme.macd,
      lineWidth: 2,
    });
    macdSeries.setData(derivedData.macd.values);

    const signalSeries = macdChart.addLineSeries({
      color: activeTheme.signal,
      lineWidth: 2,
    });
    signalSeries.setData(derivedData.macd.signal);

    const histSeries = macdChart.addHistogramSeries({
      priceFormat: { type: "price" },
    });
    histSeries.setData(derivedData.macd.histogram);

    priceChart.timeScale().fitContent();
    rsiChart.timeScale().fitContent();
    macdChart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      priceChart.applyOptions({ width: priceElement.clientWidth });
      rsiChart.applyOptions({ width: rsiElement.clientWidth });
      macdChart.applyOptions({ width: macdElement.clientWidth });
    });

    resizeObserver.observe(priceElement);
    resizeObserver.observe(rsiElement);
    resizeObserver.observe(macdElement);

    return () => {
      resizeObserver.disconnect();
      priceChart.remove();
      rsiChart.remove();
      macdChart.remove();
    };
  }, [activeTheme, data, derivedData, isLineChart, onHoverData]);

  return (
    <section className="flex flex-1 flex-col gap-3 pb-4">
      <HoverTape hoverData={hoverData} />

      <ChartPanel
        refTarget={priceChartRef}
        title={isLineChart ? "Close Price" : "Price Action"}
        caption="Volume overlay"
        heightClass="min-h-[420px] lg:min-h-[620px]"
        isLoading={isLoading}
      />
      <ChartPanel
        refTarget={rsiChartRef}
        title="RSI"
        caption="14 period"
        heightClass="min-h-[178px]"
        isLoading={isLoading}
      />
      <ChartPanel
        refTarget={macdChartRef}
        title="MACD"
        caption="Signal and histogram"
        heightClass="min-h-[232px]"
        isLoading={isLoading}
      />
    </section>
  );
}

function ChartPanel({ caption, heightClass, isLoading, refTarget, title }) {
  return (
    <div className="overflow-hidden rounded-lg border border-[var(--border-panel)] bg-[var(--surface-chart)] shadow-[var(--shadow-panel)] transition-colors duration-300">
      <div className="flex h-10 items-center justify-between border-b border-[var(--border-subtle)] px-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs uppercase tracking-[0.16em] text-[var(--text-secondary)]">
            {title}
          </span>
          <span className="text-xs text-[var(--text-muted)]">{caption}</span>
        </div>
        {isLoading && (
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-warning)]" />
        )}
      </div>
      <div ref={refTarget} className={`${heightClass} w-full`} />
    </div>
  );
}

function HoverTape({ hoverData }) {
  const cells = hoverData
    ? [
        ["O", hoverData.open, "text-[var(--text-primary)]"],
        ["H", hoverData.high, "text-[var(--accent-positive)]"],
        ["L", hoverData.low, "text-[var(--accent-negative)]"],
        ["C", hoverData.close, "text-[var(--accent-info)]"],
        ["VOL", Intl.NumberFormat().format(hoverData.volume), "text-[var(--accent-warning)]"],
      ]
    : [
        ["O", "-", "text-[var(--text-muted)]"],
        ["H", "-", "text-[var(--text-muted)]"],
        ["L", "-", "text-[var(--text-muted)]"],
        ["C", "-", "text-[var(--text-muted)]"],
        ["VOL", "-", "text-[var(--text-muted)]"],
      ];

  return (
    <div className="grid grid-cols-2 gap-2 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-raised)] px-3 py-2 font-mono text-xs transition-colors duration-300 sm:flex sm:flex-wrap sm:items-center sm:gap-5">
      {cells.map(([label, value, color]) => (
        <span key={label} className="flex items-center gap-2 text-[var(--text-muted)]">
          {label}
          <span className={color}>{value}</span>
        </span>
      ))}
    </div>
  );
}
