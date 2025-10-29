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
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
    IF target_user_id IS NULL THEN
        RETURN;
    END IF;
    SELECT COALESCE(SUM(t.duration) / 3600.0, 0) INTO total_user_hours
    FROM timesheets t
    WHERE t.user_id = target_user_id;
    RETURN QUERY
    SELECT 
        COALESCE(p.name, 'General Work') as task,
        ROUND(COALESCE(SUM(t.duration) / 3600.0, 0), 2)::NUMERIC as total_hours,
        ROUND(COALESCE(SUM(CASE WHEN j.billable THEN t.duration ELSE 0 END) / 3600.0, 0), 2)::NUMERIC as billable_hours,
        COUNT(DISTINCT t.date)::BIGINT as days_worked,
        CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN 
                ROUND((COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)), 2)::NUMERIC
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