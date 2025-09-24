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
    SELECT t.user_id INTO target_user_id
    FROM timesheets t
    WHERE t.id = timesheet_id_param;
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