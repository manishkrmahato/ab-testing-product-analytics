"""
Unit and regression tests for src.power_analysis module.
Verifies two-sided rejection regions, agreement with statsmodels, and monotonicity.
"""

import pytest
import math
import numpy as np
from statsmodels.stats.power import NormalIndPower

from src.power_analysis import (
    calculate_sample_size_per_group,
    calculate_mde,
    calculate_statistical_power,
    generate_power_curve,
)


def test_calculate_statistical_power_at_zero_effect():
    """
    CRITICAL REGRESSION TEST:
    Under a two-sided test with null effect = 0, power must equal alpha (0.05).
    """
    baseline_cr = 0.12
    sample_size = 145000
    alpha = 0.05

    power_zero = calculate_statistical_power(
        baseline_cr=baseline_cr,
        effect_absolute=0.0,
        sample_size_per_group=sample_size,
        alpha=alpha,
        alternative="two-sided",
    )

    assert pytest.approx(power_zero, abs=1e-6) == alpha


def test_calculate_statistical_power_against_statsmodels():
    """
    Compares custom two-sided proportion power against statsmodels NormalIndPower benchmark.
    """
    baseline_cr = 0.120386
    sample_size = 145274
    alpha = 0.05
    diff = -0.001578

    power_custom = calculate_statistical_power(
        baseline_cr=baseline_cr,
        effect_absolute=diff,
        sample_size_per_group=sample_size,
        alpha=alpha,
        alternative="two-sided",
    )

    # Standardized effect size d for normal power
    pooled_sd = math.sqrt(baseline_cr * (1.0 - baseline_cr))
    std_effect = abs(diff) / pooled_sd

    sm_power = NormalIndPower().power(
        effect_size=std_effect,
        nobs1=sample_size,
        alpha=alpha,
        alternative="two-sided",
    )

    assert pytest.approx(power_custom, abs=1e-5) == sm_power


def test_two_sided_vs_one_sided_power():
    """
    For a positive effect, a one-sided test should have slightly higher power than two-sided
    because all alpha is placed in the favorable tail.
    """
    baseline_cr = 0.12
    sample_size = 50000
    effect = 0.003  # +0.3 pp

    pwr_two = calculate_statistical_power(baseline_cr, effect, sample_size, alpha=0.05, alternative="two-sided")
    pwr_one = calculate_statistical_power(baseline_cr, effect, sample_size, alpha=0.05, alternative="one-sided")

    assert pwr_one > pwr_two
    assert pwr_two > 0.05


def test_power_monotonic_with_sample_size():
    """
    Power must strictly increase as sample size increases for any non-zero effect.
    """
    baseline_cr = 0.12
    effect = 0.003

    pwr_small = calculate_statistical_power(baseline_cr, effect, sample_size_per_group=10000)
    pwr_med = calculate_statistical_power(baseline_cr, effect, sample_size_per_group=50000)
    pwr_large = calculate_statistical_power(baseline_cr, effect, sample_size_per_group=150000)

    assert pwr_small < pwr_med < pwr_large


def test_calculate_sample_size_and_mde_consistency():
    baseline_cr = 0.12
    sample_size = 145274

    mde_res = calculate_mde(baseline_cr=baseline_cr, sample_size_per_group=sample_size, alpha=0.05, power=0.80)

    # Re-calculate required sample size using the calculated MDE
    n_required = calculate_sample_size_per_group(
        baseline_cr=baseline_cr,
        mde_relative_pct=mde_res.mde_relative_pct,
        alpha=0.05,
        power=0.80,
    )

    assert pytest.approx(n_required, rel=0.02) == sample_size


def test_generate_power_curve_properties():
    df = generate_power_curve(baseline_cr=0.12, sample_size_per_group=100000, alpha=0.05)

    assert len(df) == 50
    assert "relative_lift_pct" in df.columns
    assert "power" in df.columns
    # Power at zero lift must equal alpha
    assert pytest.approx(df.iloc[0]["power"], abs=1e-4) == 0.05
    # Power must be monotonically non-decreasing
    assert (df["power"].diff().dropna() >= -1e-8).all()


def test_invalid_parameters_raise():
    with pytest.raises(ValueError):
        calculate_sample_size_per_group(baseline_cr=1.5, mde_relative_pct=5.0)

    with pytest.raises(ValueError):
        calculate_mde(baseline_cr=0.10, sample_size_per_group=0)

    with pytest.raises(ValueError):
        calculate_statistical_power(baseline_cr=0.10, effect_absolute=0.01, sample_size_per_group=100, alternative="invalid")
