"""
Unit tests for src.bayesian_analysis module.
"""

import pytest
import numpy as np
from src.bayesian_analysis import beta_binomial_update, run_bayesian_ab_test


def test_beta_binomial_update():
    # Prior Beta(1, 1), 10 conversions out of 100
    alpha_post, beta_post = beta_binomial_update(1.0, 1.0, conversions=10, total=100)
    assert alpha_post == 11.0
    assert beta_post == 91.0


def test_bayesian_ab_test_properties():
    conv_c, n_c = 100, 1000  # 10%
    conv_t, n_t = 150, 1000  # 15%

    res, samples_c, samples_t, diff = run_bayesian_ab_test(
        conv_c, n_c, conv_t, n_t, n_samples=50000, seed=123
    )

    # Treatment clearly better
    assert res.prob_treatment_beats_control > 0.99
    assert res.expected_loss_treatment < res.expected_loss_control
    assert res.credible_interval_95_lower > 0.0

    # Symmetry when groups are identical
    res_ident, _, _, _ = run_bayesian_ab_test(
        100, 1000, 100, 1000, n_samples=50000, seed=123
    )
    assert pytest.approx(res_ident.prob_treatment_beats_control, abs=0.03) == 0.50
    assert res_ident.credible_interval_95_lower < 0.0 < res_ident.credible_interval_95_upper


def test_invalid_bayesian_inputs_raise():
    with pytest.raises(ValueError):
        beta_binomial_update(-1.0, 1.0, 10, 100)

    with pytest.raises(ValueError):
        beta_binomial_update(1.0, 1.0, 110, 100)
