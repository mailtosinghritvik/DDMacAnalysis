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
-- 6. DASHBOARD SUMMARY FUNCTION
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
