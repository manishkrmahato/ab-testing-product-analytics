# A/B Testing & Product Experimentation Analytics — Final Report

## Executive summary

This project analyzes a public educational e-commerce landing-page experiment using Python, Pandas, SciPy, Statsmodels, SQLite, and Bayesian Beta-Binomial modeling. The primary analysis follows the project's benchmark matched-filter cohort: it removes rows whose recorded `group` conflicts with `landing_page`, then retains the earliest remaining record per visitor. Because some visitors have conflicting assignment or exposure records, this cohort is a benchmark analysis—not a guaranteed unbiased intention-to-treat estimate. Sensitivity analyses are included to show how results vary under alternative visitor-level rules.

**Primary-cohort result:** control conversion was 12.0386% (17,489/145,274) and treatment conversion was 11.8808% (17,264/145,310). The treatment-minus-control difference was -0.1578 percentage points (relative lift -1.3110%). The two-sided pooled two-proportion test gave z = -1.3109, p = 0.1899. The 95% Wald interval for the difference was approximately [-0.3938, +0.0781] percentage points. The interval includes zero, so this experiment does not establish a statistically significant conversion improvement.

**Decision framing:** based on this dataset alone, there is insufficient evidence to justify launching the redesign for conversion-rate improvement. Retaining the existing page while investigating the design and, if appropriate, running a better-instrumented experiment is a cautious recommendation—not proof that the redesign is harmful.

## 1. Question and hypotheses

- **Question:** Does the redesigned page change visitor-level conversion rate compared with the existing page?
- **Primary metric:** binary conversion rate per visitor.
- **Null hypothesis:** treatment conversion rate minus control conversion rate equals zero.
- **Alternative:** the difference is non-zero (two-sided).
- **Significance level:** 0.05.
- **Effect direction:** treatment minus control; negative values favor control.

## 2. Data provenance and quality

The dataset is associated with Udacity's educational project *Analyze A/B Test Results* and is mirrored in public repositories. The included data documentation records source URLs and file hashes. **A formal license for the third-party dataset could not be verified from the files available with this project.** The MIT license applies to project-authored code only; it does not grant rights to the third-party data. Verify the upstream terms before redistributing the CSV files publicly.

The raw file contains 294,478 rows and 290,584 distinct visitor IDs. The audit identifies repeated visitor records, group-assignment conflicts, and page/group mismatches. In this dataset, 3,893 rows are mismatches: 1,928 control-group rows record `new_page`, and 1,965 treatment-group rows record `old_page`. Repeated visitor records mean row-level and visitor-level counts must not be conflated.

### Cohort definitions

The code compares four specifications:

1. **Benchmark matched filter:** removes mismatched rows and keeps the earliest remaining record per visitor.
2. **Strictly unambiguous cohort:** removes any visitor with a routing mismatch.
3. **First-touch assignment sensitivity:** uses the earliest recorded group and aggregates conversion as the maximum observed visitor outcome.
4. **First-page-viewed sensitivity:** assigns a visitor based on the first recorded landing page and aggregates conversion as the maximum observed outcome.

The raw dataset does not provide an independently verified assignment log. Consequently, the first-touch cohort is an *assignment-proxy sensitivity analysis*, not proof of true randomized assignment. The as-treated analysis is observational with respect to page received and should not be interpreted as preserving randomization. Excluding mismatched records may introduce selection bias if mismatch or repeat visits relate to user behavior. The alternative specifications help describe sensitivity but cannot eliminate this limitation.

## 3. Primary conversion analysis

| Metric | Control | Treatment | Treatment minus control |
|---|---:|---:|---:|
| Visitors | 145,274 | 145,310 | +36 |
| Conversions | 17,489 | 17,264 | -225 |
| Conversion rate | 12.0386% | 11.8808% | -0.1578 percentage points |

- Two-proportion pooled Z-test: z = -1.3109, p = 0.1899.
- Pearson chi-square test (without continuity correction): chi-square = 1.7185, p = 0.1899.
- Fisher exact test: two-sided p approximately 0.1905; odds ratio approximately 0.9851 under the code's treatment/control odds orientation.
- 95% Wald interval: approximately [-0.3938, +0.0781] percentage points.
- 95% score interval: see the pipeline's independently calculated output; close rounded values do not mean the methods are mathematically identical.

The p-value is above 0.05 and the interval includes zero. This means the data do not provide sufficient evidence to reject the no-difference null under this analysis and its assumptions. It does **not** prove that the true effect is zero. The interval remains compatible with both a modest decrease and a small increase in conversion.

## 4. Allocation check (SRM)

For the benchmark cleaned cohort, the observed counts are 145,274 control and 145,310 treatment, compared with 145,292 expected per arm under a 50:50 split. The chi-square goodness-of-fit statistic is approximately 0.00446 with p = 0.9468. **No sample-ratio mismatch was detected in this analyzed cohort.** This check does not prove assignment was valid, rule out selective attrition, or resolve the raw-data assignment/exposure inconsistencies described above.

## 5. Sensitivity analysis

The current pipeline compares these visitor-level specifications:

| Specification | Control N | Treatment N | Control CR | Treatment CR | Difference (pp) | p-value |
|---|---:|---:|---:|---:|---:|---:|
| Benchmark matched filter | 145,274 | 145,310 | 12.0386% | 11.8808% | -0.1578 | 0.1899 |
| Strictly unambiguous cohort | 143,293 | 143,398 | 12.0173% | 11.8726% | -0.1448 | 0.2320 |
| First-touch assignment proxy | 145,294 | 145,290 | 12.1732% | 12.0352% | -0.1380 | 0.2541 |
| First page viewed (as-treated) | 145,293 | 145,291 | 12.1981% | 12.0104% | -0.1877 | 0.1208 |

All four specifications show a negative point estimate and none reaches the 0.05 significance threshold. Because the specifications make different assumptions about assignment, exposure, and visitor outcomes, they are not interchangeable estimates of the same causal quantity. Similar direction across these analyses is reassuring descriptively but does not repair the absence of a verified assignment log.

## 6. Country segments and time trends

Country-level conversion rates and logistic-regression interaction results are exploratory. Nonsignificant interactions do not establish that effects are identical across countries, and they do not rule out Simpson's paradox. Multiple subgroup comparisons can increase false-positive risk; interpret segment findings cautiously. Daily and cumulative charts are descriptive and should not be used to infer absence of novelty effects without a prespecified temporal analysis.

## 7. Power and minimum detectable effect

At a baseline conversion rate near 12.04%, 145,274 users per group, alpha = 0.05, and target power = 80%, the normal-approximation MDE is approximately 0.3383 percentage points (about 2.81% relative). The corrected two-sided power function returns approximately 5% at a zero effect, as expected under the null, and approximately 25.75% at the observed absolute effect under its normal-approximation assumptions. The MDE is a planning threshold, not a boundary separating real effects from noise. Observed/post-hoc power is not used as evidence for or against the null hypothesis.

## 8. Bayesian analysis

Using independent Beta(1, 1) priors and 200,000 reproducible Monte Carlo draws, the pipeline estimates posterior mean conversion rates of approximately 12.0392% for control and 11.8813% for treatment. The posterior probability that treatment conversion exceeds control is approximately 9.53%; the posterior mean difference is negative. These results are conditional on the chosen cohort, likelihood, and prior. They are not the same quantity as a frequentist p-value and do not establish certainty that treatment will underperform.

## 9. Illustrative business impact

If—purely as an illustration—annual traffic were 5,000,000 unique visitors and the observed point estimate transported unchanged to that population, the estimated difference would correspond to about 7,890 fewer conversions per year. Scaling the primary 95% interval gives an approximate range from 19,690 fewer to 3,905 more conversions. This is a hypothetical scenario, not a measured or guaranteed outcome; the interval includes potential benefit and harm, and the analysis has assignment-quality limitations.

## 10. Recommendation and limitations

**Recommendation:** do not claim a conversion lift from this experiment. Retain the current page unless broader business evidence supports the redesign, investigate the assignment/exposure discrepancies, and consider a new experiment with reliable assignment logs, a prespecified analysis plan, and an agreed primary metric. The data do not prove the new page is harmful; they do not establish an improvement either.

Key limitations:
- No independent authoritative assignment log is available in the included dataset.
- The matched-filter and strict cohorts may be subject to selection bias.
- Conversion is binary; revenue, order value, and longer-term outcomes are unavailable.
- Country and temporal analyses are exploratory.
- The annual traffic scenario is hypothetical.
- Formal third-party dataset licensing remains unverified.

## Reproducibility

From the repository root, install `requirements.txt`, then run:

```bash
python -m pytest -v
python -m src.run_pipeline
```

The pipeline regenerates the cleaned cohort, SQLite database, and report figures from the raw CSVs. The included test suite checks core calculations, data cleaning, Bayesian calculations, power analysis, and SQL/Python reconciliation. Passing tests validate tested code paths; they do not by themselves prove the causal assumptions are satisfied.
