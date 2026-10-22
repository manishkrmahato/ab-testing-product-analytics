"""
Unit and regression tests for src.data_cleaning module.
Verifies detection of conflicting assignments, multi-session visitors,
and consistency across sensitivity specifications.
"""

import pytest
import pandas as pd
from src.data_cleaning import (
    audit_raw_data,
    clean_matched_filter_cohort,
    clean_unambiguous_cohort,
    clean_first_touch_itt_cohort,
    clean_as_treated_cohort,
    run_sensitivity_analysis,
)


@pytest.fixture
def sample_audit_data():
    """
    Synthetic dataset with intentional edge cases:
    - User 1: Clean control
    - User 2: Clean treatment
    - User 3: Conflicting groups across 2 visits
    - User 4: Same group (treatment), but saw conflicting landing pages (old then new)
    - User 5: User with 2 clean sessions (treatment/new_page)
    """
    return pd.DataFrame({
        "user_id": [1, 2, 3, 3, 4, 4, 5, 5],
        "timestamp": [
            "2017-01-01 10:00:00",
            "2017-01-01 11:00:00",
            "2017-01-01 12:00:00",
            "2017-01-01 13:00:00",
            "2017-01-01 14:00:00",
            "2017-01-01 15:00:00",
            "2017-01-01 16:00:00",
            "2017-01-01 17:00:00",
        ],
        "group": [
            "control",    # 1
            "treatment",  # 2
            "control",    # 3 visit 1
            "treatment",  # 3 visit 2 (conflicting group!)
            "treatment",  # 4 visit 1
            "treatment",  # 4 visit 2 (conflicting page!)
            "treatment",  # 5 visit 1
            "treatment",  # 5 visit 2
        ],
        "landing_page": [
            "old_page",  # 1
            "new_page",  # 2
            "old_page",  # 3 visit 1 (matched)
            "old_page",  # 3 visit 2 (mismatch!)
            "old_page",  # 4 visit 1 (mismatch!)
            "new_page",  # 4 visit 2 (matched)
            "new_page",  # 5 visit 1 (matched)
            "new_page",  # 5 visit 2 (matched)
        ],
        "converted": [0, 1, 0, 1, 0, 0, 0, 1],
    })


def test_audit_raw_data_classifications(sample_audit_data):
    report = audit_raw_data(sample_audit_data)

    assert report.total_raw_records == 8
    assert report.unique_visitors == 5
    assert report.single_visit_visitors == 2  # users 1 and 2
    assert report.multi_visit_visitors == 3   # users 3, 4, 5
    assert report.conflicting_group_visitors == 1  # user 3
    assert report.conflicting_page_visitors == 1   # user 4
    assert report.total_mismatch_rows == 2         # user 3 row 2, user 4 row 1


def test_cohort_cleaning_rules(sample_audit_data):
    # Rule A: Unambiguous cohort (excludes users 3 and 4)
    df_unambig = clean_unambiguous_cohort(sample_audit_data)
    assert set(df_unambig["user_id"]) == {1, 2, 5}
    assert len(df_unambig) == 3

    # Rule B: Matched filter cohort (keeps matched row for all users)
    df_matched = clean_matched_filter_cohort(sample_audit_data)
    assert set(df_matched["user_id"]) == {1, 2, 3, 4, 5}
    assert len(df_matched) == 5

    # Rule C: First-touch ITT (aggregates all 5 users, takes earliest group)
    df_itt = clean_first_touch_itt_cohort(sample_audit_data)
    assert len(df_itt) == 5
    # User 3 first group was control, user 3 converted in visit 2 -> converted = 1
    u3 = df_itt[df_itt["user_id"] == 3].iloc[0]
    assert u3["group"] == "control"
    assert u3["converted"] == 1


def test_run_sensitivity_analysis_structure(sample_audit_data):
    sens_df = run_sensitivity_analysis(sample_audit_data)

    assert len(sens_df) == 4
    assert "Specification" in sens_df.columns
    assert "Diff_Percentage_Points" in sens_df.columns
    assert "P_Value" in sens_df.columns
    assert "Total_Users" in sens_df.columns


def test_missing_and_invalid_outcomes():
    """Verify that null and out-of-bounds outcomes are flagged and dropped."""
    df_invalid = pd.DataFrame({
        "user_id": [10, 11, 12, 13],
        "timestamp": ["2017-01-01 10:00:00"] * 4,
        "group": ["control", "treatment", "control", "treatment"],
        "landing_page": ["old_page", "new_page", "old_page", "new_page"],
        "converted": [0, 1, None, 2],  # User 12 is None, User 13 is invalid 2
    })

    rep = audit_raw_data(df_invalid)
    assert rep.invalid_conversion_rows == 2

    # Cleaners should safely exclude users 12 and 13
    clean_matched = clean_matched_filter_cohort(df_invalid)
    assert len(clean_matched) == 2
    assert set(clean_matched["user_id"]) == {10, 11}

    clean_unambig = clean_unambiguous_cohort(df_invalid)
    assert len(clean_unambig) == 2
    assert set(clean_unambig["user_id"]) == {10, 11}

    clean_itt = clean_first_touch_itt_cohort(df_invalid)
    assert len(clean_itt) == 2
    assert set(clean_itt["user_id"]) == {10, 11}


def test_deterministic_aggregation_and_as_treated():
    """Verify deterministic conversion aggregation (max) and as-treated assignment."""
    df_sessions = pd.DataFrame({
        "user_id": [20, 20, 21, 21],
        "timestamp": [
            "2017-01-01 10:00:00",
            "2017-01-01 12:00:00",
            "2017-01-01 11:00:00",
            "2017-01-01 13:00:00",
        ],
        "group": ["control", "treatment", "treatment", "treatment"],
        "landing_page": ["old_page", "new_page", "new_page", "old_page"],
        "converted": [0, 1, 0, 0],
    })

    # In First-Touch ITT:
    # User 20: first group is control; max(converted) is 1
    itt_df = clean_first_touch_itt_cohort(df_sessions)
    u20 = itt_df[itt_df["user_id"] == 20].iloc[0]
    assert u20["group"] == "control"
    assert u20["converted"] == 1

    # In As-Treated:
    # User 20: first page is old_page -> mapped to control; converted is 1
    # User 21: first page is new_page -> mapped to treatment; converted is 0
    at_df = clean_as_treated_cohort(df_sessions)
    assert len(at_df) == 2
    u20_at = at_df[at_df["user_id"] == 20].iloc[0]
    u21_at = at_df[at_df["user_id"] == 21].iloc[0]
    assert u20_at["group"] == "control"
    assert u20_at["converted"] == 1
    assert u21_at["group"] == "treatment"
    assert u21_at["converted"] == 0


def test_full_dataset_reconciliation_and_exclusion_counts():
    """Regression test against the full actual raw dataset if present."""
    import os
    raw_path = "data/raw/ab_data.csv"
    if not os.path.exists(raw_path):
        pytest.skip(f"Raw data file not found at {raw_path}")

    raw_df = pd.read_csv(raw_path)
    audit = audit_raw_data(raw_df)

    # Assert exact raw counts
    assert audit.total_raw_records == 294478
    assert audit.unique_visitors == 290584
    assert audit.single_visit_visitors == 286690
    assert audit.multi_visit_visitors == 3894
    assert audit.conflicting_group_visitors == 1895
    assert audit.conflicting_page_visitors == 1998
    assert audit.control_new_page_mismatch_rows == 1928
    assert audit.treatment_old_page_mismatch_rows == 1965
    assert audit.total_mismatch_rows == 3893
    assert audit.invalid_conversion_rows == 0

    # Assert cohort sizes
    benchmark = clean_matched_filter_cohort(raw_df)
    assert len(benchmark) == 290584
    assert benchmark["user_id"].nunique() == 290584

    unambiguous = clean_unambiguous_cohort(raw_df)
    assert len(unambiguous) == 286691
    assert unambiguous["user_id"].nunique() == 286691
    # Exactly 290,584 - 3,893 = 286,691
    assert len(benchmark) - len(unambiguous) == 3893

    itt = clean_first_touch_itt_cohort(raw_df)
    assert len(itt) == 290584

    as_treated = clean_as_treated_cohort(raw_df)
    assert len(as_treated) == 290584
