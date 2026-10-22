"""
Core experimentation metrics computation module.

Provides mathematically verified calculations for conversion rates,
absolute difference, relative lift, and standard errors with robust handling
of boundary conditions and edge cases.
"""

from dataclasses import dataclass
import math
from typing import Dict, Any
import numpy as np
import pandas as pd


@dataclass
class ExperimentMetrics:
    """Summary of core empirical metrics for an A/B test."""
    n_control: int
    conversions_control: int
    cr_control: float
    se_control: float
    n_treatment: int
    conversions_treatment: int
    cr_treatment: float
    se_treatment: float
    absolute_difference: float  # Treatment - Control (in rate)
    absolute_difference_pp: float  # In percentage points
    relative_lift_pct: float  # ((Treat - Ctrl) / Ctrl) * 100
    se_unpooled: float
    se_pooled: float
    p_pooled: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_control": self.n_control,
            "conversions_control": self.conversions_control,
            "cr_control": self.cr_control,
            "se_control": self.se_control,
            "n_treatment": self.n_treatment,
            "conversions_treatment": self.conversions_treatment,
            "cr_treatment": self.cr_treatment,
            "se_treatment": self.se_treatment,
            "absolute_difference": self.absolute_difference,
            "absolute_difference_pp": self.absolute_difference_pp,
            "relative_lift_pct": self.relative_lift_pct,
            "se_unpooled": self.se_unpooled,
            "se_pooled": self.se_pooled,
            "p_pooled": self.p_pooled,
        }


def compute_conversion_rate(conversions: int, total: int) -> float:
    """
    Computes conversion rate = conversions / total.

    Raises:
        ValueError: If total < 0, conversions < 0, or conversions > total.
    Returns:
        0.0 if total == 0, else conversions / total.
    """
    if total < 0:
        raise ValueError(f"Total visitors cannot be negative (got {total}).")
    if conversions < 0:
        raise ValueError(f"Conversions cannot be negative (got {conversions}).")
    if conversions > total:
        raise ValueError(f"Conversions ({conversions}) cannot exceed total visitors ({total}).")
    if total == 0:
        return 0.0
    return float(conversions) / float(total)


def compute_absolute_lift(cr_treatment: float, cr_control: float) -> float:
    """
    Calculates absolute difference = cr_treatment - cr_control.
    """
    if not (0.0 <= cr_treatment <= 1.0):
        raise ValueError(f"cr_treatment must be in [0, 1] (got {cr_treatment}).")
    if not (0.0 <= cr_control <= 1.0):
        raise ValueError(f"cr_control must be in [0, 1] (got {cr_control}).")
    return float(cr_treatment - cr_control)


def compute_relative_lift(cr_treatment: float, cr_control: float) -> float:
    """
    Calculates relative lift as a percentage:
    ((cr_treatment - cr_control) / cr_control) * 100

    Raises:
        ZeroDivisionError: If baseline cr_control is 0.0 and cr_treatment != 0.0.
    """
    if not (0.0 <= cr_treatment <= 1.0):
        raise ValueError(f"cr_treatment must be in [0, 1] (got {cr_treatment}).")
    if not (0.0 <= cr_control <= 1.0):
        raise ValueError(f"cr_control must be in [0, 1] (got {cr_control}).")

    if cr_control == 0.0:
        if cr_treatment == 0.0:
            return 0.0
        raise ZeroDivisionError("Cannot compute relative lift against a 0.0 baseline conversion rate.")

    return float(((cr_treatment - cr_control) / cr_control) * 100.0)


def compute_standard_error(cr: float, total: int) -> float:
    """
    Computes standard error of a Bernoulli sample proportion: sqrt(p * (1 - p) / n).
    """
    if total <= 0:
        return 0.0
    if not (0.0 <= cr <= 1.0):
        raise ValueError(f"Conversion rate must be in [0, 1] (got {cr}).")
    return float(math.sqrt(cr * (1.0 - cr) / total))


def compute_unpooled_standard_error(cr_ctrl: float, n_ctrl: int, cr_treat: float, n_treat: int) -> float:
    """
    Computes unpooled standard error for difference in two proportions:
    sqrt((p_c * (1 - p_c) / n_c) + (p_t * (1 - p_t) / n_t))
    """
    if n_ctrl <= 0 or n_treat <= 0:
        raise ValueError("Sample sizes must be strictly positive.")
    var_ctrl = (cr_ctrl * (1.0 - cr_ctrl)) / n_ctrl
    var_treat = (cr_treat * (1.0 - cr_treat)) / n_treat
    return float(math.sqrt(var_ctrl + var_treat))


def compute_pooled_standard_error(conv_ctrl: int, n_ctrl: int, conv_treat: int, n_treat: int) -> float:
    """
    Computes pooled standard error under the null hypothesis (p_c == p_t):
    p_pool = (conv_c + conv_t) / (n_c + n_t)
    SE_pool = sqrt(p_pool * (1 - p_pool) * (1/n_c + 1/n_t))
    """
    if n_ctrl <= 0 or n_treat <= 0:
        raise ValueError("Sample sizes must be strictly positive.")
    p_pool = (conv_ctrl + conv_treat) / (n_ctrl + n_treat)
    var_pool = p_pool * (1.0 - p_pool) * (1.0 / n_ctrl + 1.0 / n_treat)
    return float(math.sqrt(var_pool))


def calculate_experiment_metrics(df: pd.DataFrame) -> ExperimentMetrics:
    """
    Computes the complete ExperimentMetrics object from a clean experiment DataFrame.
    """
    ctrl_mask = df["group"] == "control"
    treat_mask = df["group"] == "treatment"

    n_ctrl = int(ctrl_mask.sum())
    n_treat = int(treat_mask.sum())

    if n_ctrl == 0 or n_treat == 0:
        raise ValueError("Both control and treatment groups must contain at least 1 record.")

    conv_ctrl = int(df.loc[ctrl_mask, "converted"].sum())
    conv_treat = int(df.loc[treat_mask, "converted"].sum())

    cr_ctrl = compute_conversion_rate(conv_ctrl, n_ctrl)
    cr_treat = compute_conversion_rate(conv_treat, n_treat)

    se_ctrl = compute_standard_error(cr_ctrl, n_ctrl)
    se_treat = compute_standard_error(cr_treat, n_treat)

    abs_diff = compute_absolute_lift(cr_treat, cr_ctrl)
    abs_diff_pp = abs_diff * 100.0
    rel_lift = compute_relative_lift(cr_treat, cr_ctrl)

    se_unpooled = compute_unpooled_standard_error(cr_ctrl, n_ctrl, cr_treat, n_treat)
    se_pooled = compute_pooled_standard_error(conv_ctrl, n_ctrl, conv_treat, n_treat)
    p_pooled = (conv_ctrl + conv_treat) / (n_ctrl + n_treat)

    return ExperimentMetrics(
        n_control=n_ctrl,
        conversions_control=conv_ctrl,
        cr_control=cr_ctrl,
        se_control=se_ctrl,
        n_treatment=n_treat,
        conversions_treatment=conv_treat,
        cr_treatment=cr_treat,
        se_treatment=se_treat,
        absolute_difference=abs_diff,
        absolute_difference_pp=abs_diff_pp,
        relative_lift_pct=rel_lift,
        se_unpooled=se_unpooled,
        se_pooled=se_pooled,
        p_pooled=p_pooled,
    )
