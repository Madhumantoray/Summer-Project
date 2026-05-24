"use client";

import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export function useStockData({ symbol, timeframe, startDate, endDate }) {
  const [state, setState] = useState({
    data: [],
    error: "",
    isLoading: true,
  });

  useEffect(() => {
    const controller = new AbortController();

    async function fetchStockData() {
      setState((current) => ({ ...current, error: "", isLoading: true }));

      try {
        const params = new URLSearchParams({ timeframe });

        if (startDate && endDate) {
          params.set("start", startDate);
          params.set("end", endDate);
        }

        const response = await axios.get(
          `${API_BASE_URL}/stock/${encodeURIComponent(symbol)}?${params.toString()}`,
          { signal: controller.signal, timeout: 12000 },
        );

        const payload = response.data;

        if (!Array.isArray(payload)) {
          setState({
            data: [],
            error: payload?.error || "No stock data found",
            isLoading: false,
          });
          return;
        }

        setState({
          data: payload,
          error: payload.length === 0 ? "No stock data found" : "",
          isLoading: false,
        });
      } catch (error) {
        if (axios.isCancel(error) || error.name === "CanceledError") {
          return;
        }

        setState({
          data: [],
          error: "Unable to load stock data. Confirm the backend is running.",
          isLoading: false,
        });
      }
    }

    fetchStockData();

    return () => controller.abort();
  }, [endDate, startDate, symbol, timeframe]);

  return state;
}
