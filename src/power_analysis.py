"""
Sample size, statistical power, and Minimum Detectable Effect (MDE) module.

Implements mathematically rigorous power and sample size calculations for two-sample
proportion tests under both two-sided and one-sided alternatives.
"""

from dataclasses import dataclass
import math
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class MDEResult:
    """Result of Minimum Detectable Effect computation."""
    baseline_cr: float
    sample_size_per_group: int
    alpha: float
    power: float
    mde_absolute: float  # In conversion rate diff (e.g. 0.00338)
    mde_absolute_pp: float  # In percentage points (e.g. 0.338 pp)
    mde_relative_pct: float  # (mde_absolute / baseline_cr) * 100 (e.g. 2.81%)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_cr": self.baseline_cr,
            "sample_size_per_group": self.sample_size_per_group,
            "alpha": self.alpha,
            "power": self.power,
            "mde_absolute": self.mde_absolute,
            "mde_absolute_pp": self.mde_absolute_pp,
            "mde_relative_pct": self.mde_relative_pct,
        }


def calculate_sample_size_per_group(
    baseline_cr: float,
    mde_relative_pct: float,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided",
) -> int:
    """
    Calculates required sample size per variant for a two-sample proportion test.

    Args:
        baseline_cr: Baseline conversion rate (e.g. 0.12)
        mde_relative_pct: Target relative MDE percentage (e.g. 2.0 for 2%)
        alpha: Type I error rate (default 0.05)
        power: Statistical power 1 - beta (default 0.80)
        alternative: 'two-sided' (default) or 'one-sided'

    Returns:
        Required sample size per group (rounded up to nearest integer).
    """
    if not (0.0 < baseline_cr < 1.0):
        raise ValueError(f"baseline_cr must be strictly between 0 and 1 (got {baseline_cr}).")
    if mde_relative_pct == 0:
        raise ValueError("mde_relative_pct cannot be zero.")
    if not (0.0 < alpha < 1.0) or not (0.0 < power < 1.0):
        raise ValueError("alpha and power must be strictly between 0 and 1.")

    p1 = baseline_cr
    delta = p1 * (mde_relative_pct / 100.0)
    p2 = p1 + delta

    if not (0.0 < p2 < 1.0):
        raise ValueError(f"Resulting treatment CR ({p2}) must be between 0 and 1.")

    if alternative == "two-sided":
        z_alpha = stats.norm.ppf(1.0 - alpha / 2.0)
    elif alternative in ("one-sided", "larger", "smaller"):
        z_alpha = stats.norm.ppf(1.0 - alpha)
    else:
        raise ValueError(f"Unknown alternative '{alternative}'. Choose 'two-sided' or 'one-sided'.")

    z_beta = stats.norm.ppf(power)

    p_bar = (p1 + p2) / 2.0
    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1.0 - p_bar))
        + z_beta * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))
    ) ** 2
    denominator = (p2 - p1) ** 2

    n_required = math.ceil(numerator / denominator)
    return int(n_required)


def calculate_mde(
    baseline_cr: float,
    sample_size_per_group: int,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided",
) -> MDEResult:
    """
    Computes the Minimum Detectable Effect (MDE) given sample size per group.

    Formula (Normal approximation for equal-sized groups):
        delta_mde = (z_{alpha/2} + z_{beta}) * sqrt(2 * p * (1 - p) / n)
    """
    if not (0.0 < baseline_cr < 1.0):
        raise ValueError(f"baseline_cr must be strictly between 0 and 1 (got {baseline_cr}).")
    if sample_size_per_group <= 1:
        raise ValueError(f"sample_size_per_group must be > 1 (got {sample_size_per_group}).")
    if not (0.0 < alpha < 1.0) or not (0.0 < power < 1.0):
        raise ValueError("alpha and power must be strictly between 0 and 1.")

    if alternative == "two-sided":
        z_alpha = stats.norm.ppf(1.0 - alpha / 2.0)
    elif alternative in ("one-sided", "larger", "smaller"):
        z_alpha = stats.norm.ppf(1.0 - alpha)
    else:
        raise ValueError(f"Unknown alternative '{alternative}'. Choose 'two-sided' or 'one-sided'.")

    z_beta = stats.norm.ppf(power)

    se = math.sqrt(2.0 * baseline_cr * (1.0 - baseline_cr) / sample_size_per_group)
    mde_abs = (z_alpha + z_beta) * se
    mde_rel = (mde_abs / baseline_cr) * 100.0

    return MDEResult(
        baseline_cr=baseline_cr,
        sample_size_per_group=sample_size_per_group,
        alpha=alpha,
        power=power,
        mde_absolute=float(mde_abs),
        mde_absolute_pp=float(mde_abs * 100.0),
        mde_relative_pct=float(mde_rel),
    )


def calculate_statistical_power(
    baseline_cr: float,
    effect_absolute: float,
    sample_size_per_group: int,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> float:
    """
    Calculates statistical power for a two-sample proportion test.

    IMPORTANT STATISTICAL NOTE ON TWO-SIDED POWER:
    For a two-sided test at significance level alpha, the rejection region covers
    both tails: {Z > z_{1-alpha/2}} U {Z < -z_{1-alpha/2}}.
    Under alternative mean shift theta = |effect| / SE:
        Power = Phi(theta - z_{1-alpha/2}) + Phi(-theta - z_{1-alpha/2})

    Property Check:
    When effect_absolute == 0 (null hypothesis is true),
    Power = Phi(-z_{1-alpha/2}) + Phi(-z_{1-alpha/2}) = 2 * (alpha / 2) = alpha.
    """
    if sample_size_per_group <= 1:
        return 0.0
    if not (0.0 < baseline_cr < 1.0):
        raise ValueError(f"baseline_cr must be strictly between 0 and 1 (got {baseline_cr}).")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be strictly between 0 and 1 (got {alpha}).")

    se = math.sqrt(2.0 * baseline_cr * (1.0 - baseline_cr) / sample_size_per_group)
    if se == 0:
        return 0.0

    theta = abs(effect_absolute) / se

    if alternative == "two-sided":
        z_crit = stats.norm.ppf(1.0 - alpha / 2.0)
        # Sum of both rejection tails under shifted normal distribution
        power = float(stats.norm.cdf(theta - z_crit) + stats.norm.cdf(-theta - z_crit))
    elif alternative in ("one-sided", "larger", "smaller"):
        z_crit = stats.norm.ppf(1.0 - alpha)
        power = float(stats.norm.cdf(theta - z_crit))
    else:
        raise ValueError(f"Unknown alternative '{alternative}'. Choose 'two-sided' or 'one-sided'.")

    # Power is bounded in [alpha, 1.0] for two-sided test
    return float(np.clip(power, 0.0, 1.0))


def generate_power_curve(
    baseline_cr: float,
    sample_size_per_group: int,
    alpha: float = 0.05,
    min_rel_lift: float = 0.0,
    max_rel_lift: float = 6.0,
    steps: int = 50,
    alternative: str = "two-sided",
) -> pd.DataFrame:
    """
    Generates a DataFrame of statistical power across a spectrum of relative lift values.
    """
    rel_lifts = np.linspace(min_rel_lift, max_rel_lift, steps)
    powers = []
    abs_lifts = []

    for r_lift in rel_lifts:
        abs_lift = baseline_cr * (r_lift / 100.0)
        pwr = calculate_statistical_power(
            baseline_cr=baseline_cr,
            effect_absolute=abs_lift,
            sample_size_per_group=sample_size_per_group,
            alpha=alpha,
            alternative=alternative,
        )
        powers.append(pwr)
        abs_lifts.append(abs_lift * 100.0)

    return pd.DataFrame({
        "relative_lift_pct": rel_lifts,
        "absolute_lift_pp": abs_lifts,
        "power": powers,
    })
