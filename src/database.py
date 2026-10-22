"""
SQLite database integration and metrics reconciliation module.

Provides database initialization, automated batch ingestion, query execution,
and programmatic reconciliation between SQL-computed metrics and Python metrics.
"""

import os
import sqlite3
from typing import Dict, Any, List
import pandas as pd
from src.metrics import calculate_experiment_metrics, ExperimentMetrics


def get_connection(db_path: str = "data/experiment.db") -> sqlite3.Connection:
    """Creates a connection to the SQLite database."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    return sqlite3.connect(db_path)


def initialize_database(
    db_path: str = "data/experiment.db",
    schema_path: str = "sql/01_schema.sql",
) -> None:
    """Executes the DDL schema to prepare database tables and indexes."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)


def populate_database(
    db_path: str = "data/experiment.db",
    raw_df: pd.DataFrame = None,
    clean_df: pd.DataFrame = None,
    countries_df: pd.DataFrame = None,
    batch_size: int = 50000,
) -> None:
    """
    Loads raw events, clean events, and user country data into SQLite.
    """
    with get_connection(db_path) as conn:
        if raw_df is not None:
            raw_data = raw_df[["user_id", "timestamp", "group", "landing_page", "converted"]].copy()
            raw_data.rename(columns={"group": "group_name"}, inplace=True)
            raw_data["timestamp"] = raw_data["timestamp"].astype(str)
            raw_data.to_sql("raw_events", conn, if_exists="append", index=False, chunksize=batch_size)

        if clean_df is not None:
            clean_data = clean_df[["user_id", "timestamp", "group", "landing_page", "converted"]].copy()
            clean_data.rename(columns={"group": "group_name"}, inplace=True)
            clean_data["timestamp"] = clean_data["timestamp"].astype(str)
            clean_data.to_sql("clean_events", conn, if_exists="append", index=False, chunksize=batch_size)

        if countries_df is not None:
            countries_data = countries_df[["user_id", "country"]].copy()
            countries_data.to_sql("user_countries", conn, if_exists="append", index=False, chunksize=batch_size)


def execute_query(db_path: str, sql_query: str) -> pd.DataFrame:
    """Executes a SQL query and returns the results as a pandas DataFrame."""
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql_query, conn)


def execute_query_from_file(db_path: str, file_path: str) -> pd.DataFrame:
    """Reads a SQL query from file and returns the result DataFrame."""
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    return execute_query(db_path, sql)


def reconcile_sql_and_python_metrics(
    db_path: str = "data/experiment.db",
    clean_df: pd.DataFrame = None,
) -> Dict[str, Any]:
    """
    Executes sql/03_experiment_metrics.sql and compares the output with
    Python-calculated ExperimentMetrics to confirm 100% numerical concordance.
    """
    sql_df = execute_query_from_file(db_path, "sql/03_experiment_metrics.sql")
    sql_row = sql_df.iloc[0].to_dict()

    if clean_df is None:
        with get_connection(db_path) as conn:
            clean_df = pd.read_sql_query(
                "SELECT user_id, timestamp, group_name AS [group], landing_page, converted FROM clean_events",
                conn,
            )

    py_metrics = calculate_experiment_metrics(clean_df)

    reconciliation = {
        "n_control": {"sql": int(sql_row["n_control"]), "py": py_metrics.n_control, "match": int(sql_row["n_control"]) == py_metrics.n_control},
        "conv_control": {"sql": int(sql_row["conv_control"]), "py": py_metrics.conversions_control, "match": int(sql_row["conv_control"]) == py_metrics.conversions_control},
        "cr_control": {"sql": float(sql_row["cr_control"]), "py": round(py_metrics.cr_control, 6), "match": abs(float(sql_row["cr_control"]) - py_metrics.cr_control) < 1e-5},
        "n_treatment": {"sql": int(sql_row["n_treatment"]), "py": py_metrics.n_treatment, "match": int(sql_row["n_treatment"]) == py_metrics.n_treatment},
        "conv_treatment": {"sql": int(sql_row["conv_treatment"]), "py": py_metrics.conversions_treatment, "match": int(sql_row["conv_treatment"]) == py_metrics.conversions_treatment},
        "cr_treatment": {"sql": float(sql_row["cr_treatment"]), "py": round(py_metrics.cr_treatment, 6), "match": abs(float(sql_row["cr_treatment"]) - py_metrics.cr_treatment) < 1e-5},
        "absolute_difference": {"sql": float(sql_row["absolute_difference"]), "py": round(py_metrics.absolute_difference, 6), "match": abs(float(sql_row["absolute_difference"]) - py_metrics.absolute_difference) < 1e-5},
        "relative_lift_pct": {"sql": float(sql_row["relative_lift_pct"]), "py": round(py_metrics.relative_lift_pct, 4), "match": abs(float(sql_row["relative_lift_pct"]) - py_metrics.relative_lift_pct) < 1e-3},
    }

    all_match = all(item["match"] for item in reconciliation.values())
    reconciliation["all_reconciled"] = all_match
    return reconciliation
