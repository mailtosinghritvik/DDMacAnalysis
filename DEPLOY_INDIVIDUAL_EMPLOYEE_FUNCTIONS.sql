-- ==============================================
-- DEPLOY INDIVIDUAL EMPLOYEE FUNCTIONS TO SUPABASE
-- ==============================================
-- Copy and paste this entire file into your Supabase SQL Editor
-- This will deploy all the fixed individual employee functions

-- Function to get individual employee summary with all metrics
CREATE OR REPLACE FUNCTION get_individual_employee_summary(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    employee_id BIGINT,
    employee_name TEXT,
    full_name TEXT,
    work_start_date DATE,
    work_end_date DATE,
    total_work_hours NUMERIC,
    actual_work_days BIGINT,
    average_daily_hours NUMERIC,
    client_list TEXT[],
    task_list TEXT[],
    utilization_percentage NUMERIC,
    productivity_score NUMERIC,
    performance_rating TEXT,
    total_entries BIGINT,
    billable_hours NUMERIC,
    overtime_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        emp.employee_id,
        emp.employee_name,
        emp.full_name,
        emp.work_start_date,
        emp.work_end_date,
        emp.total_work_hours,
        emp.actual_work_days,
        emp.average_daily_hours,
        emp.client_list,
        emp.task_list,
        emp.utilization_percentage,
        emp.productivity_score,
        emp.performance_rating,
        emp.total_entries,
        emp.billable_hours,
        emp.overtime_hours
    FROM get_comprehensive_employee_analytics(start_date_param, end_date_param) emp
    WHERE emp.employee_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get individual employee productivity metrics
CREATE OR REPLACE FUNCTION get_individual_productivity_metrics(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    employee_id BIGINT,
    employee_name TEXT,
    total_hours NUMERIC,
    days_worked BIGINT,
    daily_average NUMERIC,
    productivity_score NUMERIC,
    utilization_percentage NUMERIC,
    overtime_hours NUMERIC,
    performance_rating TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        emp.employee_id,
        emp.employee_name,
        emp.total_work_hours as total_hours,
        emp.actual_work_days as days_worked,
        emp.average_daily_hours as daily_average,
        emp.productivity_score,
        emp.utilization_percentage,
        emp.overtime_hours,
        emp.performance_rating
    FROM get_comprehensive_employee_analytics(start_date_param, end_date_param) emp
    WHERE emp.employee_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get individual employee client distribution
CREATE OR REPLACE FUNCTION get_individual_client_distribution(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    client_name TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    days_worked BIGINT,
    average_hours_per_day NUMERIC,
    percentage_of_total NUMERIC
) AS $$
DECLARE
    v_total_hours NUMERIC;
BEGIN
    -- Get total hours for this employee
    SELECT COALESCE(SUM(t.duration) / 3600.0, 0) INTO v_total_hours
    FROM timesheets t
    WHERE t.user_id = user_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param);
    
    RETURN QUERY
    SELECT 
        j.name as client_name,
        ROUND(COALESCE(SUM(t.duration) / 3600.0, 0), 2) as total_hours,
        ROUND(COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0), 2) as billable_hours,
        COUNT(DISTINCT t.date) as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                ROUND(COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date), 2)
            ELSE 0
        END as average_hours_per_day,
        CASE 
            WHEN v_total_hours > 0 THEN 
                ROUND((COALESCE(SUM(t.duration) / 3600.0, 0) / v_total_hours * 100), 2)
            ELSE 0
        END as percentage_of_total
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE t.user_id = user_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY j.name, j.billable
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get individual employee task distribution
CREATE OR REPLACE FUNCTION get_individual_task_distribution(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    task_name TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    days_worked BIGINT,
    average_hours_per_day NUMERIC,
    percentage_of_total NUMERIC
) AS $$
DECLARE
    v_total_hours NUMERIC;
BEGIN
    -- Get total hours for this employee
    SELECT COALESCE(SUM(t.duration) / 3600.0, 0) INTO v_total_hours
    FROM timesheets t
    WHERE t.user_id = user_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param);
    
    RETURN QUERY
    SELECT 
        COALESCE(p.name, j.name, 'General Work') as task_name,
        ROUND(COALESCE(SUM(t.duration) / 3600.0, 0), 2) as total_hours,
        ROUND(COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0), 2) as billable_hours,
        COUNT(DISTINCT t.date) as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                ROUND(COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date), 2)
            ELSE 0
        END as average_hours_per_day,
        CASE 
            WHEN v_total_hours > 0 THEN 
                ROUND((COALESCE(SUM(t.duration) / 3600.0, 0) / v_total_hours * 100), 2)
            ELSE 0
        END as percentage_of_total
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.user_id = user_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY p.name, j.name, j.billable
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get individual employee daily work summary
CREATE OR REPLACE FUNCTION get_individual_daily_work_summary(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    work_date DATE,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_entries BIGINT,
    unique_clients BIGINT,
    unique_tasks BIGINT,
    avg_hours_per_entry NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.date as work_date,
        ROUND(COALESCE(SUM(t.duration) / 3600.0, 0), 2) as total_hours,
        ROUND(COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0), 2) as billable_hours,
        COUNT(t.id) as total_entries,
        COUNT(DISTINCT j.id) as unique_clients,
        COUNT(DISTINCT COALESCE(p.id, j.id)) as unique_tasks,
        CASE 
            WHEN COUNT(t.id) > 0 THEN 
                ROUND(COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id), 2)
            ELSE 0
        END as avg_hours_per_entry
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.user_id = user_id_param
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    GROUP BY t.date
    ORDER BY t.date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get individual employee weekly work summary
CREATE OR REPLACE FUNCTION get_individual_weekly_work_summary(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    work_week DATE,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    total_entries BIGINT,
    unique_clients BIGINT,
    unique_tasks BIGINT,
    days_worked BIGINT,
    avg_hours_per_day NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH daily_data AS (
        SELECT 
            t.date,
            t.duration,
            j.billable,
            j.id as jobcode_id,
            p.id as project_id
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = user_id_param
            AND (start_date_param IS NULL OR t.date >= start_date_param)
            AND (end_date_param IS NULL OR t.date <= end_date_param)
    ),
    weekly_data AS (
        SELECT 
            (date - INTERVAL '1 day' * EXTRACT(DOW FROM date))::DATE as work_week,
            SUM(duration) as total_duration,
            SUM(CASE WHEN billable THEN duration ELSE 0 END) as billable_duration,
            COUNT(*) as total_entries,
            COUNT(DISTINCT jobcode_id) as unique_clients,
            COUNT(DISTINCT COALESCE(project_id, jobcode_id)) as unique_tasks,
            COUNT(DISTINCT date) as days_worked
        FROM daily_data
        GROUP BY (date - INTERVAL '1 day' * EXTRACT(DOW FROM date))::DATE
    )
    SELECT 
        wd.work_week,
        ROUND(COALESCE(wd.total_duration / 3600.0, 0), 2) as total_hours,
        ROUND(COALESCE(wd.billable_duration / 3600.0, 0), 2) as billable_hours,
        wd.total_entries,
        wd.unique_clients,
        wd.unique_tasks,
        wd.days_worked,
        CASE 
            WHEN wd.days_worked > 0 THEN 
                ROUND(COALESCE(wd.total_duration / 3600.0, 0) / wd.days_worked, 2)
            ELSE 0
        END as avg_hours_per_day
    FROM weekly_data wd
    ORDER BY wd.work_week DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- DEPLOYMENT COMPLETE
-- ==============================================
-- All individual employee functions have been deployed
-- You can now test them using the Supabase SQL Editor:
-- 
-- Test examples:
-- SELECT * FROM get_individual_employee_summary(1, '2024-01-01', '2024-12-31');
-- SELECT * FROM get_individual_productivity_metrics(1);
-- SELECT * FROM get_individual_client_distribution(1);
-- SELECT * FROM get_individual_task_distribution(1);
-- SELECT * FROM get_individual_daily_work_summary(1);
-- SELECT * FROM get_individual_weekly_work_summary(1);
