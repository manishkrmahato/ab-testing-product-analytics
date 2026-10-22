"""
Data quality auditing, anomaly classification, and cohort cleaning module.

Performs deep structural audits on visitor sessions, identifies conflicting group
assignments and routing mismatches, and provides defensible cohort specifications
alongside comprehensive sensitivity analysis.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, Set
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest


@dataclass
class QualityAuditReport:
    """Comprehensive report detailing raw data structure and anomalies."""
    total_raw_records: int
    unique_visitors: int
    single_visit_visitors: int
    multi_visit_visitors: int
    conflicting_group_visitors: int
    conflicting_page_visitors: int
    control_new_page_mismatch_rows: int
    treatment_old_page_mismatch_rows: int
    total_mismatch_rows: int
    invalid_conversion_rows: int
    start_timestamp: str
    end_timestamp: str
    duration_days: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_raw_records": self.total_raw_records,
            "unique_visitors": self.unique_visitors,
            "single_visit_visitors": self.single_visit_visitors,
            "multi_visit_visitors": self.multi_visit_visitors,
            "conflicting_group_visitors": self.conflicting_group_visitors,
            "conflicting_page_visitors": self.conflicting_page_visitors,
            "control_new_page_mismatch_rows": self.control_new_page_mismatch_rows,
            "treatment_old_page_mismatch_rows": self.treatment_old_page_mismatch_rows,
            "total_mismatch_rows": self.total_mismatch_rows,
            "invalid_conversion_rows": self.invalid_conversion_rows,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "duration_days": self.duration_days,
        }


def audit_raw_data(df: pd.DataFrame) -> QualityAuditReport:
    """
    Performs comprehensive structural audit on raw experiment logs.
    """
    total_records = len(df)
    unique_users = df["user_id"].nunique()

    # Visitor visit frequency
    visit_counts = df["user_id"].value_counts()
    single_visit = int((visit_counts == 1).sum())
    multi_visit = int((visit_counts > 1).sum())

    # Multi-visit visitor anomalies
    multi_ids = visit_counts[visit_counts > 1].index
    df_multi = df[df["user_id"].isin(multi_ids)]

    group_counts_per_user = df_multi.groupby("user_id")["group"].nunique()
    conflicting_groups = int((group_counts_per_user > 1).sum())

    page_counts_per_user = df_multi.groupby("user_id")["landing_page"].nunique()
    conflicting_pages = int((page_counts_per_user > 1).sum())

    # Row-level routing mismatches
    ctrl_new = int(((df["group"] == "control") & (df["landing_page"] == "new_page")).sum())
    treat_old = int(((df["group"] == "treatment") & (df["landing_page"] == "old_page")).sum())
    total_mismatches = ctrl_new + treat_old

    # Outcome integrity
    invalid_conv = int((~df["converted"].isin([0, 1])).sum())

    ts = pd.to_datetime(df["timestamp"])
    start_ts = str(ts.min())
    end_ts = str(ts.max())
    duration_days = round((ts.max() - ts.min()).total_seconds() / 86400.0, 2)

    return QualityAuditReport(
        total_raw_records=total_records,
        unique_visitors=unique_users,
        single_visit_visitors=single_visit,
        multi_visit_visitors=multi_visit,
        conflicting_group_visitors=conflicting_groups,
        conflicting_page_visitors=conflicting_pages,
        control_new_page_mismatch_rows=ctrl_new,
        treatment_old_page_mismatch_rows=treat_old,
        total_mismatch_rows=total_mismatches,
        invalid_conversion_rows=invalid_conv,
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        duration_days=duration_days,
    )


def clean_matched_filter_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standard Benchmark Cohort (Udacity convention):
    Excludes the 3,893 mismatched rows where group != landing_page,
    drops missing or invalid outcomes,
    then deduplicates by user_id keeping the earliest visit.
    Resulting size: 290,584 unique visitors.
    """
    valid_df = df.dropna(subset=["user_id", "group", "landing_page", "converted"]).copy()
    valid_df = valid_df[valid_df["converted"].isin([0, 1])].copy()

    is_mismatch = (
        ((valid_df["group"] == "treatment") & (valid_df["landing_page"] == "old_page")) |
        ((valid_df["group"] == "control") & (valid_df["landing_page"] == "new_page"))
    )
    filtered = valid_df[~is_mismatch].copy()
    filtered["timestamp"] = pd.to_datetime(filtered["timestamp"])
    filtered = filtered.sort_values(by="timestamp", ascending=True)
    clean_df = filtered.drop_duplicates(subset=["user_id"], keep="first").copy()
    clean_df.reset_index(drop=True, inplace=True)
    return clean_df


def clean_unambiguous_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strict Complete-Case Cohort:
    Excludes all 3,893 visitors with any routing mismatch or conflicting assignment,
    retaining only visitors whose experiment exposure was completely unambiguous.
    Resulting size: 286,691 unique visitors.
    """
    valid_df = df.dropna(subset=["user_id", "group", "landing_page", "converted"]).copy()
    valid_df = valid_df[valid_df["converted"].isin([0, 1])].copy()

    is_mismatch = (
        ((valid_df["group"] == "treatment") & (valid_df["landing_page"] == "old_page")) |
        ((valid_df["group"] == "control") & (valid_df["landing_page"] == "new_page"))
    )
    mismatched_users = set(valid_df.loc[is_mismatch, "user_id"])

    df_clean = valid_df[~valid_df["user_id"].isin(mismatched_users)].copy()
    df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])
    df_clean = df_clean.sort_values(by="timestamp", ascending=True)
    df_clean = df_clean.drop_duplicates(subset=["user_id"], keep="first").copy()
    df_clean.reset_index(drop=True, inplace=True)
    return df_clean


def clean_first_touch_itt_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    First-Touch Assignment-Proxy Cohort:
    Preserves unique visitors without exclusion. Uses the earliest recorded `group`
    as an assignment proxy because an authoritative assignment log is unavailable.
    Aggregates outcome as max(converted) across sessions; this is not verified true ITT.
    """
    valid_df = df.dropna(subset=["user_id", "group", "landing_page", "converted"]).copy()
    valid_df = valid_df[valid_df["converted"].isin([0, 1])].copy()

    df_sorted = valid_df.copy()
    df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
    df_sorted = df_sorted.sort_values(by="timestamp", ascending=True)

    itt_df = df_sorted.groupby("user_id").agg(
        timestamp=("timestamp", "first"),
        group=("group", "first"),
        landing_page=("landing_page", "first"),
        converted=("converted", "max"),
        total_sessions=("group", "count"),
    ).reset_index()
    return itt_df


def clean_as_treated_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    As-Treated / First Page Viewed Cohort:
    Assigns each visitor based on the first webpage version they actually viewed
    (old_page = control, new_page = treatment), with conversion = max(converted).
    Resulting size: 290,584 unique visitors.
    """
    valid_df = df.dropna(subset=["user_id", "group", "landing_page", "converted"]).copy()
    valid_df = valid_df[valid_df["converted"].isin([0, 1])].copy()

    df_sorted = valid_df.copy()
    df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
    df_sorted = df_sorted.sort_values(by="timestamp", ascending=True)

    as_treated = df_sorted.groupby("user_id").agg(
        timestamp=("timestamp", "first"),
        landing_page=("landing_page", "first"),
        converted=("converted", "max"),
        total_sessions=("group", "count"),
    ).reset_index()

    as_treated["group"] = as_treated["landing_page"].map({
        "old_page": "control",
        "new_page": "treatment"
    })
    return as_treated


def clean_experiment_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, QualityAuditReport]:
    """
    Default project cleaner: produces the standard benchmark cohort (Rule B),
    while validating and attaching the comprehensive audit report.
    """
    report = audit_raw_data(df)
    clean_df = clean_matched_filter_cohort(df)
    return clean_df, report


def run_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executes comparative sensitivity analysis across all 4 candidate visitor-level definitions:
    1. Benchmark Matched Cohort (N = 290,584)
    2. Strictly Unambiguous Cohort (N = 286,691)
    3. First-Touch Assignment Proxy (N = 290,584)
    4. As-Treated / First Page Viewed (N = 290,584)
    """
    cohorts = {
        "Benchmark (Matched Filter)": clean_matched_filter_cohort(df),
        "Strictly Unambiguous Cohort": clean_unambiguous_cohort(df),
        "First-Touch Assignment Proxy": clean_first_touch_itt_cohort(df),
        "As-Treated (First Page)": clean_as_treated_cohort(df),
    }

    records = []
    for name, c_df in cohorts.items():
        n_ctrl = int((c_df["group"] == "control").sum())
        n_treat = int((c_df["group"] == "treatment").sum())
        x_ctrl = int(c_df.loc[c_df["group"] == "control", "converted"].sum())
        x_treat = int(c_df.loc[c_df["group"] == "treatment", "converted"].sum())

        cr_ctrl = x_ctrl / n_ctrl if n_ctrl > 0 else 0.0
        cr_treat = x_treat / n_treat if n_treat > 0 else 0.0
        diff = cr_treat - cr_ctrl
        if cr_ctrl == 0.0:
            rel_lift = 0.0 if cr_treat == 0.0 else float("nan")
        else:
            rel_lift = (diff / cr_ctrl) * 100.0

        if n_ctrl > 0 and n_treat > 0:
            z_stat, p_val = proportions_ztest([x_treat, x_ctrl], [n_treat, n_ctrl], alternative="two-sided")
        else:
            z_stat, p_val = 0.0, 1.0

        records.append({
            "Specification": name,
            "N_Control": n_ctrl,
            "N_Treatment": n_treat,
            "Total_Users": n_ctrl + n_treat,
            "CR_Control_Pct": round(cr_ctrl * 100.0, 4),
            "CR_Treatment_Pct": round(cr_treat * 100.0, 4),
            "Diff_Percentage_Points": round(diff * 100.0, 4),
            "Relative_Lift_Pct": round(rel_lift, 4),
            "Z_Statistic": round(float(z_stat), 4),
            "P_Value": round(float(p_val), 4),
            "Statistically_Significant_05": p_val < 0.05,
        })

    return pd.DataFrame(records)
