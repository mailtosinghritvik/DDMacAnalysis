-- ==============================================
-- TEST QUERIES FOR EMPLOYEE ANALYTICS FUNCTIONS
-- ==============================================

-- Test 1: Get summary for all users (First Table)
-- This will return data in the format: user, start_date, end_date, daily_average, list_of_clients, list_of_tasks
SELECT 
    username,
    start_date,
    end_date,
    total_hours,
    days_worked,
    daily_average,
    list_of_clients,
    list_of_tasks,
    custom_field_items
FROM get_all_users_summary('2024-01-01', '2024-12-31')
ORDER BY total_hours DESC;

-- Test 2: Get summary for specific user (e.g., user_id 503759)
SELECT 
    username,
    start_date,
    end_date,
    total_hours,
    days_worked,
    daily_average,
    list_of_clients,
    list_of_tasks,
    custom_field_items
FROM get_user_summary_analytics(503759, '2024-01-01', '2024-12-31');

-- Test 3: Get daily breakdown for specific user (Second Table - Daily)
-- This will return data in the format: work_date, client, task, hours
SELECT 
    work_date,
    client,
    task,
    hours,
    job_code,
    custom_field_items
FROM get_user_daily_breakdown(503759, '2024-01-01', '2024-12-31')
ORDER BY work_date DESC, client, task;

-- Test 4: Get weekly breakdown for specific user (Second Table - Weekly)
-- This will return data in the format: work_week, client, task, hours
SELECT 
    work_week,
    client,
    task,
    hours,
    job_code,
    custom_field_items
FROM get_user_weekly_breakdown(503759, '2024-01-01', '2024-12-31')
ORDER BY work_week DESC, client, task;

-- Test 5: Get comprehensive analytics (Both tables combined)
SELECT 
    -- Summary data
    username,
    start_date,
    end_date,
    total_hours,
    days_worked,
    daily_average,
    list_of_clients,
    list_of_tasks,
    -- Breakdown data
    breakdown_date,
    breakdown_client,
    breakdown_task,
    breakdown_hours,
    breakdown_job_code,
    breakdown_custom_fields
FROM get_comprehensive_user_analytics(503759, '2024-01-01', '2024-12-31', 'daily')
ORDER BY breakdown_date DESC;

-- Test 6: Get productivity scores for all users
SELECT 
    u.id as user_id,
    u.username,
    get_user_productivity_score(u.id, '2024-01-01', '2024-12-31') as productivity_score
FROM users u
WHERE u.active = true
ORDER BY productivity_score DESC;

-- Test 7: Get working days count for a date range
SELECT 
    get_working_days_count('2024-01-01', '2024-01-31') as working_days_january,
    get_working_days_count('2024-02-01', '2024-02-29') as working_days_february;

-- Test 8: Sample data format matching your requirements
-- This query will return data exactly as you specified:
-- naveen| 01-08-2025| 11-09-2025| 250 (total time) / 40 (days worked) -> 6.25 (daily average)| [shlegel,ritvik,blahblah] |[shlegelWiring,shlegelPipes,ritvikCoding,ritvikCigarettes,blahblahTask1,blahblahTask2]

SELECT 
    username || '| ' ||
    start_date || '| ' ||
    end_date || '| ' ||
    total_hours || ' (total time by ' || username || ') / ' ||
    days_worked || ' (number of days ' || username || ' has worked) -> ' ||
    ROUND(daily_average, 2) || '| ' ||
    '[' || ARRAY_TO_STRING(list_of_clients, ',') || '] |' ||
    '[' || ARRAY_TO_STRING(list_of_tasks, ',') || ']' as formatted_output
FROM get_user_summary_analytics(503759, '2024-01-01', '2024-12-31');

-- Test 9: Daily breakdown format matching your requirements
-- This will return data in the format:
-- Week/Day| Client | task | Hours
-- 20-12-2025 |Shlegel |  Wiring | 2
-- 20-12-2025 |Shlegel |  Pipes | 8

SELECT 
    work_date || ' |' ||
    client || ' |  ' ||
    task || ' | ' ||
    hours as formatted_daily_output
FROM get_user_daily_breakdown(503759, '2024-01-01', '2024-12-31')
ORDER BY work_date DESC, client, task;

-- Test 10: Weekly breakdown format
SELECT 
    work_week || ' |' ||
    client || ' |  ' ||
    task || ' | ' ||
    hours as formatted_weekly_output
FROM get_user_weekly_breakdown(503759, '2024-01-01', '2024-12-31')
ORDER BY work_week DESC, client, task;

-- ==============================================
-- PERFORMANCE TESTING QUERIES
-- ==============================================

-- Test query execution time for large datasets
EXPLAIN ANALYZE 
SELECT * FROM get_all_users_summary('2024-01-01', '2024-12-31');

-- Test with specific user and date range
EXPLAIN ANALYZE 
SELECT * FROM get_user_daily_breakdown(503759, '2024-01-01', '2024-12-31');

-- ==============================================
-- DATA VALIDATION QUERIES
-- ==============================================

-- Check if all users have data
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN total_hours > 0 THEN 1 END) as users_with_data,
    COUNT(CASE WHEN total_hours = 0 THEN 1 END) as users_without_data
FROM get_all_users_summary('2024-01-01', '2024-12-31');

-- Check data consistency
SELECT 
    user_id,
    username,
    total_hours,
    days_worked,
    daily_average,
    CASE 
        WHEN days_worked > 0 AND ABS(total_hours - (daily_average * days_worked)) > 0.01 THEN 'INCONSISTENT'
        ELSE 'OK'
    END as data_consistency
FROM get_all_users_summary('2024-01-01', '2024-12-31')
WHERE total_hours > 0;

-- ==============================================
-- SAMPLE OUTPUT FORMATS
-- ==============================================

-- Example output for first table (user summary):
/*
username | start_date | end_date   | total_hours | days_worked | daily_average | list_of_clients                    | list_of_tasks
---------|------------|------------|-------------|-------------|---------------|-----------------------------------|-----------------------------------
naveen   | 2024-01-01 | 2024-12-31| 250.5       | 40          | 6.26          | {Shlegel,Ritvik,BlahBlah}          | {Wiring,Pipes,Coding,Cigarettes}
alice    | 2024-01-01 | 2024-12-31| 180.0       | 25          | 7.20          | {TechCorp,DataSys}                 | {Development,Analysis}
*/

-- Example output for second table (daily breakdown):
/*
work_date  | client    | task      | hours | job_code | custom_field_items
-----------|-----------|-----------|-------|----------|-------------------
2024-12-20| Shlegel   | Wiring    | 2.0   | ELEC001  | {Priority:High}
2024-12-20| Shlegel   | Pipes     | 8.0   | PIPE001  | {Priority:Medium}
2024-12-27| Ritvik    | Coding    | 12.0  | CODE001  | {Priority:High}
2024-12-27| Ritvik    | Coding    | 15.0  | CODE001  | {Priority:High}
2024-01-02| BlahBlah  | Task1     | 31.0  | TASK001  | {Priority:Low}
2024-01-02| BlahBlah  | Task2     | 12.0  | TASK002  | {Priority:Medium}
*/
