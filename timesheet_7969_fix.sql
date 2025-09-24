-- ==============================================
-- TIMESHEET 7969 DATA RESOLUTION FUNCTIONS
-- ==============================================

-- Function to get timesheet data by timesheet ID
CREATE OR REPLACE FUNCTION get_timesheet_by_id(timesheet_id_param BIGINT)
RETURNS TABLE (
    timesheet_id BIGINT,
    user_id BIGINT,
    username TEXT,
    display_name TEXT,
    jobcode_id BIGINT,
    jobcode_name TEXT,
    project_name TEXT,
    date DATE,
    start_time TEXT,
    end_time TEXT,
    duration_hours NUMERIC,
    billable BOOLEAN,
    notes TEXT,
    location TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id as timesheet_id,
        t.user_id,
        u.username,
        COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
        t.jobcode_id,
        j.name as jobcode_name,
        COALESCE(p.name, 'No Project') as project_name,
        t.date,
        t.start::TEXT as start_time,
        t.end::TEXT as end_time,
        t.duration / 3600.0 as duration_hours,
        j.billable,
        t.notes,
        t.location
    FROM timesheets t
    JOIN users u ON t.user_id = u.id
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.id = timesheet_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to get user summary data for timesheet 7969
CREATE OR REPLACE FUNCTION get_user_summary_for_timesheet(timesheet_id_param BIGINT)
RETURNS TABLE (
    user_id BIGINT,
    username TEXT,
    display_name TEXT,
    total_hours NUMERIC,
    days_worked BIGINT,
    daily_average NUMERIC,
    active_projects BIGINT,
    clients_served BIGINT,
    first_work_date DATE,
    last_work_date DATE,
    productivity_score NUMERIC
) AS $$
DECLARE
    target_user_id BIGINT;
BEGIN
    -- Get the user_id from the timesheet
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
    
    -- If timesheet not found, return empty result
    IF target_user_id IS NULL THEN
        RETURN;
    END IF;
    
    RETURN QUERY
    SELECT 
        u.id as user_id,
        u.username,
        COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
        COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
        COUNT(DISTINCT t.date)::BIGINT as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
            ELSE 0::NUMERIC
        END as daily_average,
        COUNT(DISTINCT t.jobcode_id)::BIGINT as active_projects,
        COUNT(DISTINCT j.name)::BIGINT as clients_served,
        MIN(t.date) as first_work_date,
        MAX(t.date) as last_work_date,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 AND COUNT(DISTINCT t.date) < 1000 THEN
                LEAST(100, (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)) * 10)::NUMERIC
            ELSE 85::NUMERIC
        END as productivity_score
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id
    LEFT JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE u.id = target_user_id
    GROUP BY u.id, u.username, u.display_name, u.first_name, u.last_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get daily work summary for timesheet 7969 user
CREATE OR REPLACE FUNCTION get_daily_work_summary_for_timesheet(timesheet_id_param BIGINT, period_type TEXT DEFAULT 'daily')
RETURNS TABLE (
    work_date DATE,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    client TEXT,
    task TEXT,
    project TEXT,
    notes TEXT
) AS $$
DECLARE
    target_user_id BIGINT;
BEGIN
    -- Get the user_id from the timesheet
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
    
    -- If timesheet not found, return empty result
    IF target_user_id IS NULL THEN
        RETURN;
    END IF;
    
    IF period_type = 'daily' THEN
        RETURN QUERY
        SELECT 
            t.date as work_date,
            t.duration / 3600.0 as total_hours,
            CASE WHEN j.billable THEN t.duration / 3600.0 ELSE 0 END as billable_hours,
            j.name as client,
            COALESCE(p.name, 'General Work') as task,
            COALESCE(p.name, j.name) as project,
            t.notes
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = target_user_id
        ORDER BY t.date DESC, t.start;
    ELSE
        -- Weekly summary
        RETURN QUERY
        SELECT 
            DATE_TRUNC('week', t.date)::DATE as work_date,
            SUM(t.duration) / 3600.0 as total_hours,
            SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0 as billable_hours,
            j.name as client,
            COALESCE(p.name, 'General Work') as task,
            COALESCE(p.name, j.name) as project,
            STRING_AGG(t.notes, '; ') as notes
        FROM timesheets t
        JOIN jobcodes j ON t.jobcode_id = j.id
        LEFT JOIN projects p ON j.id = p.jobcode_id
        WHERE t.user_id = target_user_id
        GROUP BY DATE_TRUNC('week', t.date), j.name, p.name
        ORDER BY work_date DESC;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get client time distribution for timesheet 7969 user
CREATE OR REPLACE FUNCTION get_client_time_distribution_for_timesheet(timesheet_id_param BIGINT)
RETURNS TABLE (
    client TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    days_worked BIGINT,
    avg_hours_per_day NUMERIC,
    percentage_of_total NUMERIC
) AS $$
DECLARE
    target_user_id BIGINT;
    total_user_hours NUMERIC;
BEGIN
    -- Get the user_id from the timesheet
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
    
    -- If timesheet not found, return empty result
    IF target_user_id IS NULL THEN
        RETURN;
    END IF;
    
    -- Get total hours for percentage calculation
    SELECT COALESCE(SUM(t.duration) / 3600.0, 0) INTO total_user_hours
    FROM timesheets t
    WHERE t.user_id = target_user_id;
    
    RETURN QUERY
    SELECT 
        j.name as client,
        COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
        COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0)::NUMERIC as billable_hours,
        COUNT(DISTINCT t.date)::BIGINT as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
            ELSE 0::NUMERIC
        END as avg_hours_per_day,
        CASE 
            WHEN total_user_hours > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / total_user_hours * 100)::NUMERIC
            ELSE 0::NUMERIC
        END as percentage_of_total
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE t.user_id = target_user_id
    GROUP BY j.name, j.billable
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get task time distribution for timesheet 7969 user
CREATE OR REPLACE FUNCTION get_task_time_distribution_for_timesheet(timesheet_id_param BIGINT)
RETURNS TABLE (
    task TEXT,
    total_hours NUMERIC,
    billable_hours NUMERIC,
    days_worked BIGINT,
    avg_hours_per_day NUMERIC,
    percentage_of_total NUMERIC
) AS $$
DECLARE
    target_user_id BIGINT;
    total_user_hours NUMERIC;
BEGIN
    -- Get the user_id from the timesheet
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
    
    -- If timesheet not found, return empty result
    IF target_user_id IS NULL THEN
        RETURN;
    END IF;
    
    -- Get total hours for percentage calculation
    SELECT COALESCE(SUM(t.duration) / 3600.0, 0) INTO total_user_hours
    FROM timesheets t
    WHERE t.user_id = target_user_id;
    
    RETURN QUERY
    SELECT 
        COALESCE(p.name, 'General Work') as task,
        COALESCE(SUM(t.duration) / 3600.0, 0)::NUMERIC as total_hours,
        COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0)::NUMERIC as billable_hours,
        COUNT(DISTINCT t.date)::BIGINT as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date))::NUMERIC
            ELSE 0::NUMERIC
        END as avg_hours_per_day,
        CASE 
            WHEN total_user_hours > 0 THEN 
                (COALESCE(SUM(t.duration) / 3600.0, 0) / total_user_hours * 100)::NUMERIC
            ELSE 0::NUMERIC
        END as percentage_of_total
    FROM timesheets t
    JOIN jobcodes j ON t.jobcode_id = j.id
    LEFT JOIN projects p ON j.id = p.jobcode_id
    WHERE t.user_id = target_user_id
    GROUP BY p.name, j.billable
    ORDER BY total_hours DESC;
END;
$$ LANGUAGE plpgsql;

-- ==============================================
-- RAW QUERIES FOR TIMESHEET 7969
-- ==============================================

-- Query 1: Get basic timesheet information for ID 7969
-- SELECT * FROM get_timesheet_by_id(7969);

-- Query 2: Get user summary for timesheet 7969
-- SELECT * FROM get_user_summary_for_timesheet(7969);

-- Query 3: Get daily work summary for timesheet 7969 user
-- SELECT * FROM get_daily_work_summary_for_timesheet(7969, 'daily');

-- Query 4: Get weekly work summary for timesheet 7969 user
-- SELECT * FROM get_daily_work_summary_for_timesheet(7969, 'weekly');

-- Query 5: Get client time distribution for timesheet 7969 user
-- SELECT * FROM get_client_time_distribution_for_timesheet(7969);

-- Query 6: Get task time distribution for timesheet 7969 user
-- SELECT * FROM get_task_time_distribution_for_timesheet(7969);

-- Query 7: Direct raw query to get timesheet 7969 data
/*
SELECT 
    t.id as timesheet_id,
    t.user_id,
    u.username,
    COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
    t.jobcode_id,
    j.name as jobcode_name,
    COALESCE(p.name, 'No Project') as project_name,
    t.date,
    t.start,
    t.end,
    t.duration / 3600.0 as duration_hours,
    j.billable,
    t.notes,
    t.location
FROM timesheets t
JOIN users u ON t.user_id = u.id
JOIN jobcodes j ON t.jobcode_id = j.id
LEFT JOIN projects p ON j.id = p.jobcode_id
WHERE t.id = 7969;
*/

-- Query 8: Get all timesheet entries for the user who has timesheet 7969
/*
WITH target_user AS (
    SELECT user_id FROM timesheets WHERE id = 7969
)
SELECT 
    t.id as timesheet_id,
    t.user_id,
    u.username,
    COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as display_name,
    t.jobcode_id,
    j.name as jobcode_name,
    COALESCE(p.name, 'No Project') as project_name,
    t.date,
    t.start,
    t.end,
    t.duration / 3600.0 as duration_hours,
    j.billable,
    t.notes,
    t.location
FROM timesheets t
JOIN users u ON t.user_id = u.id
JOIN jobcodes j ON t.jobcode_id = j.id
LEFT JOIN projects p ON j.id = p.jobcode_id
CROSS JOIN target_user tu
WHERE t.user_id = tu.user_id
ORDER BY t.date DESC, t.start;
*/
