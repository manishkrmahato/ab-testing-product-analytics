"""
Hypothesis testing and confidence interval module for A/B testing.

Implements two-proportion z-tests, Pearson chi-square tests, Fisher's exact tests,
sample-ratio mismatch (SRM) checks, and multiple confidence interval formulations.
"""

from dataclasses import dataclass
import math
from typing import Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import confint_proportions_2indep


@dataclass
class ZTestResult:
    """Outcome of a two-proportion z-test."""
    z_stat: float
    p_value: float
    standard_error: float
    method: str
    alternative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "z_stat": self.z_stat,
            "p_value": self.p_value,
            "standard_error": self.standard_error,
            "method": self.method,
            "alternative": self.alternative,
        }


@dataclass
class ChiSquareResult:
    """Outcome of a 2x2 contingency Chi-Square test."""
    chi2_stat: float
    p_value: float
    dof: int
    correction: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chi2_stat": self.chi2_stat,
            "p_value": self.p_value,
            "dof": self.dof,
            "correction": self.correction,
        }


@dataclass
class FisherResult:
    """
    Outcome of Fisher's exact test.
    Odds ratio is explicitly defined as odds(treatment) / odds(control).
    """
    odds_ratio: float
    p_value: float
    alternative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "odds_ratio": self.odds_ratio,
            "p_value": self.p_value,
            "alternative": self.alternative,
        }


@dataclass
class SRMResult:
    """Outcome of Sample Ratio Mismatch (SRM) evaluation."""
    chi2_stat: float
    p_value: float
    observed_control: int
    observed_treatment: int
    expected_control: float
    expected_treatment: float
    is_srm_detected: bool
    threshold_alpha: float
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chi2_stat": self.chi2_stat,
            "p_value": self.p_value,
            "observed_control": self.observed_control,
            "observed_treatment": self.observed_treatment,
            "expected_control": self.expected_control,
            "expected_treatment": self.expected_treatment,
            "is_srm_detected": self.is_srm_detected,
            "threshold_alpha": self.threshold_alpha,
            "interpretation": self.interpretation,
        }


@dataclass
class ConfidenceIntervalResult:
    """Confidence interval for the difference between two proportions (Treatment - Control)."""
    lower: float
    upper: float
    lower_pp: float  # In percentage points
    upper_pp: float  # In percentage points
    confidence_level: float
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "lower_pp": self.lower_pp,
            "upper_pp": self.upper_pp,
            "confidence_level": self.confidence_level,
            "method": self.method,
        }


def two_proportion_z_test(
    conv_ctrl: int,
    n_ctrl: int,
    conv_treat: int,
    n_treat: int,
    alternative: str = "two-sided",
    pooled: bool = True,
) -> ZTestResult:
    """
    Computes two-proportion z-test comparing treatment vs control.
    Direction: p_treatment - p_control.

    Hypothesis:
        H0: p_treatment - p_control = 0
        H1: p_treatment - p_control != 0 (if alternative == 'two-sided')
            p_treatment - p_control > 0  (if alternative == 'larger')
            p_treatment - p_control < 0  (if alternative == 'smaller')
    """
    if n_ctrl <= 0 or n_treat <= 0:
        raise ValueError("Sample sizes must be strictly positive integers.")
    if conv_ctrl < 0 or conv_ctrl > n_ctrl or conv_treat < 0 or conv_treat > n_treat:
        raise ValueError("Conversion counts must be between 0 and their respective sample sizes.")

    p_c = conv_ctrl / n_ctrl
    p_t = conv_treat / n_treat
    diff = p_t - p_c

    if pooled:
        p_pool = (conv_ctrl + conv_treat) / (n_ctrl + n_treat)
        se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n_ctrl + 1.0 / n_treat))
        method_str = "pooled_z_test"
    else:
        var_c = p_c * (1.0 - p_c) / n_ctrl
        var_t = p_t * (1.0 - p_t) / n_treat
        se = math.sqrt(var_c + var_t)
        method_str = "unpooled_z_test"

    if se == 0.0:
        z_stat = 0.0
        p_val = 1.0
    else:
        z_stat = diff / se
        if alternative == "two-sided":
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
        elif alternative == "larger":
            p_val = float(1.0 - stats.norm.cdf(z_stat))
        elif alternative == "smaller":
            p_val = float(stats.norm.cdf(z_stat))
        else:
            raise ValueError(f"Unknown alternative '{alternative}'. Choose 'two-sided', 'larger', or 'smaller'.")

    return ZTestResult(
        z_stat=float(z_stat),
        p_value=float(p_val),
        standard_error=float(se),
        method=method_str,
        alternative=alternative,
    )


def chi_square_test(
    conv_ctrl: int,
    n_ctrl: int,
    conv_treat: int,
    n_treat: int,
    correction: bool = False,
) -> ChiSquareResult:
    """
    Computes Pearson Chi-Square test of independence on a 2x2 contingency table:
    [[conv_treat, non_conv_treat], [conv_ctrl, non_conv_ctrl]]
    """
    table = [
        [conv_treat, n_treat - conv_treat],
        [conv_ctrl, n_ctrl - conv_ctrl],
    ]
    chi2, p_val, dof, _ = stats.chi2_contingency(table, correction=correction)
    return ChiSquareResult(
        chi2_stat=float(chi2),
        p_value=float(p_val),
        dof=int(dof),
        correction=correction,
    )


def fishers_exact_test(
    conv_ctrl: int,
    n_ctrl: int,
    conv_treat: int,
    n_treat: int,
    alternative: str = "two-sided",
) -> FisherResult:
    """
    Computes Fisher's exact test on a 2x2 contingency table.
    Orientation: Row 0 is Treatment, Row 1 is Control.
    Odds ratio = odds(treatment) / odds(control).
    """
    table = [
        [conv_treat, n_treat - conv_treat],
        [conv_ctrl, n_ctrl - conv_ctrl],
    ]
    odds_ratio, p_val = stats.fisher_exact(table, alternative=alternative)
    return FisherResult(
        odds_ratio=float(odds_ratio),
        p_value=float(p_val),
        alternative=alternative,
    )


def sample_ratio_mismatch_test(
    n_ctrl: int,
    n_treat: int,
    expected_ratio: Tuple[float, float] = (0.5, 0.5),
    alpha: float = 0.001,
) -> SRMResult:
    """
    Tests for Sample Ratio Mismatch (SRM) using a Chi-Square goodness-of-fit test.

    NOTE: Failure to detect SRM (p >= alpha) indicates no statistically significant
    deviation from the target allocation ratio in the analyzed population. It does
    NOT prove that assignment was free from bias, selective attrition, or upstream routing issues.
    """
    total = n_ctrl + n_treat
    if total <= 0:
        raise ValueError("Total sample size must be strictly positive.")

    ratio_sum = sum(expected_ratio)
    r_ctrl = expected_ratio[0] / ratio_sum
    r_treat = expected_ratio[1] / ratio_sum

    exp_ctrl = total * r_ctrl
    exp_treat = total * r_treat

    observed = [n_ctrl, n_treat]
    expected = [exp_ctrl, exp_treat]

    res = stats.chisquare(f_obs=observed, f_exp=expected)
    chi2_val = float(res.statistic)
    p_val = float(res.pvalue)
    is_srm = bool(p_val < alpha)

    if is_srm:
        interp = f"SRM DETECTED (p={p_val:.4e} < {alpha}): Observed allocation deviates significantly from expected ratio."
    else:
        interp = f"No SRM detected in analyzed population (p={p_val:.4f} >= {alpha}). Allocation is consistent with {expected_ratio[0]}:{expected_ratio[1]}."

    return SRMResult(
        chi2_stat=chi2_val,
        p_value=p_val,
        observed_control=n_ctrl,
        observed_treatment=n_treat,
        expected_control=float(exp_ctrl),
        expected_treatment=float(exp_treat),
        is_srm_detected=is_srm,
        threshold_alpha=alpha,
        interpretation=interp,
    )


def confidence_interval_difference(
    conv_ctrl: int,
    n_ctrl: int,
    conv_treat: int,
    n_treat: int,
    confidence_level: float = 0.95,
    method: str = "wald",
) -> ConfidenceIntervalResult:
    """
    Calculates confidence interval for (p_treatment - p_control).

    Supported methods:
        - 'wald': Standard unpooled normal approximation
          CI = (p_t - p_c) +/- z_{alpha/2} * sqrt(p_t(1-p_t)/n_t + p_c(1-p_c)/n_c)
        - 'agresti_caffo': Adds 1 success and 1 failure to each group (+4 adjustment)
        - 'score': Newcombe / Wilson score method without continuity correction (via statsmodels)
    """
    alpha = 1.0 - confidence_level
    p_c = conv_ctrl / n_ctrl
    p_t = conv_treat / n_treat
    diff = p_t - p_c
    z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))

    if method == "wald":
        var_c = (p_c * (1.0 - p_c)) / n_ctrl
        var_t = (p_t * (1.0 - p_t)) / n_treat
        se = math.sqrt(var_c + var_t)
        margin = z_crit * se
        ci_lower = diff - margin
        ci_upper = diff + margin
    elif method == "agresti_caffo":
        n_c_adj = n_ctrl + 2
        n_t_adj = n_treat + 2
        p_c_adj = (conv_ctrl + 1) / n_c_adj
        p_t_adj = (conv_treat + 1) / n_t_adj
        diff_adj = p_t_adj - p_c_adj
        se_adj = math.sqrt((p_c_adj * (1.0 - p_c_adj) / n_c_adj) + (p_t_adj * (1.0 - p_t_adj) / n_t_adj))
        margin = z_crit * se_adj
        ci_lower = diff_adj - margin
        ci_upper = diff_adj + margin
    elif method == "score":
        ci_lower, ci_upper = confint_proportions_2indep(
            count1=conv_treat,
            nobs1=n_treat,
            count2=conv_ctrl,
            nobs2=n_ctrl,
            method="score",
            alpha=alpha,
        )
    else:
        raise ValueError(f"Unsupported method '{method}'. Choose 'wald', 'agresti_caffo', or 'score'.")

    return ConfidenceIntervalResult(
        lower=float(ci_lower),
        upper=float(ci_upper),
        lower_pp=float(ci_lower * 100.0),
        upper_pp=float(ci_upper * 100.0),
        confidence_level=confidence_level,
        method=method,
    )
