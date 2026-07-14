export function calculateReturns(data) {
  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  const firstClose = Number(data[0].Close);
  const lastClose = Number(data[data.length - 1].Close);
  const change = lastClose - firstClose;
  const percentReturn = (change / firstClose) * 100;

  return {
    percent: percentReturn.toFixed(2),
    change: change.toFixed(2),
    first: firstClose.toFixed(2),
    last: lastClose.toFixed(2),
  };
}

export function buildCandleData(data) {
  return data.map((item) => ({
    time: item.Date,
    open: Number(item.Open),
    high: Number(item.High),
    low: Number(item.Low),
    close: Number(item.Close),
  }));
}

export function buildLineData(data) {
  return data.map((item) => ({
    time: item.Date,
    value: Number(item.Close),
  }));
}

export function buildVolumeData(data) {
  return data.map((item) => ({
    time: item.Date,
    value: Number(item.Volume),
    color:
      Number(item.Close) >= Number(item.Open)
        ? "rgba(32, 178, 142, 0.34)"
        : "rgba(207, 74, 74, 0.34)",
  }));
}

export function buildRsiData(data) {
  const startIndex = data.findIndex((item) => Number(item.RSI) !== 0);
  const validData = startIndex === -1 ? [] : data.slice(startIndex);
  return {
    values: validData.map((item) => ({
      time: item.Date,
      value: Number(item.RSI),
    })),
    overbought: data.map((item) => ({
      time: item.Date,
      value: 70,
    })),
    oversold: data.map((item) => ({
      time: item.Date,
      value: 30,
    })),
  };
}

export function buildMacdData(data) {
  const startIndex = data.findIndex(
    (item) => Number(item.MACD) !== 0 || Number(item.MACD_SIGNAL) !== 0
  );
  const validData = startIndex === -1 ? [] : data.slice(startIndex);
  return {
    values: validData.map((item) => ({
      time: item.Date,
      value: Number(item.MACD),
    })),
    signal: validData.map((item) => ({
      time: item.Date,
      value: Number(item.MACD_SIGNAL),
    })),
    histogram: validData.map((item) => ({
      time: item.Date,
      value: Number(item.MACD_DIFF),
      color:
        Number(item.MACD_DIFF) >= 0
          ? "rgba(32, 178, 142, 0.48)"
          : "rgba(207, 74, 74, 0.48)",
    })),
  };
}

export function formatHoverData(item) {
  return {
    open: Number(item.Open).toFixed(2),
    high: Number(item.High).toFixed(2),
    low: Number(item.Low).toFixed(2),
    close: Number(item.Close).toFixed(2),
    volume: Number(item.Volume),
  };
}
