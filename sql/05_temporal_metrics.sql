-- Daily and Cumulative Temporal Metrics Query

WITH daily_stats AS (
    SELECT
        DATE(timestamp) AS event_date,
        group_name,
        COUNT(*) AS daily_visitors,
        SUM(converted) AS daily_conversions,
        ROUND(1.0 * SUM(converted) / COUNT(*), 6) AS daily_cr
    FROM clean_events
    GROUP BY DATE(timestamp), group_name
)
SELECT
    event_date,
    MAX(CASE WHEN group_name = 'control' THEN daily_visitors END) AS ctrl_visitors,
    MAX(CASE WHEN group_name = 'control' THEN daily_conversions END) AS ctrl_conversions,
    MAX(CASE WHEN group_name = 'control' THEN daily_cr END) AS ctrl_cr,
    MAX(CASE WHEN group_name = 'treatment' THEN daily_visitors END) AS treat_visitors,
    MAX(CASE WHEN group_name = 'treatment' THEN daily_conversions END) AS treat_conversions,
    MAX(CASE WHEN group_name = 'treatment' THEN daily_cr END) AS treat_cr,
    ROUND(
        MAX(CASE WHEN group_name = 'treatment' THEN daily_cr END) - 
        MAX(CASE WHEN group_name = 'control' THEN daily_cr END), 6
    ) AS daily_diff
FROM daily_stats
GROUP BY event_date
ORDER BY event_date;
