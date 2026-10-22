-- Sample Ratio Mismatch (SRM) Goodness-of-Fit Query
-- Assumes 50/50 allocation ratio
--
-- METHODOLOGICAL NOTE:
-- A non-significant SRM test (p >= alpha) indicates that observed sample counts
-- do not depart significantly from the 50/50 target ratio in the analyzed population.
-- It does NOT prove that the randomization was valid, or that there was no selective
-- attrition or upstream telemetry failure.

WITH counts AS (
    SELECT
        SUM(CASE WHEN group_name = 'control' THEN 1 ELSE 0 END) AS obs_control,
        SUM(CASE WHEN group_name = 'treatment' THEN 1 ELSE 0 END) AS obs_treatment,
        COUNT(*) AS total_visitors
    FROM clean_events
),
srm_calc AS (
    SELECT
        obs_control,
        obs_treatment,
        total_visitors,
        total_visitors * 0.5 AS exp_control,
        total_visitors * 0.5 AS exp_treatment,
        (POWER(obs_control - (total_visitors * 0.5), 2) / (total_visitors * 0.5)) +
        (POWER(obs_treatment - (total_visitors * 0.5), 2) / (total_visitors * 0.5)) AS chi2_statistic
    FROM counts
)
SELECT
    obs_control,
    obs_treatment,
    total_visitors,
    exp_control,
    exp_treatment,
    ROUND(chi2_statistic, 6) AS chi2_statistic,
    CASE 
        WHEN chi2_statistic > 6.634897 THEN 'FLAG_POTENTIAL_SRM_P_LT_01'
        ELSE 'NO_SRM_DETECTED_AT_01_LEVEL'
    END AS srm_status
FROM srm_calc;
