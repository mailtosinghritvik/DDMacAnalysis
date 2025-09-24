-- Time Analytics Functions for DDMac Analytics
-- Deploy these functions to your Supabase database

-- ==============================================
-- 6. TIME ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get time period overview
CREATE OR REPLACE FUNCTION get_time_period_overview(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    total_hours NUMERIC,
    total_users BIGINT,
    total_clients BIGINT,
    total_sessions BIGINT,
    working_days BIGINT,
    avg_daily_hours NUMERIC,
    avg_session_length NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.user_id) as total_users,
        COUNT(DISTINCT t.jobcode_id) as total_clients,
        COUNT(t.id) as total_sessions,
        COUNT(DISTINCT t.date) as working_days,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
            ELSE 0
        END as avg_daily_hours,
        CASE 
            WHEN COUNT(t.id) > 0 THEN
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END as avg_session_length
    FROM timesheets t
    WHERE t.date >= start_date AND t.date <= end_date;
END;
$$ LANGUAGE plpgsql;

-- Function to get daily time distribution
CREATE OR REPLACE FUNCTION get_time_daily_distribution(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    work_date DATE,
    total_hours NUMERIC,
    users_active BIGINT,
    clients_active BIGINT,
    sessions BIGINT,
    longest_session_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date as work_date,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.user_id) as users_active,
        COUNT(DISTINCT t.jobcode_id) as clients_active,
        COUNT(t.id) as sessions,
        COALESCE(MAX(t.duration) / 3600.0, 0) as longest_session_hours
    FROM timesheets t
    WHERE t.date >= start_date AND t.date <= end_date
    GROUP BY t.date
    ORDER BY t.date;
END;
$$ LANGUAGE plpgsql;

-- Function to get user performance ranking
CREATE OR REPLACE FUNCTION get_time_user_performance(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    user_name TEXT,
    total_hours NUMERIC,
    working_days BIGINT,
    avg_hours_per_day NUMERIC,
    clients_served BIGINT,
    sessions BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as user_name,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.date) as working_days,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
            ELSE 0
        END as avg_hours_per_day,
        COUNT(DISTINCT t.jobcode_id) as clients_served,
        COUNT(t.id) as sessions
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id AND t.date >= start_date AND t.date <= end_date
    WHERE u.active = true
    GROUP BY u.id, u.display_name, u.first_name, u.last_name
    HAVING COALESCE(SUM(t.duration), 0) > 0
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get client activity summary
CREATE OR REPLACE FUNCTION get_time_client_activity(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    client_name TEXT,
    total_hours NUMERIC,
    users_assigned BIGINT,
    sessions BIGINT,
    avg_session_hours NUMERIC,
    working_days BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.name as client_name,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.user_id) as users_assigned,
        COUNT(t.id) as sessions,
        CASE 
            WHEN COUNT(t.id) > 0 THEN
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END as avg_session_hours,
        COUNT(DISTINCT t.date) as working_days
    FROM jobcodes j
    LEFT JOIN timesheets t ON j.id = t.jobcode_id AND t.date >= start_date AND t.date <= end_date
    WHERE j.active = true
    GROUP BY j.id, j.name
    HAVING COALESCE(SUM(t.duration), 0) > 0
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get weekly summary
CREATE OR REPLACE FUNCTION get_time_weekly_summary(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    week_start DATE,
    week_end DATE,
    total_hours NUMERIC,
    daily_average NUMERIC,
    users BIGINT,
    clients BIGINT,
    sessions BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH weekly_data AS (
        SELECT 
            DATE_TRUNC('week', t.date) as week_start,
            DATE_TRUNC('week', t.date) + INTERVAL '6 days' as week_end,
            SUM(t.duration) / 3600.0 as total_hours,
            COUNT(DISTINCT t.user_id) as users,
            COUNT(DISTINCT t.jobcode_id) as clients,
            COUNT(t.id) as sessions
        FROM timesheets t
        WHERE t.date >= start_date AND t.date <= end_date
        GROUP BY DATE_TRUNC('week', t.date)
    )
    SELECT 
        wd.week_start::DATE,
        wd.week_end::DATE,
        COALESCE(wd.total_hours, 0) as total_hours,
        CASE 
            WHEN wd.users > 0 THEN
                COALESCE(wd.total_hours, 0) / 7.0
            ELSE 0
        END as daily_average,
        wd.users,
        wd.clients,
        wd.sessions
    FROM weekly_data wd
    ORDER BY wd.week_start;
END;
$$ LANGUAGE plpgsql;

-- Function to get session length analysis
CREATE OR REPLACE FUNCTION get_time_session_analysis(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE (
    session_type TEXT,
    count BIGINT,
    total_hours NUMERIC,
    percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH session_categories AS (
        SELECT 
            CASE 
                WHEN t.duration < 7200 THEN 'Short Sessions (< 2 hours)'
                WHEN t.duration < 14400 THEN 'Medium Sessions (2-4 hours)'
                ELSE 'Long Sessions (4+ hours)'
            END as session_type,
            t.duration / 3600.0 as hours
        FROM timesheets t
        WHERE t.date >= start_date AND t.date <= end_date
    ),
    totals AS (
        SELECT 
            COUNT(*) as total_count,
            SUM(hours) as total_hours
        FROM session_categories
    )
    SELECT 
        sc.session_type,
        COUNT(*) as count,
        SUM(sc.hours) as total_hours,
        CASE 
            WHEN t.total_count > 0 THEN
                (COUNT(*) * 100.0 / t.total_count)
            ELSE 0
        END as percentage
    FROM session_categories sc
    CROSS JOIN totals t
    GROUP BY sc.session_type, t.total_count
    ORDER BY sc.session_type;
END;
$$ LANGUAGE plpgsql;
