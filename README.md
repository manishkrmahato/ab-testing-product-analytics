# A/B Testing & Product Experimentation Analytics

An end-to-end data science project evaluating an e-commerce landing-page experiment using Python, SQL, statistical hypothesis testing, confidence intervals, power analysis, and Bayesian methods.

The project focuses on a core product analytics question: **Did the redesigned landing page improve conversion rates, and is the evidence strong enough to support a rollout decision?**

## Key Findings

The benchmark analysis produced the following results:

| Metric | Result |
|---|---:|
| Raw records | 294,478 |
| Unique visitors in raw data | 290,584 |
| Control conversion rate | 12.0386% |
| Treatment conversion rate | 11.8808% |
| Treatment minus control | −0.1578 percentage points |
| Two-proportion Z-test p-value | 0.1899 |
| 95% confidence interval for the difference | −0.3938 to +0.0781 percentage points |

The observed conversion rate was slightly lower for the treatment group. The test did not provide statistically significant evidence of an improvement at the 5% significance level.

**Important:** The dataset contains inconsistent group assignments and landing-page exposures. The findings must be interpreted alongside the documented data-quality issues and sensitivity analyses. The benchmark result alone does not establish that the redesign caused a decrease in conversions.

## Technologies Used

- **Python:** Data processing and statistical analysis
- **Pandas and NumPy:** Data cleaning and numerical computation
- **SciPy:** Statistical hypothesis testing
- **SQLite and SQL:** Data storage, querying, and metric reconciliation
- **Matplotlib:** Data visualization
- **Jupyter Notebook:** Exploratory analysis and experiment evaluation
- **Pytest:** Automated testing

## Project Structure

```text
ab-testing-product-analytics/
├── data/
│   └── README.md
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb
│   └── 02_experiment_analysis.ipynb
├── reports/
│   ├── figures/
│   └── final_experiment_report.md
├── scripts/
│   └── build_notebooks.py
├── sql/
│   ├── 01_schema.sql
│   ├── 02_data_quality_audit.sql
│   ├── 03_experiment_metrics.sql
│   ├── 04_srm_check.sql
│   ├── 05_temporal_metrics.sql
│   └── 06_segment_metrics.sql
├── src/
│   ├── data_loader.py
│   ├── data_cleaning.py
│   ├── database.py
│   ├── metrics.py
│   ├── hypothesis_testing.py
│   ├── power_analysis.py
│   ├── bayesian_analysis.py
│   ├── visualization.py
│   └── run_pipeline.py
├── tests/
├── requirements.txt
├── LICENSE
└── README.md
```

## Analysis Workflow

1. **Data ingestion and quality auditing:** Examine visitor records, repeated observations, inconsistent assignments, and landing-page mismatches.
2. **Exploratory data analysis:** Investigate conversion rates, visitor distributions, daily trends, and geographic segments.
3. **Frequentist inference:** Calculate conversion-rate differences, hypothesis tests, and confidence intervals.
4. **Experiment diagnostics:** Evaluate sample-ratio mismatch and investigate data-quality concerns.
5. **Power and MDE analysis:** Assess statistical power and the minimum detectable effect under stated assumptions.
6. **Bayesian analysis:** Estimate posterior conversion rates, the probability that treatment performs better, and decision uncertainty.
7. **Sensitivity analysis:** Compare results under alternative visitor-level data-handling specifications.
8. **Reporting and testing:** Generate visualizations and reports, and validate calculations with automated tests.

## Visualizations

The repository includes figures for:

- Conversion rates and confidence intervals
- Daily and cumulative conversion trends
- Geographic segment comparisons
- Statistical power and minimum detectable effect
- Bayesian posterior distributions
- Sensitivity analysis across alternative data-handling specifications

See [`reports/figures/`](reports/figures/) and the [final experiment report](reports/final_experiment_report.md).

## Getting Started

### 1. Requirements

Install a supported Python version and Git.

Clone the repository:

```bash
git clone https://github.com/manishkrmahato/ab-testing-product-analytics.git
cd ab-testing-product-analytics
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Obtain the dataset

The raw CSV files are not included in this repository. Follow the instructions and review the provenance information in [`data/README.md`](data/README.md).

The documented upstream files are:

- [`ab_data.csv`](https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv)
- [`countries.csv`](https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv)

Download the files into `data/raw/` before running the pipeline. From the repository root, in PowerShell:

```powershell
New-Item -ItemType Directory -Force data/raw

curl.exe -fL -o data/raw/ab_data.csv "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv"

curl.exe -fL -o data/raw/countries.csv "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv"
```

Verify the files against the SHA-256 hashes documented in `data/README.md` before analyzing them.

**Licensing note:** The formal license and redistribution rights for the third-party dataset have not been verified. Download availability does not establish permission to redistribute it.

### 5. Run the analysis pipeline

From the repository root:

```bash
python -m src.run_pipeline
```

### 6. Run the tests

```bash
python -m pytest -v
```

The pipeline and tests may depend on the raw data being downloaded first. See the data documentation and source code for the exact input requirements.

## Reproducibility and Testing

The project includes automated tests for data cleaning, metrics, hypothesis testing, power analysis, Bayesian calculations, and SQL/Python reconciliation.

The reported validation run completed with 36 passing tests and a successful pipeline execution. Results can vary if the source data, dependencies, or analysis specifications change.

## Limitations

- The dataset contains visitors with conflicting group assignments and/or landing-page exposures.
- A verified authoritative assignment log is unavailable, so the first-touch assignment analysis is a proxy rather than a confirmed intention-to-treat analysis.
- Filtering ambiguous records may introduce selection bias.
- Nonsignificant results do not establish that the true effect is zero.
- Segment analyses are subject to uncertainty and should not be interpreted as proof that treatment effects are identical across countries.
- Revenue, average order value, and other downstream business outcomes are not available in the dataset.
- The formal third-party dataset license remains unverified.

These limitations are considered when interpreting the findings and making recommendations.

## Detailed Documentation

- [Dataset Documentation, Provenance & Quality Audit](data/README.md)
- [Final Experiment Report](reports/final_experiment_report.md)
- [Exploratory Data Analysis Notebook](notebooks/01_exploratory_data_analysis.ipynb)
- [Experiment Analysis Notebook](notebooks/02_experiment_analysis.ipynb)

## License

The repository's `LICENSE` file describes the intended license for the project code. It does not grant ownership of or additional rights to the third-party dataset. Refer to [`data/README.md`](data/README.md) for source and licensing caveats.

---

**Author:** Manish Kumar Mahato

**GitHub:** [manishkrmahato/ab-testing-product-analytics](https://github.com/manishkrmahato/ab-testing-product-analytics)
