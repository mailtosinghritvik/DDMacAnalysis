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