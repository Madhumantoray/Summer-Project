"use client";

import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export function useSentimentData(symbol, enabled = true) {
  const [state, setState] = useState({
    data: [],
    error: "",
    isLoading: false,
  });

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const controller = new AbortController();

    async function fetchSentimentData() {
      setState((current) => ({ ...current, error: "", isLoading: true }));

      try {
        const response = await axios.get(
          `${API_BASE_URL}/sentiment/${encodeURIComponent(symbol)}`,
          { signal: controller.signal, timeout: 180000 },
        );

        const payload = response.data;

        if (!Array.isArray(payload)) {
          setState({
            data: [],
            error: payload?.error || "No news available",
            isLoading: false,
          });
          return;
        }

        setState({
          data: payload,
          error: "",
          isLoading: false,
        });
      } catch (error) {
        if (axios.isCancel(error) || error.name === "CanceledError") {
          return;
        }

        setState({
          data: [],
          error: "Unable to load sentiment data.",
          isLoading: false,
        });
      }
    }

    fetchSentimentData();

    return () => controller.abort();
  }, [enabled, symbol]);

  return state;
}
