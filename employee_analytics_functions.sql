-- ==============================================
-- EMPLOYEE ANALYTICS DATA FUNCTIONS
-- Redesigned data structure for frontend requirements
-- ==============================================

-- Function 1: Get user summary data (First Table)
-- Returns: user, start_date, end_date, daily_average, list_of_clients, list_of_tasks
CREATE OR REPLACE FUNCTION get_user_summary_analytics(
    user_id_param BIGINT DEFAULT NULL,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    display_name TEXT,
    start_date DATE,
    end_date DATE,
    total_hours NUMERIC,
    days_worked BIGINT,
    daily_average NUMERIC,
    list_of_clients TEXT[],
    list_of_tasks TEXT[],
    custom_field_items TEXT[]
) AS $$
DECLARE
    actual_start_date DATE;
    actual_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF start_date_param IS NULL THEN
        SELECT MIN(t.date) INTO actual_start_date FROM timesheets t WHERE t.user_id = COALESCE(user_id_param, t.user_id);
    ELSE
        actual_start_date := start_date_param;
    END IF;
    
    IF end_date_param IS NULL THEN
        SELECT MAX(t.date) INTO actual_end_date FROM timesheets t WHERE t.user_id = COALESCE(user_id_param, t.user_id);
    ELSE
        actual_end_date := end_date_param;
    END IF;
    
    RETURN QUERY
    WITH user_data AS (
        SELECT 
            u.id as user_id,
            u.username,
            COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
            COALESCE(actual_start_date, MIN(t.date)) as start_date,
            COALESCE(actual_end_date, MAX(t.date)) as end_date,
            COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
            COUNT(DISTINCT t.date)::BIGINT as days_worked,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
                ELSE 0::NUMERIC
            END as daily_average
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id 
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
        WHERE u.id = COALESCE(user_id_param, u.id)
        GROUP BY u.id, u.username, u.display_name, u.first_name, u.last_name
    ),
    client_data AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT j.name ORDER BY j.name) as clients
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        WHERE t.user_id = COALESCE(user_id_param, t.user_id)
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
        GROUP BY t.user_id
    ),
    task_data AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT COALESCE(p.name, j.name) ORDER BY COALESCE(p.name, j.name)) as tasks
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = COALESCE(user_id_param, t.user_id)
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
        GROUP BY t.user_id
    ),
    custom_field_data AS (
        SELECT 
            t.user_id,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) as custom_fields
        FROM timesheets t
        JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        JOIN custom_fields cf ON cfv.customfield_id = cf.id
        WHERE t.user_id = COALESCE(user_id_param, t.user_id)
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
            AND cfv.value IS NOT NULL
        GROUP BY t.user_id
    )
    SELECT 
        ud.user_id,
        ud.username,
        ud.display_name,
        ud.start_date,
        ud.end_date,
        ud.total_hours,
        ud.days_worked,
        ud.daily_average,
        COALESCE(cd.clients, ARRAY[]::TEXT[]) as list_of_clients,
        COALESCE(td.tasks, ARRAY[]::TEXT[]) as list_of_tasks,
        COALESCE(cfd.custom_fields, ARRAY[]::TEXT[]) as custom_field_items
    FROM user_data ud
    LEFT JOIN client_data cd ON ud.user_id = cd.user_id
    LEFT JOIN task_data td ON ud.user_id = td.user_id
    LEFT JOIN custom_field_data cfd ON ud.user_id = cfd.user_id
    ORDER BY ud.total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Get daily work breakdown for a specific user (Second Table - Daily)
CREATE OR REPLACE FUNCTION get_user_daily_breakdown(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    work_date DATE,
    client TEXT,
    task TEXT,
    hours NUMERIC,
    job_code TEXT,
    custom_field_items TEXT[]
) AS $$
DECLARE
    actual_start_date DATE;
    actual_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF start_date_param IS NULL THEN
        SELECT MIN(t.date) INTO actual_start_date FROM timesheets t WHERE t.user_id = user_id_param;
    ELSE
        actual_start_date := start_date_param;
    END IF;
    
    IF end_date_param IS NULL THEN
        SELECT MAX(t.date) INTO actual_end_date FROM timesheets t WHERE t.user_id = user_id_param;
    ELSE
        actual_end_date := end_date_param;
    END IF;
    
    RETURN QUERY
    WITH daily_work AS (
        SELECT 
            t.date as work_date,
            j.name as client,
            COALESCE(p.name, j.name) as task,
            t.duration / 3600.0 as hours,
            j.short_code as job_code,
            t.id as timesheet_id
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = user_id_param
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
    ),
    custom_fields AS (
        SELECT 
            t.date as work_date,
            j.name as client,
            COALESCE(p.name, j.name) as task,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) as custom_field_items
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        JOIN custom_fields cf ON cfv.customfield_id = cf.id
        WHERE t.user_id = user_id_param
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
            AND cfv.value IS NOT NULL
        GROUP BY t.date, j.name, p.name
    )
    SELECT 
        dw.work_date,
        dw.client,
        dw.task,
        dw.hours,
        dw.job_code,
        COALESCE(cf.custom_field_items, ARRAY[]::TEXT[]) as custom_field_items
    FROM daily_work dw
    LEFT JOIN custom_fields cf ON dw.work_date = cf.work_date 
        AND dw.client = cf.client 
        AND dw.task = cf.task
    ORDER BY dw.work_date DESC, dw.client, dw.task;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Get weekly work breakdown for a specific user (Second Table - Weekly)
CREATE OR REPLACE FUNCTION get_user_weekly_breakdown(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    work_week DATE,
    client TEXT,
    task TEXT,
    hours NUMERIC,
    job_code TEXT,
    custom_field_items TEXT[]
) AS $$
DECLARE
    actual_start_date DATE;
    actual_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF start_date_param IS NULL THEN
        SELECT MIN(t.date) INTO actual_start_date FROM timesheets t WHERE t.user_id = user_id_param;
    ELSE
        actual_start_date := start_date_param;
    END IF;
    
    IF end_date_param IS NULL THEN
        SELECT MAX(t.date) INTO actual_end_date FROM timesheets t WHERE t.user_id = user_id_param;
    ELSE
        actual_end_date := end_date_param;
    END IF;
    
    RETURN QUERY
    WITH weekly_work AS (
        SELECT 
            DATE_TRUNC('week', t.date)::DATE as work_week,
            j.name as client,
            COALESCE(p.name, j.name) as task,
            SUM(t.duration) / 3600.0 as hours,
            j.short_code as job_code
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = user_id_param
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
        GROUP BY DATE_TRUNC('week', t.date), j.name, p.name, j.short_code
    ),
    weekly_custom_fields AS (
        SELECT 
            DATE_TRUNC('week', t.date)::DATE as work_week,
            j.name as client,
            COALESCE(p.name, j.name) as task,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) as custom_field_items
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        JOIN custom_fields cf ON cfv.customfield_id = cf.id
        WHERE t.user_id = user_id_param
            AND (t.date >= actual_start_date OR actual_start_date IS NULL)
            AND (t.date <= actual_end_date OR actual_end_date IS NULL)
            AND cfv.value IS NOT NULL
        GROUP BY DATE_TRUNC('week', t.date), j.name, p.name
    )
    SELECT 
        ww.work_week,
        ww.client,
        ww.task,
        ww.hours,
        ww.job_code,
        COALESCE(wcf.custom_field_items, ARRAY[]::TEXT[]) as custom_field_items
    FROM weekly_work ww
    LEFT JOIN weekly_custom_fields wcf ON ww.work_week = wcf.work_week 
        AND ww.client = wcf.client 
        AND ww.task = wcf.task
    ORDER BY ww.work_week DESC, ww.client, ww.task;
END;
$$ LANGUAGE plpgsql;

-- Function 4: Get comprehensive user analytics (Combines both tables)
CREATE OR REPLACE FUNCTION get_comprehensive_user_analytics(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL,
    period_type TEXT DEFAULT 'daily'
)
RETURNS TABLE (
    -- Summary data (First table)
    user_id BIGINT,
    username TEXT,
    display_name TEXT,
    start_date DATE,
    end_date DATE,
    total_hours NUMERIC,
    days_worked BIGINT,
    daily_average NUMERIC,
    list_of_clients TEXT[],
    list_of_tasks TEXT[],
    custom_field_items TEXT[],
    -- Breakdown data (Second table)
    breakdown_date DATE,
    breakdown_client TEXT,
    breakdown_task TEXT,
    breakdown_hours NUMERIC,
    breakdown_job_code TEXT,
    breakdown_custom_fields TEXT[]
) AS $$
DECLARE
    actual_start_date DATE;
    actual_end_date DATE;
BEGIN
    -- Set default date range if not provided
    IF start_date_param IS NULL THEN
        SELECT MIN(t.date) INTO actual_start_date FROM timesheets t WHERE t.user_id = user_id_param;
    ELSE
        actual_start_date := start_date_param;
    END IF;
    
    IF end_date_param IS NULL THEN
        SELECT MAX(t.date) INTO actual_end_date FROM timesheets t WHERE t.user_id = user_id_param;
    ELSE
        actual_end_date := end_date_param;
    END IF;
    
    RETURN QUERY
    WITH user_summary AS (
        SELECT 
            u.id as user_id,
            u.username,
            COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
            actual_start_date as start_date,
            actual_end_date as end_date,
            COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
            COUNT(DISTINCT t.date)::BIGINT as days_worked,
            CASE 
                WHEN COUNT(DISTINCT t.date) > 0 THEN 
                    (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
                ELSE 0::NUMERIC
            END as daily_average,
            ARRAY_AGG(DISTINCT j.name ORDER BY j.name) as list_of_clients,
            ARRAY_AGG(DISTINCT COALESCE(p.name, j.name) ORDER BY COALESCE(p.name, j.name)) as list_of_tasks,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) FILTER (WHERE cfv.value IS NOT NULL) as custom_field_items
        FROM users u
        LEFT JOIN timesheets t ON u.id = t.user_id 
            AND t.date >= actual_start_date 
            AND t.date <= actual_end_date
        LEFT JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        LEFT JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        WHERE u.id = user_id_param
        GROUP BY u.id, u.username, u.display_name, u.first_name, u.last_name
    ),
    breakdown_data AS (
        SELECT 
            CASE 
                WHEN period_type = 'weekly' THEN DATE_TRUNC('week', t.date)::DATE
                ELSE t.date
            END as breakdown_date,
            j.name as breakdown_client,
            COALESCE(p.name, j.name) as breakdown_task,
            SUM(t.duration) / 3600.0 as breakdown_hours,
            j.short_code as breakdown_job_code,
            ARRAY_AGG(DISTINCT cfv.value ORDER BY cfv.value) FILTER (WHERE cfv.value IS NOT NULL) as breakdown_custom_fields
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        LEFT JOIN timesheet_customfield_values cfv ON t.id = cfv.timesheet_id
        WHERE t.user_id = user_id_param
            AND t.date >= actual_start_date 
            AND t.date <= actual_end_date
        GROUP BY 
            CASE 
                WHEN period_type = 'weekly' THEN DATE_TRUNC('week', t.date)::DATE
                ELSE t.date
            END,
            j.name, p.name, j.short_code
    )
    SELECT 
        us.user_id,
        us.username,
        us.display_name,
        us.start_date,
        us.end_date,
        us.total_hours,
        us.days_worked,
        us.daily_average,
        us.list_of_clients,
        us.list_of_tasks,
        us.custom_field_items,
        bd.breakdown_date,
        bd.breakdown_client,
        bd.breakdown_task,
        bd.breakdown_hours,
        bd.breakdown_job_code,
        bd.breakdown_custom_fields
    FROM user_summary us
    CROSS JOIN breakdown_data bd
    ORDER BY bd.breakdown_date DESC, bd.breakdown_client, bd.breakdown_task;
END;
$$ LANGUAGE plpgsql;

-- Function 5: Get all users summary (for the main dashboard)
CREATE OR REPLACE FUNCTION get_all_users_summary(
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    display_name TEXT,
    start_date DATE,
    end_date DATE,
    total_hours NUMERIC,
    days_worked BIGINT,
    daily_average NUMERIC,
    list_of_clients TEXT[],
    list_of_tasks TEXT[],
    custom_field_items TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM get_user_summary_analytics(NULL, start_date_param, end_date_param);
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- EXAMPLE USAGE QUERIES
-- ==============================================

-- Example 1: Get summary for all users
-- SELECT * FROM get_all_users_summary('2024-01-01', '2024-12-31');

-- Example 2: Get summary for specific user
-- SELECT * FROM get_user_summary_analytics(503759, '2024-01-01', '2024-12-31');

-- Example 3: Get daily breakdown for specific user
-- SELECT * FROM get_user_daily_breakdown(503759, '2024-01-01', '2024-12-31');

-- Example 4: Get weekly breakdown for specific user
-- SELECT * FROM get_user_weekly_breakdown(503759, '2024-01-01', '2024-12-31');

-- Example 5: Get comprehensive analytics for specific user
-- SELECT * FROM get_comprehensive_user_analytics(503759, '2024-01-01', '2024-12-31', 'daily');

-- ==============================================
-- UTILITY FUNCTIONS
-- ==============================================

-- Function to get working days count (excluding weekends and holidays)
CREATE OR REPLACE FUNCTION get_working_days_count(
    start_date DATE,
    end_date DATE
)
RETURNS INTEGER AS $$
DECLARE
    day_count INTEGER := 0;
    current_date DATE := start_date;
BEGIN
    WHILE current_date <= end_date LOOP
        -- Check if it's not a weekend (Saturday = 6, Sunday = 0)
        IF EXTRACT(DOW FROM current_date) NOT IN (0, 6) THEN
            day_count := day_count + 1;
        END IF;
        current_date := current_date + INTERVAL '1 day';
    END LOOP;
    
    RETURN day_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user productivity score
CREATE OR REPLACE FUNCTION get_user_productivity_score(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS NUMERIC AS $$
DECLARE
    total_hours NUMERIC;
    days_worked INTEGER;
    productivity_score NUMERIC;
BEGIN
    SELECT 
        COALESCE(SUM(t.duration) / 3600.0, 0),
        COUNT(DISTINCT t.date)
    INTO total_hours, days_worked
    FROM timesheets t
    WHERE t.user_id = user_id_param
        AND (t.date >= start_date_param OR start_date_param IS NULL)
        AND (t.date <= end_date_param OR end_date_param IS NULL);
    
    IF days_worked > 0 THEN
        productivity_score := LEAST(100, (total_hours / days_worked) * 10);
    ELSE
        productivity_score := 0;
    END IF;
    
    RETURN productivity_score;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_timesheets_user_date ON timesheets(user_id, date);
CREATE INDEX IF NOT EXISTS idx_timesheets_jobcode ON timesheets(jobcode_id);
CREATE INDEX IF NOT EXISTS idx_timesheet_customfield_values_timesheet ON timesheet_customfield_values(timesheet_id);
CREATE INDEX IF NOT EXISTS idx_jobcodes_name ON jobcodes(name);
CREATE INDEX IF NOT EXISTS idx_projects_jobcode ON projects(jobcode_id);

-- ==============================================
-- VIEWS FOR EASY ACCESS
-- ==============================================

-- View for user summary data
CREATE OR REPLACE VIEW v_user_summary AS
SELECT * FROM get_all_users_summary();

-- View for daily work breakdown (all users)
CREATE OR REPLACE VIEW v_daily_work_breakdown AS
SELECT 
    t.user_id,
    u.username,
    t.date as work_date,
    j.name as client,
    COALESCE(p.name, j.name) as task,
    t.duration / 3600.0 as hours,
    j.short_code as job_code
FROM timesheets t
JOIN users u ON t.user_id = u.id
JOIN jobcodes j ON t.jobcode_id = j.id
LEFT JOIN projects p ON j.id = p.jobcode_id
ORDER BY t.user_id, t.date DESC;

-- View for weekly work breakdown (all users)
CREATE OR REPLACE VIEW v_weekly_work_breakdown AS
SELECT 
    t.user_id,
    u.username,
    DATE_TRUNC('week', t.date)::DATE as work_week,
    j.name as client,
    COALESCE(p.name, j.name) as task,
    SUM(t.duration) / 3600.0 as hours,
    j.short_code as job_code
FROM timesheets t
JOIN users u ON t.user_id = u.id
JOIN jobcodes j ON t.jobcode_id = j.id
LEFT JOIN projects p ON j.id = p.jobcode_id
GROUP BY t.user_id, u.username, DATE_TRUNC('week', t.date), j.name, p.name, j.short_code
ORDER BY t.user_id, work_week DESC;
