-- ==============================================
-- EMPLOYEE ANALYTICS SQL FUNCTIONS
-- Complete integration with Employee_Analytics.py
-- ==============================================

-- Function 1: Get employee summary data (First Table)
CREATE OR REPLACE FUNCTION get_employee_summary_data(
    p_user_id BIGINT DEFAULT NULL,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
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
    custom_field_values TEXT[]
) AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF p_start_date IS NULL THEN
        SELECT MIN(t.date) INTO v_start_date 
        FROM timesheets t 
        WHERE t.user_id = COALESCE(p_user_id, t.user_id);
    ELSE
        v_start_date := p_start_date;
    END IF;
    
    IF p_end_date IS NULL THEN
        SELECT MAX(t.date) INTO v_end_date 
        FROM timesheets t 
        WHERE t.user_id = COALESCE(p_user_id, t.user_id);
    ELSE
        v_end_date := p_end_date;
    END IF;
    
    RETURN QUERY
    WITH employee_summary AS (
        SELECT 
            u.id as employee_id,
            u.username as employee_name,
            COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as full_name,
            v_start_date as work_start_date,
            v_end_date as work_end_date,
            COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_work_hours,
            COUNT(DISTINCT t.date)::BIGINT as actual_work_days,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
                ELSE 0::NUMERIC
            END as average_daily_hours
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id 
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
        WHERE u.id = COALESCE(p_user_id, u.id)
        GROUP BY u.id, u.username, u.display_name, u.first_name, u.last_name
    ),
    employee_clients AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT j.name ORDER BY j.name) as clients
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE t.user_id = COALESCE(p_user_id, t.user_id)
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
        GROUP BY t.user_id
    ),
    employee_tasks AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT COALESCE(p.name, j.name) ORDER BY COALESCE(p.name, j.name)) as tasks
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = COALESCE(p_user_id, t.user_id)
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
        GROUP BY t.user_id
    ),
    employee_custom_fields AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) as custom_fields
        FROM timesheets t
        JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        JOIN custom_fields cf ON cfv.customfield_id = cf.id
        WHERE t.user_id = COALESCE(p_user_id, t.user_id)
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
            AND cfv.value IS NOT NULL
        GROUP BY t.user_id
    )
    SELECT 
        es.employee_id,
        es.employee_name,
        es.full_name,
        es.work_start_date,
        es.work_end_date,
        es.total_work_hours,
        es.actual_work_days,
        es.average_daily_hours,
        COALESCE(ec.clients, ARRAY[]::TEXT[]) as client_list,
        COALESCE(et.tasks, ARRAY[]::TEXT[]) as task_list,
        COALESCE(ecf.custom_fields, ARRAY[]::TEXT[]) as custom_field_values
    FROM employee_summary es
    LEFT JOIN employee_clients ec ON es.employee_id = ec.user_id
    LEFT JOIN employee_tasks et ON es.employee_id = et.user_id
    LEFT JOIN employee_custom_fields ecf ON es.employee_id = ecf.user_id
    ORDER BY es.total_work_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Get daily work breakdown (Second Table - Daily)
CREATE OR REPLACE FUNCTION get_employee_daily_work_data(
    p_user_id BIGINT,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    work_date DATE,
    client_name TEXT,
    task_name TEXT,
    hours_worked NUMERIC,
    job_code TEXT,
    custom_field_items TEXT[]
) AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF p_start_date IS NULL THEN
        SELECT MIN(t.date) INTO v_start_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_start_date := p_start_date;
    END IF;
    
    IF p_end_date IS NULL THEN
        SELECT MAX(t.date) INTO v_end_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_end_date := p_end_date;
    END IF;
    
    RETURN QUERY
    WITH daily_work_data AS (
        SELECT 
            t.date as work_date,
            j.name as client_name,
            COALESCE(p.name, j.name) as task_name,
            t.duration / 3600.0 as hours_worked,
            j.short_code as job_code,
            t.id as timesheet_id
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = p_user_id
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
    ),
    daily_custom_fields AS (
        SELECT 
            t.date as work_date,
            j.name as client_name,
            COALESCE(p.name, j.name) as task_name,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) as custom_field_items
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        JOIN custom_fields cf ON cfv.customfield_id = cf.id
        WHERE t.user_id = p_user_id
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
            AND cfv.value IS NOT NULL
        GROUP BY t.date, j.name, p.name
    )
    SELECT 
        dwd.work_date,
        dwd.client_name,
        dwd.task_name,
        dwd.hours_worked,
        dwd.job_code,
        COALESCE(dcf.custom_field_items, ARRAY[]::TEXT[]) as custom_field_items
    FROM daily_work_data dwd
    LEFT JOIN daily_custom_fields dcf ON dwd.work_date = dcf.work_date 
        AND dwd.client_name = dcf.client_name 
        AND dwd.task_name = dcf.task_name
    ORDER BY dwd.work_date DESC, dwd.client_name, dwd.task_name;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Get weekly work breakdown (Second Table - Weekly)
CREATE OR REPLACE FUNCTION get_employee_weekly_work_data(
    p_user_id BIGINT,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    work_week DATE,
    client_name TEXT,
    task_name TEXT,
    hours_worked NUMERIC,
    job_code TEXT,
    custom_field_items TEXT[]
) AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF p_start_date IS NULL THEN
        SELECT MIN(t.date) INTO v_start_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_start_date := p_start_date;
    END IF;
    
    IF p_end_date IS NULL THEN
        SELECT MAX(t.date) INTO v_end_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_end_date := p_end_date;
    END IF;
    
    RETURN QUERY
    WITH weekly_work_data AS (
        SELECT 
            DATE_TRUNC('week', t.date)::DATE as work_week,
            j.name as client_name,
            COALESCE(p.name, j.name) as task_name,
            SUM(t.duration) / 3600.0 as hours_worked,
            j.short_code as job_code
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = p_user_id
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
        GROUP BY DATE_TRUNC('week', t.date), j.name, p.name, j.short_code
    ),
    weekly_custom_fields AS (
        SELECT 
            DATE_TRUNC('week', t.date)::DATE as work_week,
            j.name as client_name,
            COALESCE(p.name, j.name) as task_name,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) as custom_field_items
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        JOIN custom_fields cf ON cfv.customfield_id = cf.id
        WHERE t.user_id = p_user_id
            AND (t.date >= v_start_date OR v_start_date IS NULL)
            AND (t.date <= v_end_date OR v_end_date IS NULL)
            AND cfv.value IS NOT NULL
        GROUP BY DATE_TRUNC('week', t.date), j.name, p.name
    )
    SELECT 
        wwd.work_week,
        wwd.client_name,
        wwd.task_name,
        wwd.hours_worked,
        wwd.job_code,
        COALESCE(wcf.custom_field_items, ARRAY[]::TEXT[]) as custom_field_items
    FROM weekly_work_data wwd
    LEFT JOIN weekly_custom_fields wcf ON wwd.work_week = wcf.work_week 
        AND wwd.client_name = wcf.client_name 
        AND wwd.task_name = wcf.task_name
    ORDER BY wwd.work_week DESC, wwd.client_name, wwd.task_name;
END;
$$ LANGUAGE plpgsql;

-- Function 4: Get all employees summary (for dashboard overview)
CREATE OR REPLACE FUNCTION get_all_employees_summary(
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
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
    custom_field_values TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM get_employee_summary_data(NULL, p_start_date, p_end_date);
END;
$$ LANGUAGE plpgsql;

-- Function 5: Get employee productivity metrics
CREATE OR REPLACE FUNCTION get_employee_productivity_metrics(
    p_user_id BIGINT,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    employee_id BIGINT,
    employee_name TEXT,
    total_hours NUMERIC,
    days_worked BIGINT,
    daily_average NUMERIC,
    productivity_score NUMERIC,
    utilization_percentage NUMERIC,
    overtime_hours NUMERIC
) AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
    v_total_hours NUMERIC;
    v_days_worked BIGINT;
    v_daily_average NUMERIC;
    v_productivity_score NUMERIC;
    v_utilization_percentage NUMERIC;
    v_overtime_hours NUMERIC;
BEGIN
    -- Set default date range if not provided
    IF p_start_date IS NULL THEN
        SELECT MIN(t.date) INTO v_start_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_start_date := p_start_date;
    END IF;
    
    IF p_end_date IS NULL THEN
        SELECT MAX(t.date) INTO v_end_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_end_date := p_end_date;
    END IF;
    
    -- Get basic metrics
    SELECT 
        COALESCE(SUM(t.duration) / 3600.0, 0),
        COUNT(DISTINCT t.date),
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))
            ELSE 0
        END
    INTO v_total_hours, v_days_worked, v_daily_average
    FROM timesheets t
    WHERE t.user_id = p_user_id
        AND t.date >= v_start_date 
        AND t.date <= v_end_date;
    
    -- Calculate productivity score (0-100)
    v_productivity_score := LEAST(100, (v_daily_average / 8.0) * 100);
    
    -- Calculate utilization percentage
    v_utilization_percentage := (v_daily_average / 8.0) * 100;
    
    -- Calculate overtime hours
    v_overtime_hours := GREATEST(0, v_daily_average - 8.0) * v_days_worked;
    
    RETURN QUERY
    SELECT 
        u.id as employee_id,
        u.username as employee_name,
        v_total_hours,
        v_days_worked,
        v_daily_average,
        v_productivity_score,
        v_utilization_percentage,
        v_overtime_hours
    FROM users u
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function 6: Get employee performance rating
CREATE OR REPLACE FUNCTION get_employee_performance_rating(
    p_user_id BIGINT,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    v_daily_average NUMERIC;
    v_performance_rating TEXT;
BEGIN
    SELECT 
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))
            ELSE 0
        END
    INTO v_daily_average
    FROM timesheets t
    WHERE t.user_id = p_user_id
        AND (t.date >= p_start_date OR p_start_date IS NULL)
        AND (t.date <= p_end_date OR p_end_date IS NULL);
    
    IF v_daily_average >= 8.0 THEN
        v_performance_rating := 'Excellent';
    ELSIF v_daily_average >= 6.0 THEN
        v_performance_rating := 'Good';
    ELSIF v_daily_average >= 4.0 THEN
        v_performance_rating := 'Average';
    ELSE
        v_performance_rating := 'Needs Improvement';
    END IF;
    
    RETURN v_performance_rating;
END;
$$ LANGUAGE plpgsql;

-- Function 7: Calculate working days (excluding weekends)
CREATE OR REPLACE FUNCTION calculate_working_days(
    p_start_date DATE,
    p_end_date DATE
)
RETURNS INTEGER AS $$
DECLARE
    day_count INTEGER := 0;
    current_day DATE := p_start_date;
BEGIN
    WHILE current_day <= p_end_date LOOP
        -- Check if it's not a weekend (Saturday = 6, Sunday = 0)
        IF EXTRACT(DOW FROM current_day) NOT IN (0, 6) THEN
            day_count := day_count + 1;
        END IF;
        current_day := current_day + INTERVAL '1 day';
    END LOOP;
    
    RETURN day_count;
END;
$$ LANGUAGE plpgsql;

-- Function 8: Get employee client distribution
CREATE OR REPLACE FUNCTION get_employee_client_distribution(
    p_user_id BIGINT,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
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
    v_start_date DATE;
    v_end_date DATE;
    v_total_user_hours NUMERIC;
BEGIN
    -- Set default date range if not provided
    IF p_start_date IS NULL THEN
        SELECT MIN(t.date) INTO v_start_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_start_date := p_start_date;
    END IF;
    
    IF p_end_date IS NULL THEN
        SELECT MAX(t.date) INTO v_end_date FROM timesheets t WHERE t.user_id = p_user_id;
    ELSE
        v_end_date := p_end_date;
    END IF;
    
    -- Get total hours for percentage calculation
    SELECT COALESCE(SUM(t.duration) / 3600.0, 0) INTO v_total_user_hours
    FROM timesheets t
    WHERE t.user_id = p_user_id
        AND t.date >= v_start_date 
        AND t.date <= v_end_date;
    
    RETURN QUERY
    SELECT 
        j.name as client_name,
        COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
        COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0)::NUMERIC as billable_hours,
        COUNT(DISTINCT t.date)::BIGINT as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
            ELSE 0::NUMERIC
        END as average_hours_per_day,
        CASE 
            WHEN v_total_user_hours > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / v_total_user_hours * 100)::NUMERIC
            ELSE 0::NUMERIC
        END as percentage_of_total
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE t.user_id = p_user_id
        AND t.date >= v_start_date 
        AND t.date <= v_end_date
    GROUP BY j.name, j.billable
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Create optimized indexes for better performance
CREATE INDEX IF NOT EXISTS idx_timesheets_user_date_analytics ON timesheets(user_id, date) WHERE date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_timesheets_jobcode_analytics ON timesheets(jobcode_id) WHERE jobcode_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_timesheet_customfield_values_analytics ON timesheet_customfield_values(timesheet_id, customfield_id);
CREATE INDEX IF NOT EXISTS idx_jobcodes_name_analytics ON jobcodes(name) WHERE name IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_projects_jobcode_analytics ON projects(jobcode_id) WHERE jobcode_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_active_analytics ON users(id) WHERE active = true;

-- ==============================================
-- VIEWS FOR EASY ACCESS
-- ==============================================

-- View for all employees summary
CREATE OR REPLACE VIEW v_all_employees_summary AS
SELECT * FROM get_all_employees_summary();

-- View for daily work breakdown (all employees)
CREATE OR REPLACE VIEW v_daily_work_all_employees AS
SELECT 
    t.user_id,
    u.username,
    t.date as work_date,
    j.name as client_name,
    COALESCE(p.name, j.name) as task_name,
    t.duration / 3600.0 as hours_worked,
    j.short_code as job_code
FROM timesheets t
JOIN users u ON t.user_id = u.id
JOIN jobcodes j ON t.jobcode_id = j.id
LEFT JOIN projects p ON j.id = p.jobcode_id
ORDER BY t.user_id, t.date DESC;

-- View for weekly work breakdown (all employees)
CREATE OR REPLACE VIEW v_weekly_work_all_employees AS
SELECT 
    t.user_id,
    u.username,
    DATE_TRUNC('week', t.date)::DATE as work_week,
    j.name as client_name,
    COALESCE(p.name, j.name) as task_name,
    SUM(t.duration) / 3600.0 as hours_worked,
    j.short_code as job_code
FROM timesheets t
JOIN users u ON t.user_id = u.id
JOIN jobcodes j ON t.jobcode_id = j.id
LEFT JOIN projects p ON j.id = p.jobcode_id
GROUP BY t.user_id, u.username, DATE_TRUNC('week', t.date), j.name, p.name, j.short_code
ORDER BY t.user_id, work_week DESC;

-- ==============================================
-- EXAMPLE USAGE QUERIES
-- ==============================================

-- Example 1: Get summary for all employees
-- SELECT * FROM get_all_employees_summary('2024-01-01', '2024-12-31');

-- Example 2: Get summary for specific employee
-- SELECT * FROM get_employee_summary_data(503759, '2024-01-01', '2024-12-31');

-- Example 3: Get daily breakdown for specific employee
-- SELECT * FROM get_employee_daily_work_data(503759, '2024-01-01', '2024-12-31');

-- Example 4: Get weekly breakdown for specific employee
-- SELECT * FROM get_employee_weekly_work_data(503759, '2024-01-01', '2024-12-31');

-- Example 5: Get productivity metrics for specific employee
-- SELECT * FROM get_employee_productivity_metrics(503759, '2024-01-01', '2024-12-31');

-- Example 6: Get performance rating for specific employee
-- SELECT get_employee_performance_rating(503759, '2024-01-01', '2024-12-31');

-- Example 7: Get client distribution for specific employee
-- SELECT * FROM get_employee_client_distribution(503759, '2024-01-01', '2024-12-31');

-- Example 8: Calculate working days
-- SELECT calculate_working_days('2024-01-01', '2024-01-31');

-- ==============================================
-- DATA VALIDATION QUERIES
-- ==============================================

-- Check if all employees have data
-- SELECT 
--     COUNT(*) as total_employees,
--     COUNT(CASE WHEN total_work_hours > 0 THEN 1 END) as employees_with_data,
--     COUNT(CASE WHEN total_work_hours = 0 THEN 1 END) as employees_without_data
-- FROM get_all_employees_summary('2024-01-01', '2024-12-31');

-- Check data consistency
-- SELECT 
--     employee_id,
--     employee_name,
--     total_work_hours,
--     actual_work_days,
--     average_daily_hours,
--     CASE 
--         WHEN actual_work_days > 0 AND ABS(total_work_hours - (average_daily_hours * actual_work_days)) > 0.01 THEN 'INCONSISTENT'
--         ELSE 'OK'
--     END as data_consistency
-- FROM get_all_employees_summary('2024-01-01', '2024-12-31')
-- WHERE total_work_hours > 0;
