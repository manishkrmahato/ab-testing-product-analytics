-- Primary Experiment Metrics Computation Query
-- Reconciles with Python metrics module

WITH group_aggregates AS (
    SELECT
        group_name,
        COUNT(*) AS total_visitors,
        SUM(converted) AS total_conversions,
        1.0 * SUM(converted) / COUNT(*) AS conversion_rate
    FROM clean_events
    GROUP BY group_name
),
pivoted AS (
    SELECT
        MAX(CASE WHEN group_name = 'control' THEN total_visitors END) AS n_control,
        MAX(CASE WHEN group_name = 'control' THEN total_conversions END) AS conv_control,
        MAX(CASE WHEN group_name = 'control' THEN conversion_rate END) AS cr_control,
        MAX(CASE WHEN group_name = 'treatment' THEN total_visitors END) AS n_treatment,
        MAX(CASE WHEN group_name = 'treatment' THEN total_conversions END) AS conv_treatment,
        MAX(CASE WHEN group_name = 'treatment' THEN conversion_rate END) AS cr_treatment
    FROM group_aggregates
)
SELECT
    n_control,
    conv_control,
    ROUND(cr_control, 6) AS cr_control,
    ROUND(cr_control * 100.0, 4) AS cr_control_pct,
    n_treatment,
    conv_treatment,
    ROUND(cr_treatment, 6) AS cr_treatment,
    ROUND(cr_treatment * 100.0, 4) AS cr_treatment_pct,
    ROUND(cr_treatment - cr_control, 6) AS absolute_difference,
    ROUND((cr_treatment - cr_control) * 100.0, 4) AS absolute_difference_pp,
    ROUND(((cr_treatment - cr_control) / cr_control) * 100.0, 4) AS relative_lift_pct
FROM pivoted;
