-- Data Quality Audit Queries: Detailed Visitor and Session Breakdown

-- 1. Total record volume and unique visitor count
SELECT 
    COUNT(*) AS total_records,
    COUNT(DISTINCT user_id) AS unique_visitors,
    COUNT(*) - COUNT(DISTINCT user_id) AS repeat_session_records
FROM raw_events;

-- 2. Null and boundary validation
SELECT
    SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS null_user_ids,
    SUM(CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END) AS null_timestamps,
    SUM(CASE WHEN group_name IS NULL THEN 1 ELSE 0 END) AS null_groups,
    SUM(CASE WHEN landing_page IS NULL THEN 1 ELSE 0 END) AS null_landing_pages,
    SUM(CASE WHEN converted NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_conversions
FROM raw_events;

-- 3. Row-level routing mismatch breakdown
SELECT
    group_name,
    landing_page,
    COUNT(*) AS record_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM raw_events), 4) AS pct_of_raw_data,
    CASE 
        WHEN (group_name = 'control' AND landing_page = 'new_page') 
          OR (group_name = 'treatment' AND landing_page = 'old_page')
        THEN 'ROUTING_MISMATCH'
        ELSE 'CONSISTENT_MATCH'
    END AS routing_status
FROM raw_events
GROUP BY group_name, landing_page
ORDER BY group_name, landing_page;

-- 4. Multi-session visitor classification: Conflicting groups vs. conflicting pages
WITH user_session_summary AS (
    SELECT
        user_id,
        COUNT(*) AS session_count,
        COUNT(DISTINCT group_name) AS distinct_groups,
        COUNT(DISTINCT landing_page) AS distinct_pages
    FROM raw_events
    GROUP BY user_id
    HAVING COUNT(*) > 1
)
SELECT
    COUNT(*) AS total_multi_session_visitors,
    SUM(CASE WHEN distinct_groups > 1 THEN 1 ELSE 0 END) AS visitors_with_conflicting_groups,
    SUM(CASE WHEN distinct_pages > 1 THEN 1 ELSE 0 END) AS visitors_with_conflicting_pages,
    SUM(CASE WHEN distinct_groups = 1 AND distinct_pages = 1 THEN 1 ELSE 0 END) AS visitors_with_clean_repeats
FROM user_session_summary;

-- 5. Verification: Zero duplicate users in the clean analysis table
SELECT 
    user_id,
    COUNT(*) AS clean_session_count
FROM clean_events
GROUP BY user_id
HAVING COUNT(*) > 1;
