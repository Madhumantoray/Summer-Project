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
# # Event Study — Sentiment Extremes & Stock Returns
#
# This notebook tests the core behavioural finance hypothesis:
#
# > **Do days with strongly negative financial sentiment precede
# > mean-reverting positive returns?**
#
# **Methodology:**
# 1. Classify each sentiment day into Strong Negative, Neutral, or Strong Positive
# 2. Compare subsequent returns across groups
# 3. Compute cumulative abnormal returns (CAR) over event windows
# 4. Perform statistical tests for significance

# %% [markdown]
# ## 1. Setup & Data Loading

# %%
import sys
from pathlib import Path

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

from scipy import stats as scipy_stats

try:
    import statsmodels.api as sm
    from statsmodels.stats.weightstats import ttest_ind
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("statsmodels not installed — some tests will be skipped")

from database.database import get_db
from database.models import ResearchMetric

# %%
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

print(f"Loaded {len(df)} observations")
df.head()

# %% [markdown]
# ## 2. Event Classification
#
# | Group | Condition |
# |-------|-----------|
# | Strong Negative | sentiment < −0.7 |
# | Neutral | −0.2 ≤ sentiment ≤ 0.2 |
# | Strong Positive | sentiment > 0.7 |

# %%
THRESHOLDS = {
    "Strong Negative": lambda s: s < -0.7,
    "Neutral": lambda s: (-0.2 <= s) & (s <= 0.2),
    "Strong Positive": lambda s: s > 0.7,
}

def classify_sentiment(score):
    if score < -0.7:
        return "Strong Negative"
    elif score > 0.7:
        return "Strong Positive"
    elif -0.2 <= score <= 0.2:
        return "Neutral"
    else:
        return "Other"

df["sentiment_group"] = df["sentiment_score"].apply(classify_sentiment)
group_counts = df["sentiment_group"].value_counts()
print("=== Event Group Counts ===")
print(group_counts)
print()

# Filter to the three research groups
research_groups = ["Strong Negative", "Neutral", "Strong Positive"]
df_groups = df[df["sentiment_group"].isin(research_groups)].copy()
print(f"Using {len(df_groups)} observations across {len(research_groups)} groups")

# %% [markdown]
# ## 3. Group Statistics

# %%
return_cols = [
    "future_return_1d", "future_return_3d",
    "future_return_7d", "future_return_30d",
    "abnormal_return_1d", "abnormal_return_7d",
]

# Mean returns by group
print("=== Mean Future Returns by Sentiment Group ===\n")
group_means = df_groups.groupby("sentiment_group")[return_cols].mean()
print(group_means.round(4).to_string())
print()

# Volatility (std) by group
print("=== Return Volatility (Std Dev) by Sentiment Group ===\n")
group_std = df_groups.groupby("sentiment_group")[return_cols].std()
print(group_std.round(4).to_string())
print()

# Observation counts
print("=== Observations per Group ===\n")
group_n = df_groups.groupby("sentiment_group")[return_cols].count()
print(group_n.to_string())

# %% [markdown]
# ## 4. Box Plots — Returns by Sentiment Group

# %%
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
colors = {
    "Strong Negative": "#F44336",
    "Neutral": "#FFC107",
    "Strong Positive": "#4CAF50",
}

for ax, col, title in zip(
    axes.flat,
    ["future_return_1d", "future_return_3d", "future_return_7d", "future_return_30d"],
    ["1-Day Return", "3-Day Return", "7-Day Return", "30-Day Return"],
):
    data_by_group = []
    labels = []
    box_colors = []
    for group in research_groups:
        subset = df_groups[df_groups["sentiment_group"] == group][col].dropna()
        if len(subset) > 0:
            data_by_group.append(subset.values)
            labels.append(f"{group}\n(n={len(subset)})")
            box_colors.append(colors[group])

    if data_by_group:
        bp = ax.boxplot(data_by_group, labels=labels, patch_artist=True, widths=0.6)
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

    ax.set_title(f"{title} by Sentiment Group", fontsize=12)
    ax.set_ylabel("Return")
    ax.axhline(0, color="black", linestyle="--", alpha=0.5)
    ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("boxplot_returns_by_group.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 5. Mean Return Comparison Chart

# %%
fig, ax = plt.subplots(figsize=(12, 6))

x = np.arange(len(return_cols))
width = 0.25

for i, group in enumerate(research_groups):
    means = []
    errors = []
    for col in return_cols:
        subset = df_groups[df_groups["sentiment_group"] == group][col].dropna()
        means.append(subset.mean() if len(subset) > 0 else 0)
        errors.append(subset.std() / np.sqrt(len(subset)) if len(subset) > 1 else 0)

    ax.bar(
        x + i * width, means, width,
        label=group, color=colors[group], alpha=0.7,
        yerr=errors, capsize=4,
    )

ax.set_xlabel("Return Window")
ax.set_ylabel("Mean Return")
ax.set_title("Mean Returns by Sentiment Group (with Standard Error)", fontsize=14)
ax.set_xticks(x + width)
labels = [c.replace("future_return_", "").replace("abnormal_return_", "abn_") for c in return_cols]
ax.set_xticklabels(labels)
ax.legend()
ax.axhline(0, color="black", linestyle="--", alpha=0.5)
ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("mean_return_comparison.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 6. Statistical Testing
#
# **Hypothesis test:**
# > H₀: Mean future return after negative sentiment = Mean future return after positive sentiment
# > H₁: They are different (two-tailed)
#
# We use Welch's t-test (unequal variances) and report p-values
# with 95% confidence intervals.

# %%
print("=" * 70)
print("STATISTICAL TESTS: Strong Negative vs Strong Positive")
print("=" * 70)
print()

neg = df_groups[df_groups["sentiment_group"] == "Strong Negative"]
pos = df_groups[df_groups["sentiment_group"] == "Strong Positive"]

test_results = []

for col in return_cols:
    neg_returns = neg[col].dropna()
    pos_returns = pos[col].dropna()

    if len(neg_returns) < 2 or len(pos_returns) < 2:
        print(f"  {col}: insufficient data (neg={len(neg_returns)}, pos={len(pos_returns)})")
        continue

    # Welch's t-test (does not assume equal variances)
    t_stat, p_value = scipy_stats.ttest_ind(neg_returns, pos_returns, equal_var=False)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(
        (neg_returns.std() ** 2 + pos_returns.std() ** 2) / 2
    )
    cohens_d = (neg_returns.mean() - pos_returns.mean()) / pooled_std if pooled_std > 0 else 0

    # Confidence interval for the difference in means
    diff_mean = neg_returns.mean() - pos_returns.mean()
    se_diff = np.sqrt(neg_returns.var() / len(neg_returns) + pos_returns.var() / len(pos_returns))
    ci_lower = diff_mean - 1.96 * se_diff
    ci_upper = diff_mean + 1.96 * se_diff

    sig = "***" if p_value < 0.01 else "**" if p_value < 0.05 else "*" if p_value < 0.10 else ""

    result = {
        "Return Window": col,
        "Neg Mean": round(neg_returns.mean(), 4),
        "Pos Mean": round(pos_returns.mean(), 4),
        "Diff": round(diff_mean, 4),
        "t-stat": round(t_stat, 3),
        "p-value": round(p_value, 4),
        "Cohen's d": round(cohens_d, 3),
        "95% CI": f"[{ci_lower:.4f}, {ci_upper:.4f}]",
        "Sig": sig,
    }
    test_results.append(result)

    print(f"  {col}:")
    print(f"    Neg mean = {neg_returns.mean():+.4f}  (n={len(neg_returns)})")
    print(f"    Pos mean = {pos_returns.mean():+.4f}  (n={len(pos_returns)})")
    print(f"    Diff     = {diff_mean:+.4f}")
    print(f"    t        = {t_stat:.3f}")
    print(f"    p        = {p_value:.4f}  {sig}")
    print(f"    Cohen's d= {cohens_d:.3f}")
    print(f"    95% CI   = [{ci_lower:.4f}, {ci_upper:.4f}]")
    print()

test_df = pd.DataFrame(test_results)
test_df

# %% [markdown]
# ## 7. Cumulative Abnormal Returns (CAR)

# %%
# Compute CAR for each group over windows [0, 1, 3, 7, 30]
windows = [0, 1, 3, 7, 30]
return_map = {
    0: None,  # baseline
    1: "future_return_1d",
    3: "future_return_3d",
    7: "future_return_7d",
    30: "future_return_30d",
}

fig, ax = plt.subplots(figsize=(12, 6))

for group in research_groups:
    group_df = df_groups[df_groups["sentiment_group"] == group]
    car_values = [0]  # starts at 0 on event day

    for w in windows[1:]:
        col = return_map[w]
        mean_return = group_df[col].dropna().mean() if col else 0
        car_values.append(mean_return if not np.isnan(mean_return) else 0)

    ax.plot(
        windows, car_values,
        marker="o", linewidth=2, markersize=8,
        label=group, color=colors[group],
    )

ax.set_xlabel("Trading Days After Event", fontsize=12)
ax.set_ylabel("Cumulative Return", fontsize=12)
ax.set_title("Cumulative Returns by Sentiment Group", fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
ax.axhline(0, color="black", linestyle="--", alpha=0.5)
ax.set_xticks(windows)

plt.tight_layout()
plt.savefig("cumulative_returns.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 8. Abnormal Return Analysis

# %%
# Cumulative Abnormal Returns (market-adjusted)
fig, ax = plt.subplots(figsize=(12, 6))

abn_map = {1: "abnormal_return_1d", 7: "abnormal_return_7d"}
abn_windows = [0, 1, 7]

for group in research_groups:
    group_df = df_groups[df_groups["sentiment_group"] == group]
    car_values = [0]

    for w in abn_windows[1:]:
        col = abn_map.get(w)
        if col:
            mean_abn = group_df[col].dropna().mean()
            car_values.append(mean_abn if not np.isnan(mean_abn) else 0)
        else:
            car_values.append(0)

    ax.plot(
        abn_windows, car_values,
        marker="s", linewidth=2, markersize=8,
        label=group, color=colors[group],
    )

ax.set_xlabel("Trading Days After Event", fontsize=12)
ax.set_ylabel("Cumulative Abnormal Return", fontsize=12)
ax.set_title("Cumulative Abnormal Returns (Market-Adjusted)", fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
ax.axhline(0, color="black", linestyle="--", alpha=0.5)
ax.set_xticks(abn_windows)

plt.tight_layout()
plt.savefig("cumulative_abnormal_returns.png", bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 9. Additional Statistical Tests

# %%
if HAS_STATSMODELS:
    print("=" * 70)
    print("ADDITIONAL TESTS (statsmodels)")
    print("=" * 70)

    for col in ["future_return_7d", "abnormal_return_7d"]:
        neg_data = neg[col].dropna()
        pos_data = pos[col].dropna()

        if len(neg_data) < 2 or len(pos_data) < 2:
            continue

        # Welch's t-test via statsmodels (provides CI directly)
        t_stat, p_value, dof = ttest_ind(neg_data, pos_data, usevar="unequal")

        print(f"\n  {col}:")
        print(f"    Welch t-test: t={t_stat:.3f}, p={p_value:.4f}, df={dof:.1f}")

        # Mann-Whitney U test (non-parametric alternative)
        u_stat, u_p = scipy_stats.mannwhitneyu(neg_data, pos_data, alternative="two-sided")
        print(f"    Mann-Whitney U: U={u_stat:.1f}, p={u_p:.4f}")
else:
    print("statsmodels not available — skipping additional tests")

# %% [markdown]
# ## 10. Summary
#
# ### Key Research Question
# > Do negative sentiment days significantly outperform positive sentiment days?
#
# ### Findings
# - Group means, volatilities, and statistical tests are reported above
# - Box plots show the distribution of returns by sentiment group
# - CAR plots show cumulative performance after sentiment events
# - t-tests and confidence intervals quantify significance
#
# ### Interpretation Notes
# - **Small sample caveat**: With limited headline data (Google News RSS),
#   results should be treated as preliminary
# - **Multiple testing**: When testing multiple return windows,
#   consider Bonferroni correction (divide α by number of tests)
# - **Look-ahead bias**: All returns are computed using future prices only
# - **After-market handling**: News after 15:30 IST is attributed to
#   the next trading day
