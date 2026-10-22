"""
Bayesian A/B testing module using Beta-Binomial conjugate analysis.

Computes posterior distributions, probability of treatment superiority,
Bayesian credible intervals, and decision-theoretic expected loss.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any
import numpy as np
from scipy import stats


@dataclass
class BayesianABResult:
    """Outcome of Bayesian A/B test analysis."""
    prior_alpha_ctrl: float
    prior_beta_ctrl: float
    posterior_alpha_ctrl: float
    posterior_beta_ctrl: float
    posterior_mean_ctrl: float
    prior_alpha_treat: float
    prior_beta_treat: float
    posterior_alpha_treat: float
    posterior_beta_treat: float
    posterior_mean_treat: float
    prob_treatment_beats_control: float
    expected_loss_treatment: float  # In conversion rate units
    expected_loss_control: float
    credible_interval_95_lower: float  # Difference in CR
    credible_interval_95_upper: float
    credible_interval_95_lower_pp: float  # Percentage points
    credible_interval_95_upper_pp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prior_alpha_ctrl": self.prior_alpha_ctrl,
            "prior_beta_ctrl": self.prior_beta_ctrl,
            "posterior_alpha_ctrl": self.posterior_alpha_ctrl,
            "posterior_beta_ctrl": self.posterior_beta_ctrl,
            "posterior_mean_ctrl": self.posterior_mean_ctrl,
            "prior_alpha_treat": self.prior_alpha_treat,
            "prior_beta_treat": self.prior_beta_treat,
            "posterior_alpha_treat": self.posterior_alpha_treat,
            "posterior_beta_treat": self.posterior_beta_treat,
            "posterior_mean_treat": self.posterior_mean_treat,
            "prob_treatment_beats_control": self.prob_treatment_beats_control,
            "expected_loss_treatment": self.expected_loss_treatment,
            "expected_loss_control": self.expected_loss_control,
            "credible_interval_95_lower": self.credible_interval_95_lower,
            "credible_interval_95_upper": self.credible_interval_95_upper,
            "credible_interval_95_lower_pp": self.credible_interval_95_lower_pp,
            "credible_interval_95_upper_pp": self.credible_interval_95_upper_pp,
        }


def beta_binomial_update(
    prior_alpha: float,
    prior_beta: float,
    conversions: int,
    total: int,
) -> Tuple[float, float]:
    """
    Computes exact posterior Beta parameters under Binomial likelihood:
    alpha_post = alpha_prior + conversions
    beta_post = beta_prior + (total - conversions)
    """
    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("Prior parameters alpha and beta must be strictly positive.")
    if conversions < 0 or total < conversions:
        raise ValueError("Invalid conversion counts.")

    post_alpha = prior_alpha + conversions
    post_beta = prior_beta + (total - conversions)
    return float(post_alpha), float(post_beta)


def run_bayesian_ab_test(
    conv_ctrl: int,
    n_ctrl: int,
    conv_treat: int,
    n_treat: int,
    prior_alpha_ctrl: float = 1.0,
    prior_beta_ctrl: float = 1.0,
    prior_alpha_treat: float = 1.0,
    prior_beta_treat: float = 1.0,
    n_samples: int = 200000,
    seed: int = 42,
) -> Tuple[BayesianABResult, np.ndarray, np.ndarray, np.ndarray]:
    """
    Conducts Bayesian A/B testing via Beta-Binomial conjugate updating and Monte Carlo sampling.

    Returns:
        (BayesianABResult, samples_ctrl, samples_treat, samples_diff)
    """
    post_a_c, post_b_c = beta_binomial_update(prior_alpha_ctrl, prior_beta_ctrl, conv_ctrl, n_ctrl)
    post_a_t, post_b_t = beta_binomial_update(prior_alpha_treat, prior_beta_treat, conv_treat, n_treat)

    post_mean_c = post_a_c / (post_a_c + post_b_c)
    post_mean_t = post_a_t / (post_a_t + post_b_t)

    # Monte Carlo simulation from posterior distributions
    rng = np.random.default_rng(seed)
    samples_c = rng.beta(post_a_c, post_b_c, size=n_samples)
    samples_t = rng.beta(post_a_t, post_b_t, size=n_samples)
    diff = samples_t - samples_c

    # Probability treatment is superior
    prob_t_beats_c = float(np.mean(samples_t > samples_c))

    # Expected Loss (in conversion rate units)
    # Loss of choosing treatment when control is actually better
    loss_treatment = float(np.mean(np.maximum(samples_c - samples_t, 0.0)))
    # Loss of choosing control when treatment is actually better
    loss_control = float(np.mean(np.maximum(samples_t - samples_c, 0.0)))

    # 95% Credible Interval for difference
    ci_lower = float(np.percentile(diff, 2.5))
    ci_upper = float(np.percentile(diff, 97.5))

    result = BayesianABResult(
        prior_alpha_ctrl=prior_alpha_ctrl,
        prior_beta_ctrl=prior_beta_ctrl,
        posterior_alpha_ctrl=post_a_c,
        posterior_beta_ctrl=post_b_c,
        posterior_mean_ctrl=float(post_mean_c),
        prior_alpha_treat=prior_alpha_treat,
        prior_beta_treat=prior_beta_treat,
        posterior_alpha_treat=post_a_t,
        posterior_beta_treat=post_b_t,
        posterior_mean_treat=float(post_mean_t),
        prob_treatment_beats_control=prob_t_beats_c,
        expected_loss_treatment=loss_treatment,
        expected_loss_control=loss_control,
        credible_interval_95_lower=ci_lower,
        credible_interval_95_upper=ci_upper,
        credible_interval_95_lower_pp=ci_lower * 100.0,
        credible_interval_95_upper_pp=ci_upper * 100.0,
    )

    return result, samples_c, samples_t, diff
