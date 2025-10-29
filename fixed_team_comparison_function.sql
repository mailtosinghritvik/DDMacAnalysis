CREATE OR REPLACE FUNCTION get_team_comparison_metrics(
    user_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    metric_name TEXT,
    user_value NUMERIC,
    team_average NUMERIC,
    user_rank INTEGER,
    total_users INTEGER,
    percentile NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH user_metrics AS (
        SELECT 
            u.id as user_id,
            COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
            COUNT(DISTINCT t.date) as working_days,
            COUNT(DISTINCT j.id) as clients_served,
            COUNT(t.id) as total_sessions,
            COALESCE(SUM(t.duration) / 3600.0, 0) / NULLIF(COUNT(DISTINCT t.date), 0) as avg_hours_per_day,
            COALESCE(SUM(t.duration) / 3600.0, 0) / NULLIF(COUNT(t.id), 0) as avg_session_length,
            COALESCE(MAX(t.duration) / 3600.0, 0) as longest_session
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id
        LEFT JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE u.active = true
            AND (t.date IS NULL OR (t.date >= start_date_param AND t.date <= end_date_param))
        GROUP BY u.id
    ),
    team_averages AS (
        SELECT 
            AVG(total_hours) as avg_total_hours,
            AVG(avg_hours_per_day) as avg_hours_per_day,
            AVG(clients_served) as avg_clients_served,
            AVG(avg_session_length) as avg_session_length,
            AVG(longest_session) as avg_longest_session
        FROM user_metrics
    ),
    ranked_metrics AS (
        SELECT 
            user_id,
            total_hours,
            working_days,
            clients_served,
            total_sessions,
            avg_hours_per_day,
            avg_session_length,
            longest_session,
            RANK() OVER (ORDER BY total_hours DESC)::INTEGER as total_hours_rank,
            RANK() OVER (ORDER BY avg_hours_per_day DESC)::INTEGER as avg_hours_rank,
            RANK() OVER (ORDER BY clients_served DESC)::INTEGER as clients_rank,
            RANK() OVER (ORDER BY avg_session_length DESC)::INTEGER as session_length_rank,
            RANK() OVER (ORDER BY longest_session DESC)::INTEGER as longest_session_rank,
            COUNT(*) OVER()::INTEGER as total_users
        FROM user_metrics
    )
    SELECT 
        'Total Hours'::TEXT as metric_name,
        um.total_hours as user_value,
        ta.avg_total_hours as team_average,
        rm.total_hours_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.total_hours_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    CROSS JOIN team_averages ta
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Avg Hours/Day'::TEXT as metric_name,
        um.avg_hours_per_day as user_value,
        ta.avg_hours_per_day as team_average,
        rm.avg_hours_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.avg_hours_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    CROSS JOIN team_averages ta
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Clients Served'::TEXT as metric_name,
        um.clients_served as user_value,
        ta.avg_clients_served as team_average,
        rm.clients_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.clients_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    CROSS JOIN team_averages ta
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Avg Session Length'::TEXT as metric_name,
        um.avg_session_length as user_value,
        ta.avg_session_length as team_average,
        rm.session_length_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.session_length_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    CROSS JOIN team_averages ta
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Longest Session'::TEXT as metric_name,
        um.longest_session as user_value,
        ta.avg_longest_session as team_average,
        rm.longest_session_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.longest_session_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    CROSS JOIN team_averages ta
    WHERE um.user_id = user_id_param;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION "public"."get_employee_detailed_data_v2"("user_id_param" bigint, "start_date_param" "date" DEFAULT NULL::"date", "end_date_param" "date" DEFAULT NULL::"date", "limit_param" integer DEFAULT 1000, "offset_param" integer DEFAULT 0) 
RETURNS TABLE("work_date" "date", "client_name" "text", "task_name" "text", "hours_worked" numeric, "job_code" "text", "billable" boolean)
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date as work_date,
        COALESCE(j.name, 'Unknown') as client_name,
        COALESCE(p.name, j.name, 'Unknown') as task_name,
        ROUND((t.duration / 3600.0), 2) as hours_worked,
        COALESCE(j.short_code, '') as job_code,
        COALESCE(j.billable, true) as billable
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.user_id = user_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    ORDER BY t.date DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;