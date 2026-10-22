"""
Unit tests for src.metrics module.
"""

import pytest
import math
import pandas as pd
from src.metrics import (
    compute_conversion_rate,
    compute_absolute_lift,
    compute_relative_lift,
    compute_standard_error,
    compute_unpooled_standard_error,
    compute_pooled_standard_error,
    calculate_experiment_metrics,
)


def test_compute_conversion_rate_valid():
    assert compute_conversion_rate(10, 100) == 0.10
    assert compute_conversion_rate(0, 100) == 0.0
    assert compute_conversion_rate(100, 100) == 1.0


def test_compute_conversion_rate_zero_denominator():
    assert compute_conversion_rate(0, 0) == 0.0


def test_compute_conversion_rate_invalid_inputs():
    with pytest.raises(ValueError, match="Total visitors cannot be negative"):
        compute_conversion_rate(5, -10)

    with pytest.raises(ValueError, match="Conversions cannot be negative"):
        compute_conversion_rate(-5, 10)

    with pytest.raises(ValueError, match="cannot exceed total visitors"):
        compute_conversion_rate(15, 10)


def test_compute_absolute_lift():
    assert pytest.approx(compute_absolute_lift(0.12, 0.10), rel=1e-6) == 0.02
    assert pytest.approx(compute_absolute_lift(0.10, 0.12), rel=1e-6) == -0.02
    assert compute_absolute_lift(0.15, 0.15) == 0.0

    with pytest.raises(ValueError):
        compute_absolute_lift(1.2, 0.1)


def test_compute_relative_lift():
    # 12% vs 10% is +20% relative lift
    assert pytest.approx(compute_relative_lift(0.12, 0.10), rel=1e-6) == 20.0
    # 8% vs 10% is -20% relative lift
    assert pytest.approx(compute_relative_lift(0.08, 0.10), rel=1e-6) == -20.0
    # Equal rates
    assert compute_relative_lift(0.10, 0.10) == 0.0
    # Both zero
    assert compute_relative_lift(0.0, 0.0) == 0.0


def test_compute_relative_lift_zero_baseline_raises():
    with pytest.raises(ZeroDivisionError, match="Cannot compute relative lift against a 0.0 baseline"):
        compute_relative_lift(0.05, 0.0)


def test_compute_standard_error():
    # p = 0.5, n = 100 -> sqrt(0.25 / 100) = sqrt(0.0025) = 0.05
    assert pytest.approx(compute_standard_error(0.5, 100), rel=1e-6) == 0.05
    assert compute_standard_error(0.0, 100) == 0.0
    assert compute_standard_error(1.0, 100) == 0.0
    assert compute_standard_error(0.5, 0) == 0.0


def test_compute_pooled_and_unpooled_se():
    conv_c, n_c = 100, 1000  # 10%
    conv_t, n_t = 120, 1000  # 12%

    unpooled = compute_unpooled_standard_error(0.10, n_c, 0.12, n_t)
    expected_unpooled = math.sqrt((0.10 * 0.90 / 1000) + (0.12 * 0.88 / 1000))
    assert pytest.approx(unpooled, rel=1e-6) == expected_unpooled

    pooled = compute_pooled_standard_error(conv_c, n_c, conv_t, n_t)
    p_pool = 220 / 2000  # 0.11
    expected_pooled = math.sqrt(p_pool * (1 - p_pool) * (1 / 1000 + 1 / 1000))
    assert pytest.approx(pooled, rel=1e-6) == expected_pooled


def test_calculate_experiment_metrics_empty_group_raises():
    df_empty_ctrl = pd.DataFrame({
        "group": ["treatment", "treatment"],
        "converted": [1, 0],
    })
    with pytest.raises(ValueError, match="Both control and treatment groups must contain at least 1 record"):
        calculate_experiment_metrics(df_empty_ctrl)
