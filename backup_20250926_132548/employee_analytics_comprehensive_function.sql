-- ==============================================
-- COMPREHENSIVE EMPLOYEE ANALYTICS FUNCTION
-- ==============================================
-- This function replaces complex Python queries with a single efficient SQL function

CREATE OR REPLACE FUNCTION get_comprehensive_employee_analytics(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    -- Employee basic info
    employee_id BIGINT,
    employee_name TEXT,
    full_name TEXT,
    work_start_date DATE,
    work_end_date DATE,
    
    -- Hours and work metrics
    total_work_hours NUMERIC,
    actual_work_days BIGINT,
    average_daily_hours NUMERIC,
    
    -- Client and project info
    client_list TEXT[],
    task_list TEXT[],
    
    -- Performance metrics
    utilization_percentage NUMERIC,
    productivity_score NUMERIC,
    performance_rating TEXT,
    
    -- Additional metrics
    total_entries BIGINT,
    billable_hours NUMERIC,
    overtime_hours NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH employee_work_data AS (
        SELECT 
            u.id as employee_id,
            u.username as employee_name,
            COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as full_name,
            
            -- Calculate total hours and work days
            ROUND(COALESCE(SUM(t.duration) / 3600.0, 0), 2) as total_work_hours,
            COUNT(DISTINCT t.date) as actual_work_days,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    ROUND(COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date), 2)
                ELSE 0
            END as average_daily_hours,
            
            -- Count total entries
            COUNT(t.id) as total_entries,
            
            -- Calculate billable hours (assuming all are billable for now)
            ROUND(COALESCE(SUM(t.duration) / 3600.0, 0), 2) as billable_hours,
            
            -- Calculate overtime hours (hours over 8 per day)
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    GREATEST(0, (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)) - 8) * COUNT(DISTINCT t.date)
                ELSE 0
            END as overtime_hours,
            
            -- Date range
            MIN(t.date) as work_start_date,
            MAX(t.date) as work_end_date
            
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id 
            AND (start_date_param IS NULL OR t.date >= start_date_param)
            AND (end_date_param IS NULL OR t.date <= end_date_param)
        WHERE u.active = true
        GROUP BY u.id, u.username, u.display_name, u.first_name, u.last_name
    ),
    
    employee_clients AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT j.name ORDER BY j.name) as clients
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE (start_date_param IS NULL OR t.date >= start_date_param)
            AND (end_date_param IS NULL OR t.date <= end_date_param)
        GROUP BY t.user_id
    ),
    
    employee_tasks AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT COALESCE(p.name, j.name) ORDER BY COALESCE(p.name, j.name)) as tasks
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE (start_date_param IS NULL OR t.date >= start_date_param)
            AND (end_date_param IS NULL OR t.date <= end_date_param)
        GROUP BY t.user_id
    )
    
    SELECT 
        ewd.employee_id,
        ewd.employee_name,
        ewd.full_name,
        ewd.work_start_date,
        ewd.work_end_date,
        ewd.total_work_hours,
        ewd.actual_work_days,
        ewd.average_daily_hours,
        COALESCE(ec.clients, ARRAY[]::TEXT[]) as client_list,
        COALESCE(et.tasks, ARRAY[]::TEXT[]) as task_list,
        
        -- Calculate utilization percentage (daily hours / 8 * 100)
        CASE 
            WHEN ewd.average_daily_hours > 0 THEN 
                LEAST(100.0, (ewd.average_daily_hours / 8.0) * 100)
            ELSE 0
        END as utilization_percentage,
        
        -- Calculate productivity score (efficiency + consistency)
        CASE 
            WHEN ewd.average_daily_hours > 0 THEN 
                LEAST(100.0, (ewd.average_daily_hours / 8.0) * 100)
            ELSE 0
        END as productivity_score,
        
        -- Performance rating based on daily hours
        CASE 
            WHEN ewd.average_daily_hours >= 8.0 THEN 'Excellent'
            WHEN ewd.average_daily_hours >= 6.0 THEN 'Good'
            WHEN ewd.average_daily_hours >= 4.0 THEN 'Average'
            ELSE 'Needs Improvement'
        END as performance_rating,
        
        ewd.total_entries,
        ewd.billable_hours,
        ewd.overtime_hours
        
    FROM employee_work_data ewd
    LEFT JOIN employee_clients ec ON ewd.employee_id = ec.user_id
    LEFT JOIN employee_tasks et ON ewd.employee_id = et.user_id
    WHERE ewd.total_work_hours > 0  -- Only include employees with work hours
    ORDER BY ewd.total_work_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- KPI CALCULATION FUNCTION
-- ==============================================

CREATE OR REPLACE FUNCTION get_employee_kpis_comprehensive(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    total_employees BIGINT,
    avg_daily_hours_per_employee NUMERIC,
    avg_utilization NUMERIC,
    team_productivity NUMERIC,
    overtime_percentage NUMERIC,
    total_hours_all_employees NUMERIC
) AS $$
DECLARE
    v_total_employees BIGINT;
    v_avg_daily_hours NUMERIC;
    v_avg_utilization NUMERIC;
    v_team_productivity NUMERIC;
    v_overtime_pct NUMERIC;
    v_total_hours NUMERIC;
    v_daily_averages NUMERIC[];
    v_utilizations NUMERIC[];
    v_efficiency_scores NUMERIC[];
    v_variance NUMERIC;
    v_consistency_score NUMERIC;
    v_overtime_hours NUMERIC;
BEGIN
    -- Get basic counts and totals
    SELECT 
        COUNT(*),
        COALESCE(AVG(average_daily_hours), 0),
        COALESCE(SUM(total_work_hours), 0),
        COALESCE(SUM(overtime_hours), 0)
    INTO 
        v_total_employees,
        v_avg_daily_hours,
        v_total_hours,
        v_overtime_hours
    FROM get_comprehensive_employee_analytics(start_date_param, end_date_param);
    
    -- Calculate utilization (average of individual utilizations)
    SELECT ARRAY_AGG(utilization_percentage)
    INTO v_utilizations
    FROM get_comprehensive_employee_analytics(start_date_param, end_date_param)
    WHERE utilization_percentage > 0;
    
    IF v_utilizations IS NOT NULL AND array_length(v_utilizations, 1) > 0 THEN
        v_avg_utilization := (SELECT AVG(util) FROM unnest(v_utilizations) AS util);
    ELSE
        v_avg_utilization := 0;
    END IF;
    
    -- Calculate team productivity (efficiency + consistency)
    SELECT ARRAY_AGG(average_daily_hours)
    INTO v_daily_averages
    FROM get_comprehensive_employee_analytics(start_date_param, end_date_param)
    WHERE average_daily_hours > 0;
    
    IF v_daily_averages IS NOT NULL AND array_length(v_daily_averages, 1) > 0 THEN
        -- Efficiency scores
        SELECT ARRAY_AGG(LEAST(100.0, (avg_hours / 8.0) * 100))
        INTO v_efficiency_scores
        FROM unnest(v_daily_averages) AS avg_hours;
        
        -- Calculate variance for consistency
        IF array_length(v_daily_averages, 1) > 1 THEN
            v_variance := (
                SELECT AVG((avg_hours - (SELECT AVG(avg_hours) FROM unnest(v_daily_averages) AS avg_hours))^2)
                FROM unnest(v_daily_averages) AS avg_hours
            );
            v_consistency_score := GREATEST(0, 100 - (v_variance * 10));
        ELSE
            v_consistency_score := 100;
        END IF;
        
        -- Weighted productivity score
        v_team_productivity := (
            (SELECT AVG(score) FROM unnest(v_efficiency_scores) AS score) * 0.7 + 
            v_consistency_score * 0.3
        );
        v_team_productivity := LEAST(v_team_productivity, 100.0);
    ELSE
        v_team_productivity := 0;
    END IF;
    
    -- Calculate overtime percentage
    v_overtime_pct := CASE 
        WHEN v_total_hours > 0 THEN (v_overtime_hours / v_total_hours) * 100
        ELSE 0
    END;
    
    RETURN QUERY SELECT 
        v_total_employees,
        ROUND(v_avg_daily_hours, 2),
        ROUND(v_avg_utilization, 2),
        ROUND(v_team_productivity, 2),
        ROUND(v_overtime_pct, 2),
        ROUND(v_total_hours, 2);
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- INDIVIDUAL EMPLOYEE DETAILED DATA FUNCTION
-- ==============================================

CREATE OR REPLACE FUNCTION get_employee_detailed_data(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    work_date DATE,
    client_name TEXT,
    task_name TEXT,
    hours_worked NUMERIC,
    job_code TEXT,
    billable BOOLEAN
) AS $$
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
    ORDER BY t.date DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Create optimized indexes for better performance
CREATE INDEX IF NOT EXISTS idx_timesheets_user_date_analytics ON timesheets(user_id, date) WHERE date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_timesheets_date_analytics ON timesheets(date) WHERE date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobcodes_active ON jobcodes(id) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_users_active ON users(id) WHERE active = true;

-- ==============================================
-- INDIVIDUAL EMPLOYEE INSIGHTS FUNCTIONS
-- ==============================================

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
-- USAGE EXAMPLES
-- ==============================================

-- Get all employee analytics
-- SELECT * FROM get_comprehensive_employee_analytics();

-- Get employee analytics for date range
-- SELECT * FROM get_comprehensive_employee_analytics('2024-01-01', '2024-12-31');

-- Get KPIs
-- SELECT * FROM get_employee_kpis_comprehensive();

-- Get individual employee data
-- SELECT * FROM get_employee_detailed_data(12345);

-- Get individual employee summary
-- SELECT * FROM get_individual_employee_summary(12345);

-- Get individual productivity metrics
-- SELECT * FROM get_individual_productivity_metrics(12345);

-- Get individual client distribution
-- SELECT * FROM get_individual_client_distribution(12345);

-- Get individual task distribution
-- SELECT * FROM get_individual_task_distribution(12345);

-- Get individual daily work summary
-- SELECT * FROM get_individual_daily_work_summary(12345);

-- Get individual weekly work summary
-- SELECT * FROM get_individual_weekly_work_summary(12345);
