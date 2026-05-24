"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "stock-research-theme";

function getInitialTheme() {
  if (typeof window === "undefined") {
    return "dark";
  }

  const savedTheme = window.localStorage.getItem(STORAGE_KEY);
  if (savedTheme === "dark" || savedTheme === "light") {
    return savedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function useThemeMode() {
  const [themeMode, setThemeMode] = useState("dark");

  useEffect(() => {
    const frameId = window.requestAnimationFrame(() => {
      setThemeMode(getInitialTheme());
    });

    return () => window.cancelAnimationFrame(frameId);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", themeMode === "dark");
    document.documentElement.dataset.theme = themeMode;
    window.localStorage.setItem(STORAGE_KEY, themeMode);
  }, [themeMode]);

  return {
    themeMode,
    toggleTheme: () => {
      setThemeMode((current) => (current === "dark" ? "light" : "dark"));
    },
  };
}
