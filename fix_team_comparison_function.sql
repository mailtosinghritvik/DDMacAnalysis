-- ==============================================
-- FIXED TEAM COMPARISON FUNCTION
-- ==============================================
-- This function properly separates user values from team averages

CREATE OR REPLACE FUNCTION get_user_team_comparison(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    metric_name TEXT,
    user_value NUMERIC,
    team_average NUMERIC,
    user_rank BIGINT,
    total_users BIGINT,
    percentile NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH user_metrics AS (
        -- Get the specific user's metrics
        SELECT 
            u.id as user_id,
            COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
                ELSE 0
            END as avg_hours_per_day,
            COUNT(DISTINCT j.name) as clients_served,
            CASE 
                WHEN COUNT(t.id) > 0 THEN 
                    COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
                ELSE 0
            END as avg_session_length,
            CASE 
                WHEN COUNT(t.id) > 0 THEN 
                    MAX(t.duration) / 3600.0
                ELSE 0
            END as longest_session
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id 
            AND (start_date_param IS NULL OR t.date >= start_date_param)
            AND (end_date_param IS NULL OR t.date <= end_date_param)
        LEFT JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE u.id = user_id_param
        GROUP BY u.id
    ),
    all_team_metrics AS (
        -- Get ALL team members' metrics (including the target user)
        SELECT 
            u.id as user_id,
            COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
                ELSE 0
            END as avg_hours_per_day,
            COUNT(DISTINCT j.name) as clients_served,
            CASE 
                WHEN COUNT(t.id) > 0 THEN 
                    COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
                ELSE 0
            END as avg_session_length,
            CASE 
                WHEN COUNT(t.id) > 0 THEN 
                    MAX(t.duration) / 3600.0
                ELSE 0
            END as longest_session
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id 
            AND (start_date_param IS NULL OR t.date >= start_date_param)
            AND (end_date_param IS NULL OR t.date <= end_date_param)
        LEFT JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE u.active = true
        GROUP BY u.id
    ),
    team_averages AS (
        -- Calculate team averages EXCLUDING the target user
        SELECT 
            AVG(total_hours) as avg_total_hours,
            AVG(avg_hours_per_day) as avg_daily_hours,
            AVG(clients_served) as avg_clients_served,
            AVG(avg_session_length) as avg_session_length,
            AVG(longest_session) as avg_longest_session,
            COUNT(*) as total_team_members
        FROM all_team_metrics
        WHERE user_id != user_id_param  -- EXCLUDE the target user from team average
    ),
    user_rankings AS (
        -- Calculate user rankings for each metric
        SELECT 
            um.user_id,
            um.total_hours,
            um.avg_hours_per_day,
            um.clients_served,
            um.avg_session_length,
            um.longest_session,
            -- Calculate ranks (higher is better, so we use DESC)
            ROW_NUMBER() OVER (ORDER BY atm.total_hours DESC) as total_hours_rank,
            ROW_NUMBER() OVER (ORDER BY atm.avg_hours_per_day DESC) as daily_hours_rank,
            ROW_NUMBER() OVER (ORDER BY atm.clients_served DESC) as clients_rank,
            ROW_NUMBER() OVER (ORDER BY atm.avg_session_length DESC) as session_length_rank,
            ROW_NUMBER() OVER (ORDER BY atm.longest_session DESC) as longest_session_rank,
            ta.total_team_members + 1 as total_users  -- +1 to include the target user
        FROM user_metrics um
        CROSS JOIN team_averages ta
        CROSS JOIN all_team_metrics atm
        WHERE atm.user_id = um.user_id
    )
    -- Return the comparison data
    SELECT 
        'Total Hours'::TEXT as metric_name,
        ur.total_hours as user_value,
        ta.avg_total_hours as team_average,
        ur.total_hours_rank as user_rank,
        ur.total_users as total_users,
        ROUND(((ur.total_users - ur.total_hours_rank + 1)::NUMERIC / ur.total_users) * 100, 1) as percentile
    FROM user_rankings ur
    CROSS JOIN team_averages ta
    
    UNION ALL
    
    SELECT 
        'Avg Hours/Day'::TEXT as metric_name,
        ur.avg_hours_per_day as user_value,
        ta.avg_daily_hours as team_average,
        ur.daily_hours_rank as user_rank,
        ur.total_users as total_users,
        ROUND(((ur.total_users - ur.daily_hours_rank + 1)::NUMERIC / ur.total_users) * 100, 1) as percentile
    FROM user_rankings ur
    CROSS JOIN team_averages ta
    
    UNION ALL
    
    SELECT 
        'Clients Served'::TEXT as metric_name,
        ur.clients_served as user_value,
        ta.avg_clients_served as team_average,
        ur.clients_rank as user_rank,
        ur.total_users as total_users,
        ROUND(((ur.total_users - ur.clients_rank + 1)::NUMERIC / ur.total_users) * 100, 1) as percentile
    FROM user_rankings ur
    CROSS JOIN team_averages ta
    
    UNION ALL
    
    SELECT 
        'Avg Session Length'::TEXT as metric_name,
        ur.avg_session_length as user_value,
        ta.avg_session_length as team_average,
        ur.session_length_rank as user_rank,
        ur.total_users as total_users,
        ROUND(((ur.total_users - ur.session_length_rank + 1)::NUMERIC / ur.total_users) * 100, 1) as percentile
    FROM user_rankings ur
    CROSS JOIN team_averages ta
    
    UNION ALL
    
    SELECT 
        'Longest Session'::TEXT as metric_name,
        ur.longest_session as user_value,
        ta.avg_longest_session as team_average,
        ur.longest_session_rank as user_rank,
        ur.total_users as total_users,
        ROUND(((ur.total_users - ur.longest_session_rank + 1)::NUMERIC / ur.total_users) * 100, 1) as percentile
    FROM user_rankings ur
    CROSS JOIN team_averages ta;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- TEST QUERIES
-- ==============================================

-- Test the function with a specific user
-- SELECT * FROM get_user_team_comparison(1, '2024-01-01', '2024-12-31');

-- Test with all data (no date filter)
-- SELECT * FROM get_user_team_comparison(1, NULL, NULL);

-- Debug query to see what's happening
-- SELECT 
--     'User Metrics' as source,
--     total_hours,
--     avg_hours_per_day,
--     clients_served,
--     avg_session_length,
--     longest_session
-- FROM (
--     SELECT 
--         u.id as user_id,
--         COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
--         CASE 
--             WHEN COUNT(DISTINCT t.date) > 0 THEN 
--                 COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
--             ELSE 0
--         END as avg_hours_per_day,
--         COUNT(DISTINCT j.name) as clients_served,
--         CASE 
--             WHEN COUNT(t.id) > 0 THEN 
--                 COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
--             ELSE 0
--         END as avg_session_length,
--         CASE 
--             WHEN COUNT(t.id) > 0 THEN 
--                 MAX(t.duration) / 3600.0
--             ELSE 0
--         END as longest_session
--     FROM users u
--     LEFT JOIN timesheets t ON u.id = t.user_id
--     LEFT JOIN jobcodes j ON t.jobcode_id = j.id
--     WHERE u.id = 1  -- Replace with actual user ID
--     GROUP BY u.id
-- ) user_data
-- UNION ALL
-- SELECT 
--     'Team Average' as source,
--     AVG(total_hours) as total_hours,
--     AVG(avg_hours_per_day) as avg_hours_per_day,
--     AVG(clients_served) as clients_served,
--     AVG(avg_session_length) as avg_session_length,
--     AVG(longest_session) as longest_session
-- FROM (
--     SELECT 
--         u.id as user_id,
--         COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
--         CASE 
--             WHEN COUNT(DISTINCT t.date) > 0 THEN 
--                 COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
--             ELSE 0
--         END as avg_hours_per_day,
--         COUNT(DISTINCT j.name) as clients_served,
--         CASE 
--             WHEN COUNT(t.id) > 0 THEN 
--                 COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
--             ELSE 0
--         END as avg_session_length,
--         CASE 
--             WHEN COUNT(t.id) > 0 THEN 
--                 MAX(t.duration) / 3600.0
--             ELSE 0
--         END as longest_session
--     FROM users u
--     LEFT JOIN timesheets t ON u.id = t.user_id
--     LEFT JOIN jobcodes j ON t.jobcode_id = j.id
--     WHERE u.active = true AND u.id != 1  -- Exclude target user
--     GROUP BY u.id
-- ) team_data;
