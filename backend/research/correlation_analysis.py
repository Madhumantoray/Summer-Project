# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Correlation Analysis — Sentiment vs Future Returns
#
# This notebook analyses the relationship between FinBERT sentiment
# scores and subsequent stock returns for NSE equities.
#
# **Research question:** Does daily news sentiment have predictive
# power for short-term stock returns?
#
# **Methodology:**
# - Load research metrics from SQLite
# - Compute Pearson and Spearman correlations
# - Visualise sentiment–return relationships
# - Break down by symbol and return horizon

# %% [markdown]
# ## 1. Setup & Data Loading

# %%
import sys
from pathlib import Path

# Ensure backend is on path
BACKEND_DIR = str(Path().resolve().parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["figure.figsize"] = (12, 6)
matplotlib.rcParams["figure.dpi"] = 100

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("plotly not installed — falling back to matplotlib only")

from scipy import stats as scipy_stats
from database.database import get_db, engine
from database.models import ResearchMetric, NewsSentiment, StockPrice

# %%
# Load research metrics
with get_db() as db:
    metrics = db.query(ResearchMetric).all()

df = pd.DataFrame([{
    "symbol": m.symbol,
    "date": m.date,
    "sentiment_score": m.sentiment_score,
    "future_return_1d": m.future_return_1d,
    "future_return_3d": m.future_return_3d,
    "future_return_7d": m.future_return_7d,
    "future_return_30d": m.future_return_30d,
    "abnormal_return_1d": m.abnormal_return_1d,
    "abnormal_return_7d": m.abnormal_return_7d,
} for m in metrics])

print(f"Loaded {len(df)} research metric records")
print(f"Symbols: {df['symbol'].unique().tolist()}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
df.head()

# %% [markdown]
# ## 2. Descriptive Statistics

# %%
# Summary statistics for sentiment and returns
desc_cols = [
    "sentiment_score",
    "future_return_1d", "future_return_3d",
    "future_return_7d", "future_return_30d",
    "abnormal_return_1d", "abnormal_return_7d",
]
print("=== Descriptive Statistics ===")
df[desc_cols].describe().round(4)

# %%
# Distribution of sentiment scores
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(df["sentiment_score"].dropna(), bins=50, edgecolor="black", alpha=0.7, color="#2196F3")
axes[0].set_title("Distribution of Daily Sentiment Scores")
axes[0].set_xlabel("Sentiment Score")
axes[0].set_ylabel("Frequency")
axes[0].axvline(0, color="red", linestyle="--", alpha=0.7)

axes[1].hist(df["future_return_7d"].dropna(), bins=50, edgecolor="black", alpha=0.7, color="#4CAF50")
axes[1].set_title("Distribution of 7-Day Future Returns")
axes[1].set_xlabel("Return")
axes[1].set_ylabel("Frequency")
axes[1].axvline(0, color="red", linestyle="--", alpha=0.7)

plt.tight_layout()
plt.savefig("sentiment_distribution.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 3. Pearson Correlation

# %%
# Pearson correlation: sentiment vs all return windows
return_cols = [
    "future_return_1d", "future_return_3d",
    "future_return_7d", "future_return_30d",
    "abnormal_return_1d", "abnormal_return_7d",
]

print("=== Pearson Correlation: Sentiment vs Returns ===\n")
pearson_results = []
for col in return_cols:
    valid = df[["sentiment_score", col]].dropna()
    if len(valid) < 3:
        continue
    r, p = scipy_stats.pearsonr(valid["sentiment_score"], valid[col])
    sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
    pearson_results.append({
        "Return Window": col,
        "Pearson r": round(r, 4),
        "p-value": round(p, 4),
        "Significance": sig,
        "N": len(valid),
    })
    print(f"  {col:25s}  r={r:+.4f}  p={p:.4f}  N={len(valid)}  {sig}")

pearson_df = pd.DataFrame(pearson_results)
pearson_df

# %% [markdown]
# ## 4. Spearman Rank Correlation

# %%
# Spearman correlation (more robust to outliers and non-linearity)
print("=== Spearman Rank Correlation: Sentiment vs Returns ===\n")
spearman_results = []
for col in return_cols:
    valid = df[["sentiment_score", col]].dropna()
    if len(valid) < 3:
        continue
    rho, p = scipy_stats.spearmanr(valid["sentiment_score"], valid[col])
    sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
    spearman_results.append({
        "Return Window": col,
        "Spearman ρ": round(rho, 4),
        "p-value": round(p, 4),
        "Significance": sig,
        "N": len(valid),
    })
    print(f"  {col:25s}  ρ={rho:+.4f}  p={p:.4f}  N={len(valid)}  {sig}")

spearman_df = pd.DataFrame(spearman_results)
spearman_df

# %% [markdown]
# ## 5. Correlation Heatmap

# %%
# Full correlation heatmap across all numeric columns
corr_cols = ["sentiment_score"] + return_cols
corr_matrix = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr_matrix, cmap="RdYlGn", aspect="auto", vmin=-1, vmax=1)

ax.set_xticks(range(len(corr_cols)))
ax.set_yticks(range(len(corr_cols)))
labels = [c.replace("future_return_", "ret_").replace("abnormal_return_", "abn_") for c in corr_cols]
ax.set_xticklabels(labels, rotation=45, ha="right")
ax.set_yticklabels(labels)

# Annotate with values
for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        val = corr_matrix.iloc[i, j]
        ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                color="black" if abs(val) < 0.5 else "white", fontsize=9)

fig.colorbar(im, ax=ax, shrink=0.8)
ax.set_title("Correlation Heatmap: Sentiment & Returns", fontsize=14)
plt.tight_layout()
plt.savefig("correlation_heatmap.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 6. Scatter Plots — Sentiment vs Future Returns

# %%
# Scatter: sentiment_score vs future_return_7d, colored by symbol
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

for ax, col, title in zip(
    axes.flat,
    ["future_return_1d", "future_return_3d", "future_return_7d", "future_return_30d"],
    ["1-Day Return", "3-Day Return", "7-Day Return", "30-Day Return"],
):
    valid = df[["sentiment_score", col, "symbol"]].dropna()
    for symbol in valid["symbol"].unique():
        subset = valid[valid["symbol"] == symbol]
        ax.scatter(
            subset["sentiment_score"], subset[col],
            alpha=0.5, s=30, label=symbol.replace(".NS", ""),
        )

    # Add regression line
    all_valid = valid[["sentiment_score", col]].dropna()
    if len(all_valid) > 2:
        z = np.polyfit(all_valid["sentiment_score"], all_valid[col], 1)
        p = np.poly1d(z)
        x_line = np.linspace(all_valid["sentiment_score"].min(), all_valid["sentiment_score"].max(), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.7, linewidth=2)

    ax.set_xlabel("Sentiment Score")
    ax.set_ylabel(title)
    ax.set_title(f"Sentiment vs {title}")
    ax.axhline(0, color="gray", linestyle=":", alpha=0.5)
    ax.axvline(0, color="gray", linestyle=":", alpha=0.5)
    ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig("scatter_sentiment_returns.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 7. Rolling Sentiment Chart

# %%
# 30-day rolling average sentiment per symbol
fig, ax = plt.subplots(figsize=(14, 6))

for symbol in df["symbol"].unique():
    sym_df = df[df["symbol"] == symbol].sort_values("date").copy()
    sym_df["rolling_30d"] = sym_df["sentiment_score"].rolling(30, min_periods=5).mean()
    ax.plot(
        sym_df["date"], sym_df["rolling_30d"],
        label=symbol.replace(".NS", ""), linewidth=1.5,
    )

ax.set_title("30-Day Rolling Average Sentiment Score", fontsize=14)
ax.set_xlabel("Date")
ax.set_ylabel("Sentiment Score")
ax.axhline(0, color="red", linestyle="--", alpha=0.5)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("rolling_sentiment.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 8. Return Distributions by Sentiment Tercile

# %%
# Split sentiment into terciles and compare return distributions
df_valid = df[["sentiment_score", "future_return_7d"]].dropna()

if len(df_valid) >= 9:
    df_valid["sentiment_tercile"] = pd.qcut(
        df_valid["sentiment_score"], q=3,
        labels=["Negative", "Neutral", "Positive"],
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {"Negative": "#F44336", "Neutral": "#FFC107", "Positive": "#4CAF50"}

    for tercile in ["Negative", "Neutral", "Positive"]:
        subset = df_valid[df_valid["sentiment_tercile"] == tercile]["future_return_7d"]
        ax.hist(
            subset, bins=30, alpha=0.5, label=f"{tercile} (n={len(subset)})",
            color=colors[tercile], edgecolor="black",
        )

    ax.set_title("7-Day Return Distribution by Sentiment Tercile", fontsize=14)
    ax.set_xlabel("7-Day Future Return")
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.axvline(0, color="black", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("return_distribution_terciles.png", bbox_inches="tight")
    plt.show()
else:
    print("Not enough data for tercile analysis")

# %% [markdown]
# ## 9. Per-Symbol Correlation Summary

# %%
# Correlation breakdown by symbol
print("=== Per-Symbol Pearson Correlation: Sentiment vs 7-Day Return ===\n")
per_symbol = []
for symbol in df["symbol"].unique():
    sym_df = df[df["symbol"] == symbol][["sentiment_score", "future_return_7d"]].dropna()
    if len(sym_df) < 3:
        continue
    r, p = scipy_stats.pearsonr(sym_df["sentiment_score"], sym_df["future_return_7d"])
    per_symbol.append({
        "Symbol": symbol.replace(".NS", ""),
        "N": len(sym_df),
        "Pearson r": round(r, 4),
        "p-value": round(p, 4),
    })

per_symbol_df = pd.DataFrame(per_symbol)
print(per_symbol_df.to_string(index=False))
per_symbol_df

# %% [markdown]
# ## 10. Summary
#
# Key findings from correlation analysis:
# - Pearson and Spearman correlations between sentiment and future returns
# - Visual inspection of sentiment–return relationships
# - Per-symbol breakdown to identify heterogeneous effects
#
# **Next step:** Event study analysis to test whether extreme sentiment
# days produce statistically different returns.
