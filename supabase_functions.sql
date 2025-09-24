-- Supabase Functions for DDMac Analytics
-- These functions provide direct database access for the EmailReportWriter

-- ==============================================
-- 1. EMPLOYEE ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get employee overview data
CREATE OR REPLACE FUNCTION get_employee_analytics(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    employee_id BIGINT,
    first_name TEXT,
    last_name TEXT,
    display_name TEXT,
    email TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_entries BIGINT,
    avg_daily_hours NUMERIC,
    utilization_rate NUMERIC,
    productivity_score NUMERIC,
    active_projects BIGINT,
    last_active TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as employee_id,
        u.first_name,
        u.last_name,
        u.display_name,
        u.email,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration ELSE 0 END) / 3600.0, 0) as billable_hours,
        COUNT(t.id) as total_entries,
        COALESCE(AVG(t.duration) / 3600.0, 0) as avg_daily_hours,
        CASE 
            WHEN u.salaried = true THEN 
                LEAST(COALESCE(SUM(t.duration) / 3600.0, 0) / 40.0, 1.0)
            ELSE 
                LEAST(COALESCE(SUM(t.duration) / 3600.0, 0) / 40.0, 1.0)
        END as utilization_rate,
        -- Productivity score based on hours and project diversity
        CASE 
            WHEN COUNT(DISTINCT t.jobcode_id) > 0 THEN 
                LEAST(COALESCE(SUM(t.duration) / 3600.0, 0) / 40.0 * (COUNT(DISTINCT t.jobcode_id) / 2.0), 10.0)
            ELSE 0
        END as productivity_score,
        COUNT(DISTINCT t.jobcode_id) as active_projects,
        u.last_active
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id
    LEFT JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE u.active = true
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY u.id, u.first_name, u.last_name, u.display_name, u.email, u.salaried, u.last_active
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get employee detailed performance
CREATE OR REPLACE FUNCTION get_employee_detailed_performance(
    employee_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    date DATE,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    project_name TEXT,
    jobcode_name TEXT,
    notes TEXT,
    location TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date,
        t.duration / 3600.0 as total_hours,
        CASE WHEN j.billable = true THEN t.duration / 3600.0 ELSE 0 END as billable_hours,
        p.name as project_name,
        j.name as jobcode_name,
        t.notes,
        t.location
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.user_id = employee_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    ORDER BY t.date DESC, t.start;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 2. PROJECT ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get project analytics data (using jobcodes as projects)
CREATE OR REPLACE FUNCTION get_project_analytics(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    project_id BIGINT,
    project_name TEXT,
    jobcode_name TEXT,
    status TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_entries BIGINT,
    unique_employees BIGINT,
    avg_hours_per_employee NUMERIC,
    completion_percentage NUMERIC,
    budget_status TEXT,
    start_date TEXT,
    due_date TEXT,
    completed_date TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.id as project_id,
        j.name as project_name,
        j.name as jobcode_name,
        CASE 
            WHEN j.active = true THEN 'in_progress'
            ELSE 'completed'
        END as status,
        COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration ELSE 0 END) / 3600.0, 0)::NUMERIC as billable_hours,
        COUNT(t.id) as total_entries,
        COUNT(DISTINCT t.user_id) as unique_employees,
        CASE 
            WHEN COUNT(DISTINCT t.user_id) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.user_id))::NUMERIC
            ELSE 0::NUMERIC
        END as avg_hours_per_employee,
        CASE 
            WHEN ab.time_estimate > 0 THEN 
                LEAST(
                    (COALESCE(SUM(t.duration) / 3600.0, 0) / ab.time_estimate * 100)::NUMERIC,
                    100::NUMERIC
                )
            ELSE 0::NUMERIC
        END as completion_percentage,
        CASE 
            WHEN ab.cost_estimate > 0 AND COALESCE(SUM(t.duration) / 3600.0, 0) * 50 > ab.cost_estimate THEN 'over_budget'
            WHEN ab.cost_estimate > 0 AND COALESCE(SUM(t.duration) / 3600.0, 0) * 50 < ab.cost_estimate * 0.8 THEN 'under_budget'
            ELSE 'on_budget'
        END as budget_status,
        NULL::TEXT as start_date,
        NULL::TEXT as due_date,
        NULL::TEXT as completed_date
    FROM jobcodes j
    LEFT JOIN timesheets t ON j.id = t.jobcode_id
    LEFT JOIN accubid_breakdowns ab ON j.name = ab.job_name
    WHERE j.active = true
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY j.id, j.name, j.active, ab.time_estimate, ab.cost_estimate
    HAVING COUNT(t.id) > 0
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get project team allocation (using jobcodes as projects)
CREATE OR REPLACE FUNCTION get_project_team_allocation(
    project_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    employee_id BIGINT,
    employee_name TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    efficiency_score NUMERIC,
    last_activity DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as employee_id,
        COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as employee_name,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration ELSE 0 END) / 3600.0, 0) as billable_hours,
        -- Efficiency score based on hours logged vs expected
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                LEAST(COALESCE(SUM(t.duration) / 3600.0, 0) / 40.0 * (COUNT(DISTINCT t.date) / 20.0), 10.0)
            ELSE 0
        END as efficiency_score,
        MAX(t.date) as last_activity
    FROM users u
    JOIN timesheets t ON u.id = t.user_id
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE j.id = project_id_param
        AND u.active = true
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY u.id, u.display_name, u.first_name, u.last_name
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 3. TASK ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get task analytics data
CREATE OR REPLACE FUNCTION get_task_analytics(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    task_id BIGINT,
    jobcode_name TEXT,
    project_name TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_entries BIGINT,
    unique_employees BIGINT,
    avg_duration_per_entry NUMERIC,
    total_cost NUMERIC,
    efficiency_rating TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.id as task_id,
        j.name as jobcode_name,
        p.name as project_name,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration ELSE 0 END) / 3600.0, 0) as billable_hours,
        COUNT(t.id) as total_entries,
        COUNT(DISTINCT t.user_id) as unique_employees,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                AVG(t.duration) / 3600.0
            ELSE 0
        END as avg_duration_per_entry,
        COALESCE(SUM(t.duration) / 3600.0 * 50, 0) as total_cost,
        CASE 
            WHEN AVG(t.duration) / 3600.0 < 2 THEN 'high_efficiency'
            WHEN AVG(t.duration) / 360.0 < 4 THEN 'medium_efficiency'
            ELSE 'low_efficiency'
        END as efficiency_rating
    FROM jobcodes j
    LEFT JOIN timesheets t ON j.id = t.jobcode_id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE j.active = true
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY j.id, j.name, p.name
    HAVING COUNT(t.id) > 0
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 4. TIME TRACKING FUNCTIONS
-- ==============================================

-- Function to get time tracking summary

CREATE OR REPLACE FUNCTION get_time_tracking_summary(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    date DATE,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_entries BIGINT,
    unique_employees BIGINT,
    avg_hours_per_employee NUMERIC,
    total_cost NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date,
        COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration ELSE 0 END) / 3600.0, 0)::NUMERIC as billable_hours,
        COUNT(t.id) as total_entries,
        COUNT(DISTINCT t.user_id) as unique_employees,
        CASE 
            WHEN COUNT(DISTINCT t.user_id) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.user_id))::NUMERIC
            ELSE 0::NUMERIC
        END as avg_hours_per_employee,
        COALESCE(SUM(t.duration) / 3600.0 * 50, 0)::NUMERIC as total_cost
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE (start_date_param IS NULL OR t.date >= start_date_param)
      AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY t.date
    ORDER BY t.date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get employee time tracking details
CREATE OR REPLACE FUNCTION get_employee_time_tracking(
    employee_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    date DATE,
    start_time TEXT,
    end_time TEXT,
    duration_hours NUMERIC,
    jobcode_name TEXT,
    project_name TEXT,
    billable BOOLEAN,
    notes TEXT,
    location TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date,
        t.start,
        t.end,
        t.duration / 3600.0 as duration_hours,
        j.name as jobcode_name,
        p.name as project_name,
        j.billable,
        t.notes,
        t.location
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.user_id = employee_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    ORDER BY t.date DESC, t.start;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 5. FINANCIAL ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get financial metrics
CREATE OR REPLACE FUNCTION get_financial_metrics(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    total_revenue NUMERIC,
    total_cost NUMERIC,
    profit_margin NUMERIC,
    avg_hourly_rate NUMERIC,
    total_billable_hours NUMERIC,
    total_non_billable_hours NUMERIC,
    cost_per_employee NUMERIC,
    revenue_per_project NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 * 50 ELSE 0 END), 0) as total_revenue,
        COALESCE(SUM(t.duration / 3600.0 * 50), 0) as total_cost,
        CASE 
            WHEN SUM(t.duration / 3600.0 * 50) > 0 THEN
                (SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 * 50 ELSE 0 END) - 
                 SUM(t.duration / 3600.0 * 50)) / 
                SUM(t.duration / 3600.0 * 50) * 100
            ELSE 0
        END as profit_margin,
        CASE 
            WHEN SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 ELSE 0 END) > 0 THEN
                SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 * 50 ELSE 0 END) / 
                SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 ELSE 0 END)
            ELSE 0
        END as avg_hourly_rate,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 ELSE 0 END), 0) as total_billable_hours,
        COALESCE(SUM(CASE WHEN j.billable = false THEN t.duration / 3600.0 ELSE 0 END), 0) as total_non_billable_hours,
        CASE 
            WHEN COUNT(DISTINCT t.user_id) > 0 THEN
                SUM(t.duration / 3600.0 * 50) / COUNT(DISTINCT t.user_id)
            ELSE 0
        END as cost_per_employee,
        CASE 
            WHEN COUNT(DISTINCT j.id) > 0 THEN
                SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 * 50 ELSE 0 END) / COUNT(DISTINCT j.id)
            ELSE 0
        END as revenue_per_project
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param);
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 6. USER MANAGEMENT FUNCTIONS
-- ==============================================

-- Function to get available users (for dropdowns and selections)
CREATE OR REPLACE FUNCTION get_available_users()
RETURNS TABLE (
    user_id BIGINT,
    display_name TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as user_id,
        COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
        u.first_name,
        u.last_name,
        u.email,
        u.active
    FROM users u
    WHERE u.active = true
    ORDER BY u.display_name, u.first_name, u.last_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get available clients (for dropdowns and selections)
CREATE OR REPLACE FUNCTION get_available_clients()
RETURNS TABLE (
    client_id BIGINT,
    client_name TEXT,
    jobcode_name TEXT,
    billable BOOLEAN,
    active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.id as client_id,
        j.name as client_name,
        j.name as jobcode_name,
        j.billable,
        j.active
    FROM jobcodes j
    WHERE j.active = true
    ORDER BY j.name;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 7. USER ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get user daily work summary
CREATE OR REPLACE FUNCTION get_user_daily_work_summary(
    user_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    work_date DATE,
    total_hours NUMERIC,
    clients_worked BIGINT,
    sessions BIGINT,
    longest_session_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date as work_date,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT j.id) as clients_worked,
        COUNT(t.id) as sessions,
        COALESCE(MAX(t.duration) / 3600.0, 0) as longest_session_hours
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE t.user_id = user_id_param
        AND t.date >= start_date_param
        AND t.date <= end_date_param
    GROUP BY t.date
    ORDER BY t.date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get user client time distribution
CREATE OR REPLACE FUNCTION get_user_client_time_distribution(
    user_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    client_name TEXT,
    total_hours NUMERIC,
    sessions BIGINT,
    avg_session_hours NUMERIC,
    first_date DATE,
    last_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.name as client_name,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(t.id) as sessions,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END as avg_session_hours,
        MIN(t.date) as first_date,
        MAX(t.date) as last_date
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE t.user_id = user_id_param
        AND t.date >= start_date_param
        AND t.date <= end_date_param
    GROUP BY j.id, j.name
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get user vs team comparison metrics
CREATE OR REPLACE FUNCTION get_user_team_comparison(
    user_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
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
            RANK() OVER (ORDER BY total_hours DESC) as total_hours_rank,
            RANK() OVER (ORDER BY avg_hours_per_day DESC) as avg_hours_rank,
            RANK() OVER (ORDER BY clients_served DESC) as clients_rank,
            RANK() OVER (ORDER BY avg_session_length DESC) as session_length_rank,
            RANK() OVER (ORDER BY longest_session DESC) as longest_session_rank,
            COUNT(*) OVER() as total_users
        FROM user_metrics
    )
    SELECT 
        'Total Hours'::TEXT as metric_name,
        um.total_hours as user_value,
        AVG(um.total_hours) OVER() as team_average,
        rm.total_hours_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.total_hours_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Avg Hours/Day'::TEXT as metric_name,
        um.avg_hours_per_day as user_value,
        AVG(um.avg_hours_per_day) OVER() as team_average,
        rm.avg_hours_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.avg_hours_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Clients Served'::TEXT as metric_name,
        um.clients_served as user_value,
        AVG(um.clients_served) OVER() as team_average,
        rm.clients_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.clients_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Avg Session Length'::TEXT as metric_name,
        um.avg_session_length as user_value,
        AVG(um.avg_session_length) OVER() as team_average,
        rm.session_length_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.session_length_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    WHERE um.user_id = user_id_param
    
    UNION ALL
    
    SELECT 
        'Longest Session'::TEXT as metric_name,
        um.longest_session as user_value,
        AVG(um.longest_session) OVER() as team_average,
        rm.longest_session_rank as user_rank,
        rm.total_users,
        (rm.total_users - rm.longest_session_rank + 1)::NUMERIC / rm.total_users * 100 as percentile
    FROM user_metrics um
    JOIN ranked_metrics rm ON um.user_id = rm.user_id
    WHERE um.user_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get user period summary
CREATE OR REPLACE FUNCTION get_user_period_summary(
    user_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    total_hours NUMERIC,
    working_days BIGINT,
    avg_hours_per_day NUMERIC,
    clients_served BIGINT,
    total_sessions BIGINT,
    avg_session_length NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.date) as working_days,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
            ELSE 0
        END as avg_hours_per_day,
        COUNT(DISTINCT j.id) as clients_served,
        COUNT(t.id) as total_sessions,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END as avg_session_length
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE t.user_id = user_id_param
        AND t.date >= start_date_param
        AND t.date <= end_date_param;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 8. CLIENT ANALYTICS FUNCTIONS
-- ==============================================

-- Function to get client overview summary
CREATE OR REPLACE FUNCTION get_client_overview_summary(
    client_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    total_hours NUMERIC,
    users_assigned BIGINT,
    total_sessions BIGINT,
    avg_hours_per_day NUMERIC,
    working_days BIGINT,
    first_date_worked DATE,
    last_date_worked DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.user_id) as users_assigned,
        COUNT(t.id) as total_sessions,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
            ELSE 0
        END as avg_hours_per_day,
        COUNT(DISTINCT t.date) as working_days,
        MIN(t.date) as first_date_worked,
        MAX(t.date) as last_date_worked
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE j.id = client_id_param
        AND t.date >= start_date_param
        AND t.date <= end_date_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get client user allocation
CREATE OR REPLACE FUNCTION get_client_user_allocation(
    client_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    user_name TEXT,
    total_hours NUMERIC,
    percentage NUMERIC,
    sessions BIGINT,
    avg_session_hours NUMERIC,
    first_date DATE,
    last_date DATE
) AS $$
BEGIN
    RETURN QUERY
    WITH client_total_hours AS (
        SELECT COALESCE(SUM(t.duration) / 3600.0, 0) as total_client_hours
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE j.id = client_id_param
            AND t.date >= start_date_param
            AND t.date <= end_date_param
    )
    SELECT 
        COALESCE(u.username, CONCAT(u.first_name, ' ', u.last_name)) as user_name,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        CASE 
            WHEN cth.total_client_hours > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / cth.total_client_hours * 100)
            ELSE 0
        END as percentage,
        COUNT(t.id) as sessions,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END as avg_session_hours,
        MIN(t.date) as first_date,
        MAX(t.date) as last_date
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    JOIN users u ON t.user_id = u.id
    CROSS JOIN client_total_hours cth
    WHERE j.id = client_id_param
        AND t.date >= start_date_param
        AND t.date <= end_date_param
    GROUP BY u.id, u.username, u.first_name, u.last_name, cth.total_client_hours
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get client vs other clients comparison
CREATE OR REPLACE FUNCTION get_client_comparison(
    client_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    metric_name TEXT,
    client_value NUMERIC,
    ddmac_average NUMERIC,
    client_rank BIGINT,
    total_clients BIGINT,
    percentile NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH client_metrics AS (
        SELECT 
            j.id as client_id,
            j.name as client_name,
            COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
            COUNT(DISTINCT t.user_id) as users_assigned,
            COUNT(t.id) as total_sessions,
            COUNT(DISTINCT t.date) as working_days,
            CASE 
                WHEN COUNT(t.id) > 0 THEN 
                    COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
                ELSE 0
            END as avg_session_length,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    COALESCE(SUM(t.duration) / 3600.0, 0) / (COUNT(DISTINCT t.date) / 7.0)
                ELSE 0
            END as hours_per_week
        FROM jobcodes j
        LEFT JOIN timesheets t ON j.id = t.jobcode_id
        WHERE j.active = true
            AND (t.date IS NULL OR (t.date >= start_date_param AND t.date <= end_date_param))
        GROUP BY j.id, j.name
    ),
    ranked_metrics AS (
        SELECT 
            client_id,
            client_name,
            total_hours,
            users_assigned,
            total_sessions,
            working_days,
            avg_session_length,
            hours_per_week,
            RANK() OVER (ORDER BY total_hours DESC) as total_hours_rank,
            RANK() OVER (ORDER BY users_assigned DESC) as users_rank,
            RANK() OVER (ORDER BY avg_session_length DESC) as session_length_rank,
            RANK() OVER (ORDER BY working_days DESC) as working_days_rank,
            RANK() OVER (ORDER BY hours_per_week DESC) as hours_per_week_rank,
            COUNT(*) OVER() as total_clients
        FROM client_metrics
    )
    SELECT 
        'Total Hours'::TEXT as metric_name,
        cm.total_hours as client_value,
        AVG(cm.total_hours) OVER() as ddmac_average,
        rm.total_hours_rank as client_rank,
        rm.total_clients,
        (rm.total_clients - rm.total_hours_rank + 1)::NUMERIC / rm.total_clients * 100 as percentile
    FROM client_metrics cm
    JOIN ranked_metrics rm ON cm.client_id = rm.client_id
    WHERE cm.client_id = client_id_param
    
    UNION ALL
    
    SELECT 
        'Users Assigned'::TEXT as metric_name,
        cm.users_assigned as client_value,
        AVG(cm.users_assigned) OVER() as ddmac_average,
        rm.users_rank as client_rank,
        rm.total_clients,
        (rm.total_clients - rm.users_rank + 1)::NUMERIC / rm.total_clients * 100 as percentile
    FROM client_metrics cm
    JOIN ranked_metrics rm ON cm.client_id = rm.client_id
    WHERE cm.client_id = client_id_param
    
    UNION ALL
    
    SELECT 
        'Avg Session Length'::TEXT as metric_name,
        cm.avg_session_length as client_value,
        AVG(cm.avg_session_length) OVER() as ddmac_average,
        rm.session_length_rank as client_rank,
        rm.total_clients,
        (rm.total_clients - rm.session_length_rank + 1)::NUMERIC / rm.total_clients * 100 as percentile
    FROM client_metrics cm
    JOIN ranked_metrics rm ON cm.client_id = rm.client_id
    WHERE cm.client_id = client_id_param
    
    UNION ALL
    
    SELECT 
        'Working Days'::TEXT as metric_name,
        cm.working_days as client_value,
        AVG(cm.working_days) OVER() as ddmac_average,
        rm.working_days_rank as client_rank,
        rm.total_clients,
        (rm.total_clients - rm.working_days_rank + 1)::NUMERIC / rm.total_clients * 100 as percentile
    FROM client_metrics cm
    JOIN ranked_metrics rm ON cm.client_id = rm.client_id
    WHERE cm.client_id = client_id_param
    
    UNION ALL
    
    SELECT 
        'Hours per Week'::TEXT as metric_name,
        cm.hours_per_week as client_value,
        AVG(cm.hours_per_week) OVER() as ddmac_average,
        rm.hours_per_week_rank as client_rank,
        rm.total_clients,
        (rm.total_clients - rm.hours_per_week_rank + 1)::NUMERIC / rm.total_clients * 100 as percentile
    FROM client_metrics cm
    JOIN ranked_metrics rm ON cm.client_id = rm.client_id
    WHERE cm.client_id = client_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get client weekly summary
CREATE OR REPLACE FUNCTION get_client_weekly_summary(
    client_id_param BIGINT,
    start_date_param DATE,
    end_date_param DATE
)
RETURNS TABLE (
    week_start DATE,
    week_end DATE,
    total_hours NUMERIC,
    users_active BIGINT,
    sessions BIGINT,
    avg_session_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE_TRUNC('week', t.date)::DATE as week_start,
        (DATE_TRUNC('week', t.date) + INTERVAL '6 days')::DATE as week_end,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COUNT(DISTINCT t.user_id) as users_active,
        COUNT(t.id) as sessions,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END as avg_session_hours
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE j.id = client_id_param
        AND t.date >= start_date_param
        AND t.date <= end_date_param
    GROUP BY DATE_TRUNC('week', t.date)
    ORDER BY week_start DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- 9. DASHBOARD SUMMARY FUNCTION
-- ==============================================

-- Function to get comprehensive dashboard data
CREATE OR REPLACE FUNCTION get_dashboard_summary(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    total_employees BIGINT,
    active_employees BIGINT,
    total_projects BIGINT,
    active_projects BIGINT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_revenue NUMERIC,
    avg_utilization NUMERIC,
    project_health_score NUMERIC,
    total_tasks BIGINT,
    avg_task_duration NUMERIC,
    cost_efficiency NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT u.id) as total_employees,
        COUNT(DISTINCT CASE WHEN u.active = true THEN u.id END) as active_employees,
        COUNT(DISTINCT j.id) as total_projects,
        COUNT(DISTINCT CASE WHEN j.active = true THEN j.id END) as active_projects,
        COALESCE(SUM(t.duration) / 3600.0, 0) as total_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration ELSE 0 END) / 3600.0, 0) as billable_hours,
        COALESCE(SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 * 50 ELSE 0 END), 0) as total_revenue,
        CASE 
            WHEN COUNT(DISTINCT u.id) > 0 THEN
                LEAST(COALESCE(SUM(t.duration) / 3600.0, 0) / (COUNT(DISTINCT u.id) * 40.0), 1.0)
            ELSE 0
        END as avg_utilization,
        -- Project health score based on jobcode activity and billable status
        CASE 
            WHEN COUNT(DISTINCT j.id) > 0 THEN
                (COUNT(DISTINCT CASE WHEN j.active = true AND j.billable = true THEN j.id END) * 1.0 +
                 COUNT(DISTINCT CASE WHEN j.active = true AND j.billable = false THEN j.id END) * 0.7 +
                 COUNT(DISTINCT CASE WHEN j.active = false THEN j.id END) * 0.3) / 
                COUNT(DISTINCT j.id) * 10
            ELSE 0
        END as project_health_score,
        COUNT(DISTINCT j.id) as total_tasks,
        CASE 
            WHEN COUNT(t.id) > 0 THEN
                AVG(t.duration) / 3600.0
            ELSE 0
        END as avg_task_duration,
        CASE 
            WHEN SUM(t.duration / 3600.0 * 50) > 0 THEN
                SUM(CASE WHEN j.billable = true THEN t.duration / 3600.0 * 50 ELSE 0 END) / 
                SUM(t.duration / 3600.0 * 50) * 100
            ELSE 0
        END as cost_efficiency
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id
    LEFT JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param);
END;
$$ LANGUAGE plpgsql;

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