# Dataset Documentation, Provenance & Quality Audit

## Quick Summary

This project analyzes an e-commerce landing-page A/B test dataset originally used in Udacity's Data Analyst Nanodegree curriculum.

- **Raw records:** 294,478
- **Unique visitors:** 290,584
- **Data-quality concerns:** conflicting group assignments and landing-page mismatches among repeat visitors
- **Analysis approach:** compare alternative visitor-level data-handling specifications and disclose their limitations
- **Licensing:** formal third-party dataset redistribution rights have not been verified

## 1. Overview & Provenance

The dataset was originally released as part of the Udacity curriculum project *Analyze A/B Test Results*. The files are mirrored in a public GitHub repository.

### Primary dataset: `ab_data.csv`

- Source: [ab_data.csv](https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv)
- Reported file size: 15,901,933 bytes
- Reported SHA-256: `d56e2accec25e99ac21cb3d76c5df516dd19cc7a77c14c9014f94e1ea1301beb`
- Raw records: 294,478
- Unique visitor IDs: 290,584

### Secondary dataset: `countries.csv`

- Source: [countries.csv](https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv)
- Reported file size: 2,905,856 bytes
- Reported SHA-256: `c011d0503d305c295327cd9dff9c37bb62a5f9ef4b356bcdaf7deca20d55e45b`
- Records: 290,584
- Fields: `user_id`, `country`

### Licensing and usage rights

The source is publicly downloadable, but a formal license granting unrestricted redistribution or public-domain status has not been verified. Download availability does not establish permission to redistribute the dataset. Review the upstream source's terms before republishing the data.

## 2. Raw Schema

### `ab_data.csv`

| Column | Description |
|---|---|
| `user_id` | Visitor identifier |
| `timestamp` | Recorded page-view timestamp |
| `group` | Recorded experimental group: `control` or `treatment` |
| `landing_page` | Recorded page: `old_page` or `new_page` |
| `converted` | Binary conversion indicator: `0` or `1` |

### `countries.csv`

| Column | Description |
|---|---|
| `user_id` | Visitor identifier used to join datasets |
| `country` | Country code: `US`, `UK`, or `CA` |

## 3. Data-Quality Audit

The source data contains 294,478 rows and 290,584 unique visitors. There are 3,894 visitors with repeated records.

The original audit identified:
- 1 visitor with consistent repeated records.
- 1,895 visitors with conflicting recorded group assignments.
- 1,998 visitors with a stable recorded group but conflicting landing-page exposure.
- 3,893 rows where the recorded group and landing page do not match the expected mapping.

These categories describe recorded data patterns. They do not, by themselves, establish why the inconsistencies occurred or prove the original random assignment.

<details>
<summary>View detailed anomaly interpretation</summary>

### Conflicting group assignments

Some repeat visitors have records in both the `control` and `treatment` groups. Possible explanations include unstable bucketing or cross-device behavior, but the dataset alone does not establish the cause.

### Conflicting landing-page exposure

Some repeat visitors have records for both `old_page` and `new_page`. This creates uncertainty about which version they were exposed to and complicates causal interpretation.

### Row-level routing mismatches

A recorded group and page mismatch should not automatically be treated as proof of a particular assignment error. The original assignment log is unavailable, so the authoritative assignment cannot be independently verified.

</details>

## 4. Analysis Specifications and Trade-offs

The project compares four ways of handling the data. Their exact implementation and output sample sizes should be checked against the analysis code and final report.

| Specification | Approach | Important limitation |
|---|---|---|
| Strictly unambiguous cohort | Excludes visitors identified as ambiguous under the cleaning rules | Exclusion can introduce selection bias |
| Benchmark matched filter | Removes rows whose recorded group and page do not match | Repeat visitors may have seen both versions |
| First-touch assignment proxy | Uses the earliest recorded group and aggregates conversion at visitor level | Not verified intention-to-treat because authoritative assignment logs are unavailable |
| As-treated, first page | Uses the first recorded page exposure and aggregates conversion at visitor level | Does not preserve the original randomized comparison automatically |

These specifications are sensitivity analyses, not proof that any one estimate is unbiased. Results should be interpreted in light of the assumptions behind each rule.

## 5. Downloading the Data

From the repository root, run the following commands in PowerShell:

```powershell
New-Item -ItemType Directory -Force data/raw

curl.exe -fL -o data/raw/ab_data.csv "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv"

curl.exe -fL -o data/raw/countries.csv "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv"
```

### Verify the files

The hashes listed above are reference values. After downloading, calculate the SHA-256 hashes locally and compare them with the documented values before using the files.

The availability of these URLs does not establish permission to redistribute the dataset.

## 6. Interpretation Caveat

The dataset does not provide a verified authoritative assignment log. Conflicting assignments, page mismatches, and exclusion rules may affect the estimated treatment effect. Filtering ambiguous records does not automatically eliminate bias.

For the experiment's statistical results and business interpretation, see the [final experiment report](../reports/final_experiment_report.md).

---

**Purpose:** educational portfolio analysis of data quality, experimentation methodology, and statistical uncertainty.
