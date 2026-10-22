# A/B Testing & Product Experimentation Analytics

A reproducible portfolio project analyzing an educational e-commerce landing-page experiment using Python, Pandas, SciPy, Statsmodels, SQLite, Matplotlib, Bayesian Beta-Binomial modeling, and Pytest.

## Executive summary

The benchmark matched-filter cohort contains 290,584 unique visitors. Control conversion was **12.0386%** (17,489/145,274) and treatment conversion was **11.8808%** (17,264/145,310), a treatment-minus-control difference of **-0.1578 percentage points** (relative lift -1.3110%). The two-sided pooled two-proportion test returned **p = 0.1899**, and the approximate 95% Wald confidence interval was **[-0.3938, +0.0781] percentage points**. The experiment does not establish a statistically significant conversion improvement; this does not prove the true effect is zero or that the redesign is harmful.

The raw data contain repeated visitor records and inconsistencies between recorded group and page. This repository compares four cohort specifications. Because an independent authoritative assignment log is unavailable, the benchmark matched-filter cohort is not guaranteed to provide an unbiased intention-to-treat estimate. Read the [final report](reports/final_experiment_report.md) for methodology, sensitivity analysis, uncertainty, and limitations.

## Key results

| Metric | Result |
|---|---:|
| Raw records | 294,478 |
| Unique visitor IDs | 290,584 |
| Control conversion rate | 12.0386% |
| Treatment conversion rate | 11.8808% |
| Treatment minus control | -0.1578 percentage points |
| Two-proportion Z-test | z = -1.3109, p = 0.1899 |
| 95% Wald confidence interval | approximately [-0.3938, +0.0781] pp |
| SRM check on benchmark cohort | p = 0.9468; no SRM detected in this cohort |
| Bayesian P(treatment > control) | approximately 9.53% under Beta(1,1) priors |
| Power-analysis MDE | approximately 0.3383 pp at 80% target power |

## Project structure

```text
ab-testing-product-analytics/
├── data/README.md                  # Provenance, data dictionary, checksums, caveats
├── notebooks/                      # EDA and experiment analysis notebooks
├── reports/final_experiment_report.md
├── reports/figures/                # Generated figures
├── scripts/build_notebooks.py      # Notebook generation utility
├── sql/                            # Schema, quality audit, metrics, SRM, segments
├── src/                            # Cleaning, metrics, tests, power, Bayesian, database, plots
├── tests/                           # Unit and integration tests
├── requirements.txt
└── README.md
```

## Setup and run

Requires Python 3.10 or newer and Git. From the repository root:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -v
python -m src.run_pipeline
```

macOS/Linux activation:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -v
python -m src.run_pipeline
```

The pipeline reads `data/raw/ab_data.csv` and `data/raw/countries.csv`, creates derived data and a local SQLite database, and regenerates figures. If the raw files are absent, the loader attempts to download them from the URLs documented in `data/README.md`. Verify upstream terms before redistributing the third-party dataset.

To regenerate notebooks, run:

```bash
python scripts/build_notebooks.py
```

## Main technical components

- Visitor-level data-quality audit and four cohort/sensitivity specifications.
- Conversion metrics, two-proportion Z-test, Pearson chi-square, Fisher exact test, confidence intervals, and sample-ratio mismatch check.
- Two-sided statistical power and minimum detectable effect calculations.
- Beta-Binomial posterior analysis with reproducible Monte Carlo sampling.
- SQLite analytics and Python/SQL metric reconciliation.
- Automated tests for statistical functions, cleaning rules, Bayesian calculations, power analysis, and database reconciliation.

## Interpretation cautions

- Nonsignificance is not proof of no effect.
- No SRM detected does not prove randomization or data collection was unbiased.
- Nonsignificant segment interactions do not prove homogeneous treatment effects.
- The annual traffic impact shown in the report is a hypothetical scenario, not an observed business outcome.
- The third-party dataset's formal license could not be verified from the included files. The root MIT license applies to original project code only, not the third-party data.

## Licensing

Original code in this repository is licensed under the MIT License in `LICENSE`. The dataset is third-party material associated with an educational Udacity project; its formal redistribution license remains unverified. Check the upstream source terms before publishing raw CSVs publicly.
