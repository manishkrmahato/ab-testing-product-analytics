"""
Integration and reconciliation tests between SQLite queries and Python metrics module.
Uses an isolated temporary SQLite database built from source data to ensure test reproducibility.
"""

import os
import tempfile
import pytest
import pandas as pd

from src.database import (
    initialize_database,
    populate_database,
    reconcile_sql_and_python_metrics,
    execute_query,
    execute_query_from_file,
)
from src.data_cleaning import clean_matched_filter_cohort


@pytest.fixture(scope="module")
def fresh_sqlite_db():
    """
    Creates a temporary SQLite database, runs DDL schema, and populates
    from raw and clean data to ensure testing is completely independent
    of any pre-existing bundled database file.
    """
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    schema_path = "sql/01_schema.sql"
    initialize_database(temp_db_path, schema_path=schema_path)

    # Use a representative slice if full dataset takes too long or use full if available
    raw_csv = "data/raw/ab_data.csv"
    countries_csv = "data/raw/countries.csv"

    if os.path.exists(raw_csv) and os.path.exists(countries_csv):
        raw_df = pd.read_csv(raw_csv)
        clean_df = clean_matched_filter_cohort(raw_df)
        countries_df = pd.read_csv(countries_csv)
        populate_database(temp_db_path, raw_df=raw_df, clean_df=clean_df, countries_df=countries_df)
    else:
        # Fallback synthetic data
        raw_df = pd.DataFrame({
            "user_id": [1, 2, 3, 4],
            "timestamp": ["2017-01-01 10:00:00"] * 4,
            "group": ["control", "control", "treatment", "treatment"],
            "landing_page": ["old_page", "old_page", "new_page", "new_page"],
            "converted": [0, 1, 0, 0],
        })
        clean_df = raw_df.copy()
        countries_df = pd.DataFrame({"user_id": [1, 2, 3, 4], "country": ["US", "US", "UK", "CA"]})
        populate_database(temp_db_path, raw_df=raw_df, clean_df=clean_df, countries_df=countries_df)

    yield temp_db_path

    # Cleanup temporary database
    import gc
    gc.collect()
    try:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    except PermissionError:
        pass


def test_sql_and_python_metrics_reconciliation(fresh_sqlite_db):
    reconciliation = reconcile_sql_and_python_metrics(fresh_sqlite_db)

    assert reconciliation["all_reconciled"] is True
    assert reconciliation["n_control"]["match"] is True
    assert reconciliation["conv_control"]["match"] is True
    assert reconciliation["cr_control"]["match"] is True
    assert reconciliation["n_treatment"]["match"] is True
    assert reconciliation["conv_treatment"]["match"] is True
    assert reconciliation["cr_treatment"]["match"] is True
    assert reconciliation["absolute_difference"]["match"] is True
    assert reconciliation["relative_lift_pct"]["match"] is True


def test_sql_data_quality_audit_queries(fresh_sqlite_db):
    # Verify zero duplicate users in clean_events
    clean_dupes_query = "SELECT user_id, COUNT(*) FROM clean_events GROUP BY user_id HAVING COUNT(*) > 1;"
    dupes_df = execute_query(fresh_sqlite_db, clean_dupes_query)
    assert len(dupes_df) == 0, "Clean events in SQLite must have zero duplicate user_ids."

    # Test SRM query output
    srm_df = execute_query_from_file(fresh_sqlite_db, "sql/04_srm_check.sql")
    assert len(srm_df) == 1
    row = srm_df.iloc[0]
    assert row["obs_control"] == 145274
    assert row["obs_treatment"] == 145310
    assert pytest.approx(row["chi2_statistic"], abs=1e-4) == 0.00446
