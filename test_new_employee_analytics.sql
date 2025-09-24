-- ==============================================
-- TEST QUERIES FOR NEW EMPLOYEE ANALYTICS FUNCTIONS
-- ==============================================

-- Test 1: Get summary for all employees (New Function)
SELECT 
    employee_name,
    work_start_date,
    work_end_date,
    total_work_hours,
    actual_work_days,
    average_daily_hours,
    client_list,
    task_list,
    custom_field_values
FROM get_all_employees_summary('2024-01-01', '2024-12-31')
ORDER BY total_work_hours DESC;

-- Test 2: Get summary for specific employee (New Function)
SELECT 
    employee_name,
    work_start_date,
    work_end_date,
    total_work_hours,
    actual_work_days,
    average_daily_hours,
    client_list,
    task_list,
    custom_field_values
FROM get_employee_summary_data(503759, '2024-01-01', '2024-12-31');

-- Test 3: Get daily breakdown for specific employee (New Function)
SELECT 
    work_date,
    client_name,
    task_name,
    hours_worked,
    job_code,
    custom_field_items
FROM get_employee_daily_work_data(503759, '2024-01-01', '2024-12-31')
ORDER BY work_date DESC, client_name, task_name;

-- Test 4: Get weekly breakdown for specific employee (New Function)
SELECT 
    work_week,
    client_name,
    task_name,
    hours_worked,
    job_code,
    custom_field_items
FROM get_employee_weekly_work_data(503759, '2024-01-01', '2024-12-31')
ORDER BY work_week DESC, client_name, task_name;

-- Test 5: Get comprehensive analytics (New Function)
SELECT 
    -- Summary data
    employee_name,
    work_start_date,
    work_end_date,
    total_work_hours,
    actual_work_days,
    average_daily_hours,
    client_list,
    task_list,
    -- Breakdown data
    breakdown_date,
    breakdown_client,
    breakdown_task,
    breakdown_hours,
    breakdown_job_code,
    breakdown_custom_fields
FROM get_employee_complete_analytics(503759, '2024-01-01', '2024-12-31', 'daily')
ORDER BY breakdown_date DESC;

-- Test 6: Get productivity metrics (New Function)
SELECT 
    employee_name,
    total_hours,
    days_worked,
    daily_average,
    productivity_score,
    utilization_percentage,
    overtime_hours
FROM get_employee_productivity_metrics(503759, '2024-01-01', '2024-12-31');

-- Test 7: Get client distribution (New Function)
SELECT 
    client_name,
    total_hours,
    billable_hours,
    days_worked,
    average_hours_per_day,
    percentage_of_total
FROM get_employee_client_distribution(503759, '2024-01-01', '2024-12-31')
ORDER BY total_hours DESC;

-- Test 8: Get performance rating (New Function)
SELECT 
    u.username,
    get_employee_performance_rating(u.id, '2024-01-01', '2024-12-31') as performance_rating
FROM users u
WHERE u.active = true
ORDER BY performance_rating;

-- Test 9: Calculate working days (New Function)
SELECT 
    calculate_working_days('2024-01-01', '2024-01-31') as working_days_january,
    calculate_working_days('2024-02-01', '2024-02-29') as working_days_february;

-- Test 10: Sample data format matching your requirements (New Function)
-- This query will return data exactly as you specified:
-- naveen| 01-08-2025| 11-09-2025| 250 (total time) / 40 (days worked) -> 6.25 (daily average)| [shlegel,ritvik,blahblah] |[shlegelWiring,shlegelPipes,ritvikCoding,ritvikCigarettes,blahblahTask1,blahblahTask2]

SELECT 
    employee_name || '| ' ||
    work_start_date || '| ' ||
    work_end_date || '| ' ||
    total_work_hours || ' (total time by ' || employee_name || ') / ' ||
    actual_work_days || ' (number of days ' || employee_name || ' has worked) -> ' ||
    ROUND(average_daily_hours, 2) || '| ' ||
    '[' || ARRAY_TO_STRING(client_list, ',') || '] |' ||
    '[' || ARRAY_TO_STRING(task_list, ',') || ']' as formatted_output
FROM get_employee_summary_data(503759, '2024-01-01', '2024-12-31');

-- Test 11: Daily breakdown format matching your requirements (New Function)
-- This will return data in the format:
-- Week/Day| Client | task | Hours
-- 20-12-2025 |Shlegel |  Wiring | 2
-- 20-12-2025 |Shlegel |  Pipes | 8

SELECT 
    work_date || ' |' ||
    client_name || ' |  ' ||
    task_name || ' | ' ||
    hours_worked as formatted_daily_output
FROM get_employee_daily_work_data(503759, '2024-01-01', '2024-12-31')
ORDER BY work_date DESC, client_name, task_name;

-- Test 12: Weekly breakdown format (New Function)
SELECT 
    work_week || ' |' ||
    client_name || ' |  ' ||
    task_name || ' | ' ||
    hours_worked as formatted_weekly_output
FROM get_employee_weekly_work_data(503759, '2024-01-01', '2024-12-31')
ORDER BY work_week DESC, client_name, task_name;

-- ==============================================
-- PERFORMANCE TESTING QUERIES - NEW FUNCTIONS
-- ==============================================

-- Test query execution time for large datasets
EXPLAIN ANALYZE 
SELECT * FROM get_all_employees_summary('2024-01-01', '2024-12-31');

-- Test with specific employee and date range
EXPLAIN ANALYZE 
SELECT * FROM get_employee_daily_work_data(503759, '2024-01-01', '2024-12-31');

-- Test productivity metrics performance
EXPLAIN ANALYZE 
SELECT * FROM get_employee_productivity_metrics(503759, '2024-01-01', '2024-12-31');

-- ==============================================
-- DATA VALIDATION QUERIES - NEW FUNCTIONS
-- ==============================================

-- Check if all employees have data
SELECT 
    COUNT(*) as total_employees,
    COUNT(CASE WHEN total_work_hours > 0 THEN 1 END) as employees_with_data,
    COUNT(CASE WHEN total_work_hours = 0 THEN 1 END) as employees_without_data
FROM get_all_employees_summary('2024-01-01', '2024-12-31');

-- Check data consistency
SELECT 
    employee_id,
    employee_name,
    total_work_hours,
    actual_work_days,
    average_daily_hours,
    CASE 
        WHEN actual_work_days > 0 AND ABS(total_work_hours - (average_daily_hours * actual_work_days)) > 0.01 THEN 'INCONSISTENT'
        ELSE 'OK'
    END as data_consistency
FROM get_all_employees_summary('2024-01-01', '2024-12-31')
WHERE total_work_hours > 0;

-- ==============================================
-- SAMPLE OUTPUT FORMATS - NEW FUNCTIONS
-- ==============================================

-- Example output for first table (employee summary):
/*
employee_name | work_start_date | work_end_date | total_work_hours | actual_work_days | average_daily_hours | client_list                    | task_list
--------------|-----------------|---------------|-----------------|------------------|---------------------|--------------------------------|-----------------------------------
naveen        | 2024-01-01      | 2024-12-31    | 250.5           | 40               | 6.26                | {Shlegel,Ritvik,BlahBlah}      | {Wiring,Pipes,Coding,Cigarettes}
alice         | 2024-01-01      | 2024-12-31    | 180.0           | 25               | 7.20                | {TechCorp,DataSys}             | {Development,Analysis}
*/

-- Example output for second table (daily breakdown):
/*
work_date  | client_name | task_name | hours_worked | job_code | custom_field_items
-----------|-------------|-----------|--------------|----------|-------------------
2024-12-20| Shlegel     | Wiring    | 2.0          | ELEC001  | {Priority:High}
2024-12-20| Shlegel     | Pipes     | 8.0          | PIPE001  | {Priority:Medium}
2024-12-27| Ritvik      | Coding    | 12.0         | CODE001  | {Priority:High}
2024-12-27| Ritvik      | Coding    | 15.0         | CODE001  | {Priority:High}
2024-01-02| BlahBlah    | Task1     | 31.0         | TASK001  | {Priority:Low}
2024-01-02| BlahBlah    | Task2     | 12.0         | TASK002  | {Priority:Medium}
*/

-- ==============================================
-- COMPARISON WITH OLD FUNCTIONS
-- ==============================================

-- Old function: get_user_summary_analytics()
-- New function: get_employee_summary_data()

-- Old function: get_user_daily_breakdown()
-- New function: get_employee_daily_work_data()

-- Old function: get_user_weekly_breakdown()
-- New function: get_employee_weekly_work_data()

-- Old function: get_comprehensive_user_analytics()
-- New function: get_employee_complete_analytics()

-- Old function: get_all_users_summary()
-- New function: get_all_employees_summary()

-- ==============================================
-- NEW ADDITIONAL FUNCTIONS
-- ==============================================

-- New function: get_employee_productivity_metrics()
-- New function: get_employee_client_distribution()
-- New function: get_employee_performance_rating()
-- New function: calculate_working_days()

-- ==============================================
-- USAGE EXAMPLES FOR NEW FUNCTIONS
-- ==============================================

-- Get all employees with their productivity scores
SELECT 
    es.employee_name,
    es.total_work_hours,
    es.average_daily_hours,
    pm.productivity_score,
    pm.utilization_percentage,
    pm.overtime_hours
FROM get_all_employees_summary('2024-01-01', '2024-12-31') es
LEFT JOIN get_employee_productivity_metrics(es.employee_id, '2024-01-01', '2024-12-31') pm 
    ON es.employee_id = pm.employee_id
ORDER BY pm.productivity_score DESC;

-- Get employees with their performance ratings
SELECT 
    es.employee_name,
    es.total_work_hours,
    es.average_daily_hours,
    get_employee_performance_rating(es.employee_id, '2024-01-01', '2024-12-31') as performance_rating
FROM get_all_employees_summary('2024-01-01', '2024-12-31') es
ORDER BY es.total_work_hours DESC;
