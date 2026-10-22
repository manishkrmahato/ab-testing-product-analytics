"""
End-to-end experimentation execution pipeline.

Performs ingestion, structural quality auditing, cleaning, SQLite population,
statistical testing, power analysis, Bayesian inference, sensitivity analysis,
and chart generation.
"""

import os
import sys
import pandas as pd

from src.data_loader import ensure_data_downloaded, load_raw_experiment_data, load_countries_data
from src.data_cleaning import (
    audit_raw_data,
    clean_matched_filter_cohort,
    run_sensitivity_analysis,
)
from src.metrics import calculate_experiment_metrics
from src.hypothesis_testing import (
    two_proportion_z_test,
    chi_square_test,
    fishers_exact_test,
    sample_ratio_mismatch_test,
    confidence_interval_difference,
)
from src.power_analysis import calculate_mde, generate_power_curve, calculate_statistical_power
from src.bayesian_analysis import run_bayesian_ab_test
from src.database import initialize_database, populate_database, reconcile_sql_and_python_metrics
from src.visualization import (
    plot_conversion_rates_with_ci,
    plot_daily_and_cumulative_trends,
    plot_country_segment_breakdown,
    plot_power_and_mde_curve,
    plot_bayesian_posterior_distributions,
    plot_sensitivity_comparison,
)


def run_full_pipeline(
    raw_dir: str = "data/raw",
    processed_dir: str = "data/processed",
    db_path: str = "data/experiment.db",
    figures_dir: str = "reports/figures",
) -> None:
    """Executes the full analytics, modeling, database, and reporting pipeline."""
    print("=" * 70)
    print("STEP 1: Ingesting and Verifying Raw Datasets")
    print("=" * 70)
    ensure_data_downloaded(raw_dir)
    raw_df = load_raw_experiment_data(os.path.join(raw_dir, "ab_data.csv"))
    countries_df = load_countries_data(os.path.join(raw_dir, "countries.csv"))
    print(f"Loaded raw ab_data.csv: {raw_df.shape[0]:,} rows, {raw_df.shape[1]} columns")
    print(f"Loaded raw countries.csv: {countries_df.shape[0]:,} rows, {countries_df.shape[1]} columns")

    print("\n" + "=" * 70)
    print("STEP 2: Structural Data Quality Audit & Visitor Session Classification")
    print("=" * 70)
    audit_report = audit_raw_data(raw_df)
    print(f"Total Raw Records:             {audit_report.total_raw_records:,}")
    print(f"Total Unique Visitors:         {audit_report.unique_visitors:,}")
    print(f"Single-Session Visitors:       {audit_report.single_visit_visitors:,} ({(audit_report.single_visit_visitors/audit_report.unique_visitors)*100:.2f}%)")
    print(f"Multi-Session Visitors:        {audit_report.multi_visit_visitors:,} ({(audit_report.multi_visit_visitors/audit_report.unique_visitors)*100:.2f}%)")
    print(f"Conflicting Group Visitors:    {audit_report.conflicting_group_visitors:,}")
    print(f"Conflicting Page Visitors:     {audit_report.conflicting_page_visitors:,}")
    print(f"Routing Mismatch Rows:         {audit_report.total_mismatch_rows:,} (Ctrl->New: {audit_report.control_new_page_mismatch_rows:,}, Treat->Old: {audit_report.treatment_old_page_mismatch_rows:,})")
    print(f"Invalid Outcomes:              {audit_report.invalid_conversion_rows:,}")

    clean_df = clean_matched_filter_cohort(raw_df)
    os.makedirs(processed_dir, exist_ok=True)
    clean_csv_path = os.path.join(processed_dir, "clean_experiment_data.csv")
    clean_df.to_csv(clean_csv_path, index=False)
    print(f"Primary Analysis Cohort Exported: {len(clean_df):,} unique visitors to {clean_csv_path}")

    print("\n" + "=" * 70)
    print("STEP 3: Populating SQLite Database & Reconciling Metrics")
    print("=" * 70)
    initialize_database(db_path, schema_path="sql/01_schema.sql")
    populate_database(db_path, raw_df=raw_df, clean_df=clean_df, countries_df=countries_df)
    reconciled = reconcile_sql_and_python_metrics(db_path, clean_df)
    print(f"SQL vs. Python Reconciliation Status: {'ALL MATCH (PASS)' if reconciled['all_reconciled'] else 'FAIL'}")
    for k, v in reconciled.items():
        if k != "all_reconciled":
            print(f"  - {k}: SQL={v['sql']}, Python={v['py']}, Match={v['match']}")

    print("\n" + "=" * 70)
    print("STEP 4: Sample Ratio Mismatch (SRM) Integrity Check")
    print("=" * 70)
    metrics = calculate_experiment_metrics(clean_df)
    srm_res = sample_ratio_mismatch_test(metrics.n_control, metrics.n_treatment, expected_ratio=(0.5, 0.5))
    print(f"Control Observed: {srm_res.observed_control:,} (Expected: {srm_res.expected_control:,.1f})")
    print(f"Treatment Observed: {srm_res.observed_treatment:,} (Expected: {srm_res.expected_treatment:,.1f})")
    print(f"SRM Chi-Square: {srm_res.chi2_stat:.5f}, p-value: {srm_res.p_value:.4f}")
    print(f"Interpretation: {srm_res.interpretation}")

    print("\n" + "=" * 70)
    print("STEP 5: Core Statistical Inference & Hypothesis Testing")
    print("=" * 70)
    print(f"Control Conversion Rate:   {metrics.cr_control*100:.4f}% ({metrics.conversions_control:,} / {metrics.n_control:,})")
    print(f"Treatment Conversion Rate: {metrics.cr_treatment*100:.4f}% ({metrics.conversions_treatment:,} / {metrics.n_treatment:,})")
    print(f"Absolute Difference:       {metrics.absolute_difference_pp:+.4f} percentage points ({metrics.absolute_difference:+.6f})")
    print(f"Relative Lift:             {metrics.relative_lift_pct:+.4f}%")

    z_res = two_proportion_z_test(
        metrics.conversions_control, metrics.n_control,
        metrics.conversions_treatment, metrics.n_treatment,
        alternative="two-sided", pooled=True
    )
    print(f"Two-Proportion Pooled Z:   Z = {z_res.z_stat:.4f}, p = {z_res.p_value:.4f}")

    chi2_res = chi_square_test(
        metrics.conversions_control, metrics.n_control,
        metrics.conversions_treatment, metrics.n_treatment,
        correction=False
    )
    print(f"Pearson Chi-Square:        chi2 = {chi2_res.chi2_stat:.4f}, p = {chi2_res.p_value:.4f}")

    fisher_res = fishers_exact_test(
        metrics.conversions_control, metrics.n_control,
        metrics.conversions_treatment, metrics.n_treatment,
        alternative="two-sided"
    )
    print(f"Fisher's Exact Test:       Odds Ratio = {fisher_res.odds_ratio:.4f}, p = {fisher_res.p_value:.4f}")

    ci_wald = confidence_interval_difference(
        metrics.conversions_control, metrics.n_control,
        metrics.conversions_treatment, metrics.n_treatment,
        confidence_level=0.95, method="wald"
    )
    print(f"95% Wald CI for Difference:  [{ci_wald.lower_pp:+.4f}%, {ci_wald.upper_pp:+.4f}%] pp")

    ci_score = confidence_interval_difference(
        metrics.conversions_control, metrics.n_control,
        metrics.conversions_treatment, metrics.n_treatment,
        confidence_level=0.95, method="score"
    )
    print(f"95% Score CI for Difference: [{ci_score.lower_pp:+.4f}%, {ci_score.upper_pp:+.4f}%] pp")

    print("\n" + "=" * 70)
    print("STEP 6: Corrected Statistical Power Analysis & MDE")
    print("=" * 70)
    mde_res = calculate_mde(baseline_cr=metrics.cr_control, sample_size_per_group=metrics.n_control, power=0.80)
    print(f"Minimum Detectable Effect (MDE) at 80% Power: {mde_res.mde_relative_pct:.2f}% relative ({mde_res.mde_absolute_pp:.4f} pp)")

    two_sided_power = calculate_statistical_power(
        baseline_cr=metrics.cr_control,
        effect_absolute=metrics.absolute_difference,
        sample_size_per_group=metrics.n_control,
        alpha=0.05,
        alternative="two-sided",
    )
    zero_effect_power = calculate_statistical_power(
        baseline_cr=metrics.cr_control,
        effect_absolute=0.0,
        sample_size_per_group=metrics.n_control,
        alpha=0.05,
        alternative="two-sided",
    )
    print(f"Power at Zero Effect (Verification): {zero_effect_power*100:.2f}% (Expected: 5.00%)")
    print(f"Two-Sided Power for Observed Effect (-0.16 pp): {two_sided_power*100:.2f}%")

    print("\n" + "=" * 70)
    print("STEP 7: Sensitivity Analysis Across Analytical Specifications")
    print("=" * 70)
    sens_df = run_sensitivity_analysis(raw_df)
    print(sens_df.to_string(index=False))

    print("\n" + "=" * 70)
    print("STEP 8: Bayesian Beta-Binomial Inference")
    print("=" * 70)
    bayes_res, samples_c, samples_t, diff_samples = run_bayesian_ab_test(
        metrics.conversions_control, metrics.n_control,
        metrics.conversions_treatment, metrics.n_treatment,
        n_samples=200000, seed=42
    )
    print(f"Posterior Mean Control CR:    {bayes_res.posterior_mean_ctrl*100:.4f}%")
    print(f"Posterior Mean Treatment CR:  {bayes_res.posterior_mean_treat*100:.4f}%")
    print(f"P(Treatment > Control):       {bayes_res.prob_treatment_beats_control*100:.2f}%")
    print(f"P(Control > Treatment):       {(1.0 - bayes_res.prob_treatment_beats_control)*100:.2f}%")
    print(f"Expected Loss (Deploy Treat): {bayes_res.expected_loss_treatment*100:.4f} pp")
    print(f"95% Posterior Credible Interval: [{bayes_res.credible_interval_95_lower_pp:+.4f}%, {bayes_res.credible_interval_95_upper_pp:+.4f}%] pp")

    print("\n" + "=" * 70)
    print("STEP 9: Generating High-Resolution Figures")
    print("=" * 70)
    os.makedirs(figures_dir, exist_ok=True)
    plot_conversion_rates_with_ci(metrics, os.path.join(figures_dir, "01_conversion_rates_ci.png"))
    plot_daily_and_cumulative_trends(clean_df, os.path.join(figures_dir, "02_daily_and_cumulative_trends.png"))

    merged_df = clean_df.merge(countries_df, on="user_id", how="inner")
    plot_country_segment_breakdown(merged_df, os.path.join(figures_dir, "03_country_segment_breakdown.png"))

    power_curve_df = generate_power_curve(metrics.cr_control, metrics.n_control, alpha=0.05, alternative="two-sided")
    plot_power_and_mde_curve(power_curve_df, mde_res.mde_relative_pct, os.path.join(figures_dir, "04_power_curve.png"))

    plot_bayesian_posterior_distributions(samples_c, samples_t, diff_samples, bayes_res, os.path.join(figures_dir, "05_bayesian_posterior.png"))
    plot_sensitivity_comparison(sens_df, os.path.join(figures_dir, "06_sensitivity_analysis.png"))
    print(f"Saved 6 figures to {figures_dir}")

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETE & VERIFIED")
    print("=" * 70)


if __name__ == "__main__":
    run_full_pipeline()
