"""
Builds and executes the project's Jupyter Notebooks with verified real results.
"""

import os
import nbformat as nbf
from nbclient import NotebookClient


def create_eda_notebook(output_path: str = "notebooks/01_exploratory_data_analysis.ipynb"):
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.13"
        }
    }

    cells = []

    # Title & Role
    cells.append(nbf.v4.new_markdown_cell("""# 01. Exploratory Data Analysis: E-Commerce A/B Test Results

**Project**: A/B Testing & Product Experimentation Analytics  
**Role**: Senior Experimentation Analyst / Data Scientist  
**Dataset**: E-commerce Website Landing Page Experiment (`ab_data.csv` and `countries.csv`)  
**Objective**: Audit data quality, identify instrumentation anomalies and tracking mismatches, establish clean cohorts, and explore baseline user conversion behavior across time and geographic segments.
"""))

    # Imports
    cells.append(nbf.v4.new_code_cell("""import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure src modules can be imported
sys.path.append(os.path.abspath(".."))

from src.data_loader import ensure_data_downloaded, load_raw_experiment_data, load_countries_data
from src.data_cleaning import audit_raw_data, clean_experiment_data

# Set visual style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial"]
"""))

    # Section 1: Data Ingestion
    cells.append(nbf.v4.new_markdown_cell("""## 1. Data Ingestion and Provenance

We load the raw experiment records (`ab_data.csv`) and the geographic country mappings (`countries.csv`).
Each record represents a user visit with variant assignment and conversion outcome.
"""))

    cells.append(nbf.v4.new_code_cell("""ensure_data_downloaded("../data/raw")
raw_df = load_raw_experiment_data("../data/raw/ab_data.csv")
countries_df = load_countries_data("../data/raw/countries.csv")

print(f"Raw Experiment Data Shape: {raw_df.shape[0]:,} rows x {raw_df.shape[1]} columns")
print(f"Countries Mapping Shape:    {countries_df.shape[0]:,} rows x {countries_df.shape[1]} columns")
raw_df.head()
"""))

    # Section 2: Data Dictionary
    cells.append(nbf.v4.new_markdown_cell("""## 2. Data Dictionary & Schema Inspection

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `user_id` | `int64` | Unique visitor identifier |
| `timestamp` | `datetime64[ns]` | Date and UTC time of the webpage visit |
| `group` | `category` | Experimental condition (`control`, `treatment`) |
| `landing_page` | `category` | Rendered webpage version (`old_page`, `new_page`) |
| `converted` | `int64` | Binary conversion indicator (`0` = No conversion, `1` = Converted) |
| `country` | `category` | Geographic territory (`US`, `UK`, `CA`) |
"""))

    cells.append(nbf.v4.new_code_cell("""raw_df.info()
"""))

    # Section 3: Data Quality Auditing
    cells.append(nbf.v4.new_markdown_cell("""## 3. Data Quality Audit: Structural Inspection of Visitor Sessions

In web experimentation platforms, client caching, race conditions, and redirect misconfigurations frequently compromise raw telemetry.
We audit:
1. Missing or invalid outcomes (`converted` not in `{0, 1}`)
2. Unique visitor count vs. total record count
3. Visitor session frequency (single-visit vs. multi-visit users)
4. Conflicting variant assignments across sessions for the same visitor
5. Conflicting landing pages rendered across sessions for the same visitor
6. Row-level routing mismatches (`group == 'control'` on `new_page`, or `treatment` on `old_page`)
"""))

    cells.append(nbf.v4.new_code_cell("""audit_rep = audit_raw_data(raw_df)

print("=== Comprehensive Data Quality Audit Report ===")
for k, v in audit_rep.to_dict().items():
    print(f"  {k:35s}: {v}")
"""))

    cells.append(nbf.v4.new_markdown_cell("""### Structural Breakdown of Multi-Session Visitors

We investigate the **3,894 visitors** who recorded more than one session:
- **1 visitor** (`user_id = 773192`) had 2 consistent sessions in `treatment` on `new_page`.
- **1,895 visitors** were logged under conflicting experimental groups (`control` in one session, `treatment` in another).
- **1,998 visitors** were served conflicting landing pages (`old_page` in one session, `new_page` in another).
- In total, **3,893 rows** represent routing mismatches where `group` and `landing_page` disagree.
"""))

    cells.append(nbf.v4.new_code_cell("""crosstab_raw = pd.crosstab(raw_df["group"], raw_df["landing_page"], margins=True)
display(crosstab_raw)

# Identify mismatched rows
is_mismatch = (
    ((raw_df["group"] == "treatment") & (raw_df["landing_page"] == "old_page")) |
    ((raw_df["group"] == "control") & (raw_df["landing_page"] == "new_page"))
)
print(f"Total Mismatched Rows: {is_mismatch.sum():,} ({is_mismatch.mean()*100:.2f}% of raw records)")
"""))

    # Section 4: Data Cleaning Pipeline
    cells.append(nbf.v4.new_markdown_cell("""## 4. Cohort Cleaning & Methodological Framing

A common convention (e.g., in Udacity's benchmark analysis) is to filter out the 3,893 mismatched rows and retain the earliest visit for each user, producing a cohort of **290,584 unique visitors**.

> **Methodological Note**: Filtering out mismatched rows should NOT be claimed to "prevent contamination" or guarantee an unbiased causal estimate. Because users with routing errors may systematically differ from uncorrupted users, excluding them is an empirical benchmark rule that requires sensitivity validation across alternative specifications (Strictly Unambiguous, First-Touch Assignment Proxy, As-Treated).
"""))

    cells.append(nbf.v4.new_code_cell("""clean_df, _ = clean_experiment_data(raw_df)

print(f"Pre-Cleaning Row Count:  {len(raw_df):,}")
print(f"Post-Cleaning Row Count: {len(clean_df):,}")
print(f"Unique Users in Clean:   {clean_df['user_id'].nunique():,}")
print(f"Data Retention Rate:     {(len(clean_df) / len(raw_df))*100:.2f}%")

# Verify zero mismatches remain in benchmark cohort
assert (
    ((clean_df["group"] == "control") & (clean_df["landing_page"] == "new_page")).sum() == 0
)
assert (
    ((clean_df["group"] == "treatment") & (clean_df["landing_page"] == "old_page")).sum() == 0
)
print("Data validation assertions passed: Benchmark cohort is filtered and reconciled.")
"""))

    # Section 5: Group Distributions & Baseline Conversions
    cells.append(nbf.v4.new_markdown_cell("""## 5. Group Distributions & Conversion Rates

We summarize the cleaned cohorts to observe group sizes, conversion volumes, and baseline conversion rates.
"""))

    cells.append(nbf.v4.new_code_cell("""group_summary = clean_df.groupby("group", observed=False)["converted"].agg(
    Visitors="count",
    Conversions="sum",
    Conversion_Rate="mean"
).reset_index()

group_summary["Conversion_Rate_Pct"] = group_summary["Conversion_Rate"] * 100
display(group_summary)

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(group_summary["group"], group_summary["Conversion_Rate_Pct"], color=["#2B5B84", "#D95F02"], width=0.4)
ax.set_ylabel("Conversion Rate (%)", fontweight="bold")
ax.set_title("Exploratory Conversion Rate by Experiment Variant", fontweight="bold")
ax.set_ylim(0, 15)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.3, f"{yval:.2f}%", ha="center", fontweight="bold")

plt.tight_layout()
plt.show()
"""))

    # Section 6: Temporal Patterns & Novelty Effects
    cells.append(nbf.v4.new_markdown_cell("""## 6. Temporal Patterns & Novelty Effect Exploration

A common pitfall in digital experimentation is the **novelty effect**, where users initially interact more (or less) with a new interface before reverting to baseline behavior.
We plot the daily conversion rates and visitor volume across all 23 days of the test.
"""))

    cells.append(nbf.v4.new_code_cell("""clean_df["date"] = pd.to_datetime(clean_df["timestamp"]).dt.date

daily_df = clean_df.groupby(["date", "group"], observed=False).agg(
    visitors=("converted", "count"),
    conversions=("converted", "sum"),
).reset_index()
daily_df["cr_pct"] = (daily_df["conversions"] / daily_df["visitors"]) * 100

ctrl_daily = daily_df[daily_df["group"] == "control"]
treat_daily = daily_df[daily_df["group"] == "treatment"]

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(ctrl_daily["date"], ctrl_daily["cr_pct"], marker="o", color="#2B5B84", label="Control (Old Page)")
ax.plot(treat_daily["date"], treat_daily["cr_pct"], marker="s", color="#D95F02", label="Treatment (New Page)")
ax.set_title("Daily Conversion Rate Trends (Jan 2 - Jan 24, 2017)", fontweight="bold")
ax.set_ylabel("Conversion Rate (%)", fontweight="bold")
ax.set_xlabel("Date", fontweight="bold")
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
"""))

    # Section 7: Geographic Segment Exploration
    cells.append(nbf.v4.new_markdown_cell("""## 7. Geographic Segment Exploration

We merge the cleaned experiment records with the `countries.csv` dataset to check user representation and conversion behavior across territories.
"""))

    cells.append(nbf.v4.new_code_cell("""merged_df = clean_df.merge(countries_df, on="user_id", how="inner")

country_summary = merged_df.groupby(["country", "group"], observed=False).agg(
    Visitors=("converted", "count"),
    Conversions=("converted", "sum"),
    Conversion_Rate=("converted", "mean")
).reset_index()
country_summary["CR_Pct"] = country_summary["Conversion_Rate"] * 100
display(country_summary)

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(data=country_summary, x="country", y="CR_Pct", hue="group", palette=["#2B5B84", "#D95F02"], ax=ax)
ax.set_title("Conversion Rate by Country & Variant", fontweight="bold")
ax.set_ylabel("Conversion Rate (%)", fontweight="bold")
ax.set_xlabel("Country", fontweight="bold")
ax.set_ylim(0, 15)
plt.tight_layout()
plt.show()
"""))

    # Section 8: Key Insights Summary
    cells.append(nbf.v4.new_markdown_cell("""## 8. Summary of Exploratory Findings

1. **Instrumentation Quality**: 3,893 records (1.32%) contained routing mismatches. Structural inspection shows 1,895 users experienced conflicting group assignments and 1,998 users received conflicting landing pages.
2. **Benchmark Cohort**: Filtering out the 3,893 mismatched rows yields 290,584 unique visitors (145,274 control; 145,310 treatment).
3. **Conversion Baselines**: Control achieved 12.04% conversion rate; Treatment achieved 11.88% conversion rate.
4. **Temporal Stability**: Daily conversion rates oscillate consistently between 11% and 13% for both groups without evidence of extreme spikes or decay.
5. **Next Step**: Proceed to `02_experiment_analysis.ipynb` for formal statistical hypothesis testing, SRM validation, power analysis, sensitivity analysis across cohort definitions, and product decision-making.
"""))

    nb.cells = cells

    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Successfully generated {output_path}")


def create_experiment_notebook(output_path: str = "notebooks/02_experiment_analysis.ipynb"):
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.13"
        }
    }

    cells = []

    # Title & Experiment Protocol
    cells.append(nbf.v4.new_markdown_cell("""# 02. Statistical Experiment Analysis & Decision-Making

**Project**: A/B Testing & Product Experimentation Analytics  
**Role**: Senior Experimentation Analyst / Data Scientist  
**Pre-Experimental Protocol & Decision Framework**:
- **Business Question**: Does the redesigned landing page increase user conversion rate compared to the existing page?
- **Primary Metric**: User-level conversion rate ($CR = \\frac{\\text{converted users}}{\\text{total unique visitors}}$).
- **Null Hypothesis ($H_0$)**: $p_{\\text{treatment}} - p_{\\text{control}} = 0$ (The new page produces no difference in conversion).
- **Alternative Hypothesis ($H_1$)**: $p_{\\text{treatment}} - p_{\\text{control}} \\neq 0$ (Two-sided test for any significant shift).
- **Significance Level ($\\alpha$)**: $0.05$ (Two-sided test, corresponding to 95% confidence).
- **Decision Rule**: Reject $H_0$ if $p\\text{-value} < 0.05$ AND the lower bound of the 95% confidence interval is strictly greater than 0. Otherwise, fail to reject $H_0$.
"""))

    # Imports
    cells.append(nbf.v4.new_code_cell("""import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.append(os.path.abspath(".."))

from src.metrics import calculate_experiment_metrics
from src.hypothesis_testing import (
    two_proportion_z_test,
    chi_square_test,
    fishers_exact_test,
    sample_ratio_mismatch_test,
    confidence_interval_difference,
)
from src.power_analysis import calculate_mde, calculate_statistical_power, generate_power_curve
from src.bayesian_analysis import run_bayesian_ab_test
from src.database import get_connection

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial"]
"""))

    # Section 1: Load Clean Cohort
    cells.append(nbf.v4.new_markdown_cell("""## 1. Loading Cleaned Experiment Cohort

We load the verified clean cohort directly from SQLite / processed storage.
"""))

    cells.append(nbf.v4.new_code_cell("""clean_df = pd.read_csv("../data/processed/clean_experiment_data.csv")
countries_df = pd.read_csv("../data/raw/countries.csv")
metrics = calculate_experiment_metrics(clean_df)

print(f"Control Cohort Size:   {metrics.n_control:,}")
print(f"Treatment Cohort Size: {metrics.n_treatment:,}")
print(f"Total Experiment Size: {metrics.n_control + metrics.n_treatment:,}")
"""))

    # Section 2: SRM Validation
    cells.append(nbf.v4.new_markdown_cell("""## 2. Sample Ratio Mismatch (SRM) Integrity Check

Before evaluating treatment effects, we must verify that the traffic allocation mechanism was not compromised.
Under a planned 50/50 allocation, we perform a Chi-Square goodness-of-fit test.
"""))

    cells.append(nbf.v4.new_code_cell("""srm = sample_ratio_mismatch_test(
    metrics.n_control, metrics.n_treatment, expected_ratio=(0.5, 0.5), alpha=0.01
)

print(f"Observed Control:   {srm.observed_control:,} (Expected: {srm.expected_control:,.1f})")
print(f"Observed Treatment: {srm.observed_treatment:,} (Expected: {srm.expected_treatment:,.1f})")
print(f"SRM Chi-Square Statistic: {srm.chi2_stat:.5f}")
print(f"SRM p-value:             {srm.p_value:.4f}")
print(f"Result: {'SRM DETECTED - ABORT' if srm.is_srm_detected else 'SRM Test Passed (Randomization Valid)'}")
"""))

    # Section 3: Empirical Primary Metrics
    cells.append(nbf.v4.new_markdown_cell("""## 3. Empirical Primary Metric Estimates

We calculate conversion rates, absolute difference, and relative lift.
"""))

    cells.append(nbf.v4.new_code_cell("""print(f"Control Conversion Rate:   {metrics.cr_control*100:.4f}% ({metrics.conversions_control:,} / {metrics.n_control:,})")
print(f"Treatment Conversion Rate: {metrics.cr_treatment*100:.4f}% ({metrics.conversions_treatment:,} / {metrics.n_treatment:,})")
print(f"Absolute Difference:       {metrics.absolute_difference_pp:+.4f} percentage points ({metrics.absolute_difference:+.6f})")
print(f"Relative Lift:             {metrics.relative_lift_pct:+.4f}%")
print(f"Unpooled Standard Error:   {metrics.se_unpooled:.6f}")
print(f"Pooled Standard Error:     {metrics.se_pooled:.6f}")
"""))

    # Section 4: Frequentist Hypothesis Testing
    cells.append(nbf.v4.new_markdown_cell("""## 4. Frequentist Hypothesis Testing

We conduct:
1. Two-proportion pooled Z-test (Standard parametric test for binary A/B tests)
2. Pearson Chi-Square test of independence (2x2 contingency table)
3. 95% Confidence Intervals (Wald and Newcombe Score intervals)
"""))

    cells.append(nbf.v4.new_code_cell("""z_res = two_proportion_z_test(
    metrics.conversions_control, metrics.n_control,
    metrics.conversions_treatment, metrics.n_treatment,
    alternative="two-sided", pooled=True
)
print(f"Two-Proportion Pooled Z-score: {z_res.z_stat:.4f}")
print(f"Two-Sided p-value:            {z_res.p_value:.4f}")

chi2_res = chi_square_test(
    metrics.conversions_control, metrics.n_control,
    metrics.conversions_treatment, metrics.n_treatment,
    correction=False
)
print(f"Pearson Chi-Square Statistic:  {chi2_res.chi2_stat:.4f}")
print(f"Chi-Square p-value:            {chi2_res.p_value:.4f}")

ci_wald = confidence_interval_difference(
    metrics.conversions_control, metrics.n_control,
    metrics.conversions_treatment, metrics.n_treatment,
    confidence_level=0.95, method="wald"
)
ci_score = confidence_interval_difference(
    metrics.conversions_control, metrics.n_control,
    metrics.conversions_treatment, metrics.n_treatment,
    confidence_level=0.95, method="score"
)

print(f"95% Wald CI for (p_treat - p_ctrl):  [{ci_wald.lower_pp:+.4f}%, {ci_wald.upper_pp:+.4f}%] pp")
print(f"95% Score CI for (p_treat - p_ctrl): [{ci_score.lower_pp:+.4f}%, {ci_score.upper_pp:+.4f}%] pp")
"""))

    # Section 5: Statistical Power & MDE
    cells.append(nbf.v4.new_markdown_cell("""## 5. Statistical Power Analysis & Minimum Detectable Effect (MDE)

To contextualize why the effect was not significant, we calculate the Minimum Detectable Effect (MDE) under $\\alpha = 0.05$ and $80\\%$ power, and evaluate post-hoc power for the observed lift.
"""))

    cells.append(nbf.v4.new_code_cell("""mde_res = calculate_mde(baseline_cr=metrics.cr_control, sample_size_per_group=metrics.n_control, alpha=0.05, power=0.80)
print(f"Prospective MDE (at 80% power): {mde_res.mde_relative_pct:.2f}% relative ({mde_res.mde_absolute_pp:.4f} percentage points)")

observed_power = calculate_statistical_power(
    baseline_cr=metrics.cr_control,
    effect_absolute=metrics.absolute_difference,
    sample_size_per_group=metrics.n_control,
    alpha=0.05
)
print(f"Post-hoc Power to detect observed effect (-0.16 pp): {observed_power*100:.2f}%")

# Generate power curve
power_curve = generate_power_curve(metrics.cr_control, metrics.n_control)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(power_curve["relative_lift_pct"], power_curve["power"] * 100, color="#1B9E77", lw=2, label="Power Curve (n = 145,274)")
ax.axhline(80, color="#E7298A", linestyle="--", label="Target Power (80%)")
ax.axvline(mde_res.mde_relative_pct, color="#7570B3", linestyle=":", label=f"MDE = {mde_res.mde_relative_pct:.2f}%")
ax.set_title("Statistical Power Curve vs. Relative Lift", fontweight="bold")
ax.set_xlabel("Relative Lift in Conversion Rate (%)", fontweight="bold")
ax.set_ylabel("Power (%)", fontweight="bold")
ax.legend()
plt.tight_layout()
plt.show()
"""))

    # Section 6: Heterogeneity & Covariate Modeling
    cells.append(nbf.v4.new_markdown_cell("""## 6. Heterogeneity & Segment Interaction Modeling

We test whether the treatment effect varies across geographic territories using Logistic Regression with interaction terms:
$$\\text{logit}(p) = \\beta_0 + \\beta_1 \\text{Treatment} + \\beta_2 \\text{Country} + \\beta_3 (\\text{Treatment} \\times \\text{Country})$$
"""))

    cells.append(nbf.v4.new_code_cell("""merged = clean_df.merge(countries_df, on="user_id", how="inner")
merged["treatment"] = (merged["group"] == "treatment").astype(int)

# Logistic regression with interaction
logit_model = smf.logit("converted ~ treatment * C(country)", data=merged).fit()
display(logit_model.summary())
"""))

    # Section 7: Bayesian Inference
    cells.append(nbf.v4.new_markdown_cell("""## 7. Bayesian A/B Testing: Beta-Binomial Conjugate Analysis

Frequentist tests tell us $P(\\text{Data} \\mid H_0)$. Bayesian inference directly answers the product question:
**What is the probability that the new page is superior to the old page?**
"""))

    cells.append(nbf.v4.new_code_cell("""bayes_res, s_c, s_t, s_diff = run_bayesian_ab_test(
    metrics.conversions_control, metrics.n_control,
    metrics.conversions_treatment, metrics.n_treatment,
    n_samples=200000, seed=42
)

print(f"Posterior Mean Control CR:    {bayes_res.posterior_mean_ctrl*100:.4f}%")
print(f"Posterior Mean Treatment CR:  {bayes_res.posterior_mean_treat*100:.4f}%")
print(f"P(Treatment > Control):       {bayes_res.prob_treatment_beats_control*100:.2f}%")
print(f"P(Control > Treatment):       {(1.0 - bayes_res.prob_treatment_beats_control)*100:.2f}%")
print(f"Expected Loss (Deploy Treat): {bayes_res.expected_loss_treatment*100:.4f} percentage points")
print(f"95% Bayesian Credible Interval: [{bayes_res.credible_interval_95_lower_pp:+.4f}%, {bayes_res.credible_interval_95_upper_pp:+.4f}%] pp")

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(s_diff * 100, bins=80, density=True, color="#7570B3", alpha=0.7)
ax.axvline(0, color="black", linestyle="--", label="Zero Effect")
ax.axvline(bayes_res.credible_interval_95_lower_pp, color="#333333", linestyle=":", label=f"95% HDI: [{bayes_res.credible_interval_95_lower_pp:.2f}%, {bayes_res.credible_interval_95_upper_pp:.2f}%]")
ax.axvline(bayes_res.credible_interval_95_upper_pp, color="#333333", linestyle=":")
ax.set_title(f"Posterior Difference Distribution: P(Treatment > Control) = {bayes_res.prob_treatment_beats_control*100:.1f}%", fontweight="bold")
ax.set_xlabel("Conversion Rate Difference (Treatment - Control, pp)", fontweight="bold")
ax.set_ylabel("Posterior Density", fontweight="bold")
ax.legend()
plt.tight_layout()
plt.show()
"""))

    # Section 8: Final Product Recommendation
    cells.append(nbf.v4.new_markdown_cell("""## 8. Final Product Recommendation & Decision

### Recommendation: **No demonstrated conversion improvement**

1. **Statistical Evidence**:
   - Two-proportion Z-test p-value is **0.1899**, which exceeds the $\\alpha = 0.05$ threshold. We fail to reject the null hypothesis $H_0$.
   - The 95% Confidence Interval for the difference in conversion rates is **[-0.39 pp, +0.08 pp]**.
   - The interval includes zero and is compatible with both modest harm and a small benefit; it does not prove the true effect is bounded at the displayed endpoint.
2. **Bayesian Risk Assessment**:
   - Under the stated Beta(1, 1) priors and this cohort, the posterior probability that treatment is better is approximately **9.53%**. This is model-conditional evidence, not certainty.
   - Launching treatment incurs an expected loss of **0.16 percentage points** of conversion.
3. **Engineering & Business Practicality**:
   - The experiment does not establish a conversion improvement. Consider design research and a better-instrumented follow-up experiment before deciding on rollout.
4. **Actionable Next Steps**:
   - Do not claim a conversion lift from this experiment; retaining the current page pending further evidence is a cautious option.
   - Investigate assignment/exposure inconsistencies and conduct qualitative research before a follow-up experiment.
"""))

    nb.cells = cells

    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Successfully generated {output_path}")


def execute_notebook(notebook_path: str):
    """Executes a notebook in place and saves its outputs."""
    print(f"Executing {notebook_path}...")
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": os.path.dirname(os.path.abspath(notebook_path))}})
    client.execute()

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Finished executing {notebook_path}")


if __name__ == "__main__":
    create_eda_notebook()
    create_experiment_notebook()
    execute_notebook("notebooks/01_exploratory_data_analysis.ipynb")
    execute_notebook("notebooks/02_experiment_analysis.ipynb")
