-- Country Segment Breakdown Query

SELECT
    u.country,
    c.group_name,
    COUNT(*) AS total_users,
    SUM(c.converted) AS total_conversions,
    ROUND(1.0 * SUM(c.converted) / COUNT(*), 6) AS conversion_rate,
    ROUND(100.0 * SUM(c.converted) / COUNT(*), 4) AS conversion_rate_pct
FROM clean_events c
JOIN user_countries u ON c.user_id = u.user_id
GROUP BY u.country, c.group_name
ORDER BY u.country, c.group_name;
