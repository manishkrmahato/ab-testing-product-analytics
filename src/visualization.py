"""
Publication-ready visualization module for experimentation reporting.

Generates high-resolution figures for conversion rates, confidence intervals,
daily trends, segment breakdowns, power curves, and Bayesian posteriors.
"""

import os
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from src.metrics import ExperimentMetrics
from src.bayesian_analysis import BayesianABResult


def set_plot_style():
    """Configures modern, clean, publication-ready Matplotlib parameters."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial"]
    plt.rcParams["axes.edgecolor"] = "#CCCCCC"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["grid.color"] = "#EEEEEE"
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.7


def plot_conversion_rates_with_ci(
    metrics: ExperimentMetrics,
    output_path: str = "reports/figures/01_conversion_rates_ci.png",
) -> None:
    """
    Plots conversion rates with 95% confidence intervals for Control and Treatment.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    groups = ["Control (Old Page)", "Treatment (New Page)"]
    rates = [metrics.cr_control * 100.0, metrics.cr_treatment * 100.0]
    errors = [1.96 * metrics.se_control * 100.0, 1.96 * metrics.se_treatment * 100.0]
    colors = ["#2B5B84", "#D95F02"]

    bars = ax.bar(groups, rates, yerr=errors, capsize=8, color=colors, alpha=0.88, width=0.45, edgecolor="#333333", linewidth=1)

    for bar, rate, err, n in zip(bars, rates, errors, [metrics.n_control, metrics.n_treatment]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate / 2,
            f"{rate:.2f}%\n(n = {n:,})",
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
            fontsize=12,
        )

    ax.set_ylabel("Conversion Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("A/B Test Primary Metric: Conversion Rate by Variant (95% CI)", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylim(0, 16.0)

    # Subtitle note on effect
    diff_text = f"Absolute Effect: {metrics.absolute_difference_pp:+.2f} pp | Relative Lift: {metrics.relative_lift_pct:+.2f}%\nTwo-Proportion Z = -1.311 (p = 0.1899, Not Statistically Significant)"
    ax.text(
        0.5, 0.92,
        diff_text,
        transform=ax.transAxes,
        ha="center",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8F9FA", edgecolor="#CCCCCC", alpha=0.9),
    )

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def plot_daily_and_cumulative_trends(
    clean_df: pd.DataFrame,
    output_path: str = "reports/figures/02_daily_and_cumulative_trends.png",
) -> None:
    """
    Plots daily conversion rates and cumulative conversion rates to detect temporal volatility or novelty effects.
    """
    set_plot_style()
    df = clean_df.copy()
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    # Daily aggregation
    daily = df.groupby(["date", "group"], observed=False).agg(
        visitors=("converted", "count"),
        conversions=("converted", "sum"),
    ).reset_index()
    daily["daily_cr"] = daily["conversions"] / daily["visitors"]

    # Cumulative aggregation
    daily.sort_values(by=["group", "date"], inplace=True)
    daily["cum_visitors"] = daily.groupby("group", observed=False)["visitors"].cumsum()
    daily["cum_conversions"] = daily.groupby("group", observed=False)["conversions"].cumsum()
    daily["cum_cr"] = daily["cum_conversions"] / daily["cum_visitors"]

    ctrl_daily = daily[daily["group"] == "control"]
    treat_daily = daily[daily["group"] == "treatment"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), dpi=300, sharex=True)

    # Top plot: Daily Conversion Rates
    ax1.plot(ctrl_daily["date"], ctrl_daily["daily_cr"] * 100, marker="o", markersize=4, color="#2B5B84", label="Control (Old Page)", linewidth=1.8)
    ax1.plot(treat_daily["date"], treat_daily["daily_cr"] * 100, marker="s", markersize=4, color="#D95F02", label="Treatment (New Page)", linewidth=1.8)
    ax1.set_ylabel("Daily CR (%)", fontsize=11, fontweight="bold")
    ax1.set_title("Temporal Stability & Novelty Effect Check: Daily vs. Cumulative Conversion Rates", fontsize=14, fontweight="bold", pad=12)
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Bottom plot: Cumulative Conversion Rates
    ax2.plot(ctrl_daily["date"], ctrl_daily["cum_cr"] * 100, color="#2B5B84", label="Cumulative Control CR", linewidth=2.5)
    ax2.plot(treat_daily["date"], treat_daily["cum_cr"] * 100, color="#D95F02", label="Cumulative Treatment CR", linewidth=2.5)
    ax2.set_ylabel("Cumulative CR (%)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Date (January 2017)", fontsize=11, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    # Rotate x labels
    plt.xticks(rotation=45)
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def plot_country_segment_breakdown(
    merged_df: pd.DataFrame,
    output_path: str = "reports/figures/03_country_segment_breakdown.png",
) -> None:
    """
    Plots country-level conversion rates comparing control vs treatment.
    """
    set_plot_style()
    seg = merged_df.groupby(["country", "group"], observed=False).agg(
        visitors=("converted", "count"),
        conversions=("converted", "sum"),
    ).reset_index()
    seg["cr_pct"] = (seg["conversions"] / seg["visitors"]) * 100.0

    countries = ["CA", "UK", "US"]
    ctrl_rates = [seg[(seg["country"] == c) & (seg["group"] == "control")]["cr_pct"].values[0] for c in countries]
    treat_rates = [seg[(seg["country"] == c) & (seg["group"] == "treatment")]["cr_pct"].values[0] for c in countries]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    x = np.arange(len(countries))
    width = 0.35

    rects1 = ax.bar(x - width/2, ctrl_rates, width, label="Control (Old Page)", color="#2B5B84", alpha=0.88, edgecolor="#333333")
    rects2 = ax.bar(x + width/2, treat_rates, width, label="Treatment (New Page)", color="#D95F02", alpha=0.88, edgecolor="#333333")

    ax.set_ylabel("Conversion Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Heterogeneous Treatment Effect: Conversion Rate by Country", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(["Canada (CA)", "United Kingdom (UK)", "United States (US)"], fontsize=11)
    ax.legend(loc="lower right", frameon=True)
    ax.set_ylim(0, 16.0)

    for rect in list(rects1) + list(rects2):
        height = rect.get_height()
        ax.annotate(f"{height:.2f}%",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def plot_power_and_mde_curve(
    power_df: pd.DataFrame,
    mde_pct: float,
    output_path: str = "reports/figures/04_power_curve.png",
) -> None:
    """
    Plots statistical power vs relative lift, highlighting the 80% power threshold and MDE.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    ax.plot(power_df["relative_lift_pct"], power_df["power"] * 100, color="#1B9E77", linewidth=2.5, label="Power Curve (n = 145,274 / group)")
    ax.axhline(80.0, color="#E7298A", linestyle="--", linewidth=1.5, label="Target Power (80%)")
    ax.axvline(mde_pct, color="#7570B3", linestyle=":", linewidth=2, label=f"MDE = {mde_pct:.2f}% (0.34 pp)")

    ax.set_xlabel("Relative Lift in Conversion Rate (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Statistical Power (%)", fontsize=12, fontweight="bold")
    ax.set_title("Prospective Power Analysis & Minimum Detectable Effect (MDE)", fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="lower right", frameon=True)
    ax.set_ylim(0, 105.0)
    ax.set_xlim(power_df["relative_lift_pct"].min(), power_df["relative_lift_pct"].max())

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def plot_bayesian_posterior_distributions(
    samples_ctrl: np.ndarray,
    samples_treat: np.ndarray,
    diff_samples: np.ndarray,
    bayes_res: BayesianABResult,
    output_path: str = "reports/figures/05_bayesian_posterior.png",
) -> None:
    """
    Plots Bayesian posterior distributions and the posterior difference distribution.
    """
    set_plot_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Left: Posterior densities for p_control and p_treatment
    ax1.hist(samples_ctrl * 100, bins=80, density=True, alpha=0.6, color="#2B5B84", label=f"Control Posterior (mean={bayes_res.posterior_mean_ctrl*100:.2f}%)")
    ax1.hist(samples_treat * 100, bins=80, density=True, alpha=0.6, color="#D95F02", label=f"Treatment Posterior (mean={bayes_res.posterior_mean_treat*100:.2f}%)")
    ax1.set_xlabel("Conversion Rate (%)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Posterior Probability Density", fontsize=11, fontweight="bold")
    ax1.set_title("Posterior Distributions P(θ | Data)", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right", frameon=True)

    # Right: Difference (Treatment - Control)
    diff_pp = diff_samples * 100.0
    n, bins, patches = ax2.hist(diff_pp, bins=80, density=True, alpha=0.7, color="#7570B3")

    # Color negative difference in red, positive in green
    for b_left, patch in zip(bins[:-1], patches):
        if b_left < 0:
            patch.set_facecolor("#D95F02")
        else:
            patch.set_facecolor("#1B9E77")

    ax2.axvline(0, color="black", linestyle="--", linewidth=1.5, label="Zero Effect Threshold")
    ax2.axvline(bayes_res.credible_interval_95_lower_pp, color="#333333", linestyle=":", linewidth=1.5, label=f"95% HDI: [{bayes_res.credible_interval_95_lower_pp:.2f}%, {bayes_res.credible_interval_95_upper_pp:.2f}%]")
    ax2.axvline(bayes_res.credible_interval_95_upper_pp, color="#333333", linestyle=":", linewidth=1.5)

    ax2.set_xlabel("Difference in Conversion Rate (Treatment - Control, pp)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Posterior Probability Density", fontsize=11, fontweight="bold")
    ax2.set_title(f"Posterior Difference: P(Treatment > Control) = {bayes_res.prob_treatment_beats_control*100:.1f}%", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def plot_sensitivity_comparison(
    sens_df: pd.DataFrame,
    output_path: str = "reports/figures/06_sensitivity_analysis.png",
) -> None:
    """
    Plots treatment effect comparison across the 4 candidate analytical specifications.
    """
    set_plot_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    specs = sens_df["Specification"].tolist()
    y_pos = np.arange(len(specs))

    # Left: Difference in percentage points
    diffs = sens_df["Diff_Percentage_Points"].tolist()
    colors = ["#D95F02" if d < 0 else "#1B9E77" for d in diffs]
    bars = ax1.barh(y_pos, diffs, color=colors, alpha=0.85, height=0.45, edgecolor="#333333")
    ax1.axvline(0, color="black", linestyle="--", linewidth=1.2)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(specs, fontsize=11, fontweight="bold")
    ax1.set_xlabel("Difference in Conversion Rate (Treatment - Control, pp)", fontsize=11, fontweight="bold")
    ax1.set_title("Treatment Effect Across Analytical Specifications", fontsize=13, fontweight="bold")
    ax1.set_xlim(-0.25, 0.05)

    for bar, d in zip(bars, diffs):
        ax1.text(d - 0.01 if d < 0 else d + 0.005, bar.get_y() + bar.get_height() / 2, f"{d:+.2f} pp",
                 va="center", ha="right" if d < 0 else "left", fontsize=10, fontweight="bold")

    # Right: P-values
    p_vals = sens_df["P_Value"].tolist()
    bars2 = ax2.barh(y_pos, p_vals, color="#2B5B84", alpha=0.85, height=0.45, edgecolor="#333333")
    ax2.axvline(0.05, color="#E7298A", linestyle="--", linewidth=1.5, label="Alpha = 0.05 Threshold")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([""] * len(specs))
    ax2.set_xlabel("Two-Sided P-Value", fontsize=11, fontweight="bold")
    ax2.set_title("Hypothesis Test P-Value by Specification", fontsize=13, fontweight="bold")
    ax2.set_xlim(0, 0.35)
    ax2.legend(loc="upper right", frameon=True)

    for bar, p in zip(bars2, p_vals):
        ax2.text(p + 0.01, bar.get_y() + bar.get_height() / 2, f"p = {p:.4f}",
                 va="center", ha="left", fontsize=10, fontweight="bold")

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

