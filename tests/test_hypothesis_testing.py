"""
Unit and regression tests for src.hypothesis_testing module.
Validates statistical calculations, odds ratio orientations, boundary conditions,
and benchmarks against SciPy and Statsmodels.
"""

import pytest
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

from src.hypothesis_testing import (
    two_proportion_z_test,
    chi_square_test,
    fishers_exact_test,
    sample_ratio_mismatch_test,
    confidence_interval_difference,
)


def test_two_proportion_z_test_against_statsmodels():
    conv_c, n_c = 17489, 145274
    conv_t, n_t = 17264, 145310

    res = two_proportion_z_test(conv_c, n_c, conv_t, n_t, alternative="two-sided", pooled=True)
    sm_z, sm_p = proportions_ztest([conv_t, conv_c], [n_t, n_c], alternative="two-sided")

    assert pytest.approx(res.z_stat, rel=1e-5) == sm_z
    assert pytest.approx(res.p_value, rel=1e-5) == sm_p


def test_two_proportion_z_test_alternatives():
    conv_c, n_c = 100, 1000  # 10%
    conv_t, n_t = 150, 1000  # 15% (treatment larger)

    res_two = two_proportion_z_test(conv_c, n_c, conv_t, n_t, alternative="two-sided")
    res_larger = two_proportion_z_test(conv_c, n_c, conv_t, n_t, alternative="larger")
    res_smaller = two_proportion_z_test(conv_c, n_c, conv_t, n_t, alternative="smaller")

    assert res_two.z_stat > 0
    assert pytest.approx(res_larger.p_value * 2.0, rel=1e-5) == res_two.p_value
    assert res_smaller.p_value > 0.99


def test_chi_square_test_against_scipy():
    conv_c, n_c = 17489, 145274
    conv_t, n_t = 17264, 145310

    res = chi_square_test(conv_c, n_c, conv_t, n_t, correction=False)
    table = [[conv_t, n_t - conv_t], [conv_c, n_c - conv_c]]
    scipy_chi2, scipy_p, dof, _ = stats.chi2_contingency(table, correction=False)

    assert pytest.approx(res.chi2_stat, rel=1e-5) == scipy_chi2
    assert pytest.approx(res.p_value, rel=1e-5) == scipy_p
    assert res.dof == 1


def test_fishers_exact_test_orientation_and_inversion():
    """
    CRITICAL REGRESSION TEST:
    Ensures odds ratio is defined as odds(treatment) / odds(control).
    When treatment CR < control CR, OR must be < 1.0.
    Reversing the groups must invert the odds ratio (OR' = 1 / OR).
    """
    conv_c, n_c = 60, 500  # 12%
    conv_t, n_t = 45, 500  # 9% (treatment lower)

    res = fishers_exact_test(conv_c, n_c, conv_t, n_t)
    table = [[conv_t, n_t - conv_t], [conv_c, n_c - conv_c]]
    scipy_or, scipy_p = stats.fisher_exact(table)

    assert res.odds_ratio < 1.0
    assert pytest.approx(res.odds_ratio, rel=1e-5) == scipy_or
    assert pytest.approx(res.p_value, rel=1e-5) == scipy_p

    # Invert groups: treatment higher
    res_inverted = fishers_exact_test(conv_t, n_t, conv_c, n_c)
    assert pytest.approx(res.odds_ratio * res_inverted.odds_ratio, rel=1e-5) == 1.0


def test_sample_ratio_mismatch_clean():
    n_c, n_t = 145274, 145310
    srm = sample_ratio_mismatch_test(n_c, n_t, expected_ratio=(0.5, 0.5), alpha=0.01)

    assert not srm.is_srm_detected
    assert srm.p_value > 0.05
    assert pytest.approx(srm.expected_control, abs=1.0) == 145292.0
    assert "No SRM detected" in srm.interpretation


def test_sample_ratio_mismatch_detected_on_skew():
    n_c, n_t = 60000, 40000
    srm = sample_ratio_mismatch_test(n_c, n_t, expected_ratio=(0.5, 0.5), alpha=0.01)

    assert srm.is_srm_detected
    assert srm.p_value < 1e-10
    assert "SRM DETECTED" in srm.interpretation


def test_confidence_interval_difference_wald_and_score():
    conv_c, n_c = 17489, 145274
    conv_t, n_t = 17264, 145310

    wald = confidence_interval_difference(conv_c, n_c, conv_t, n_t, confidence_level=0.95, method="wald")
    score = confidence_interval_difference(conv_c, n_c, conv_t, n_t, confidence_level=0.95, method="score")

    # In large samples, Wald and Score are very close but distinct calculations
    assert pytest.approx(wald.lower, rel=1e-3) == score.lower
    assert pytest.approx(wald.upper, rel=1e-3) == score.upper
    assert wald.lower < 0.0 < wald.upper


def test_boundary_zero_and_all_conversions():
    # Boundary: Zero conversions in both groups
    res_zero = two_proportion_z_test(0, 100, 0, 100)
    assert res_zero.z_stat == 0.0
    assert res_zero.p_value == 1.0

    # Boundary: 100% conversions in both groups
    res_full = two_proportion_z_test(100, 100, 100, 100)
    assert res_full.z_stat == 0.0
    assert res_full.p_value == 1.0


def test_invalid_sample_sizes_raise():
    with pytest.raises(ValueError):
        two_proportion_z_test(10, 0, 10, 100)

    with pytest.raises(ValueError):
        sample_ratio_mismatch_test(0, 0)
