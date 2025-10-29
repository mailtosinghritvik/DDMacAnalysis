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
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
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