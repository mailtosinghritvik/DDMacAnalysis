# Employee Analytics SQL Integration

Complete SQL-based employee analytics solution with Streamlit integration.

## 📁 Files Created

1. **`employee_analytics_sql_functions.sql`** - Complete SQL functions
2. **`utils/employee_analytics_sql_handler.py`** - Python integration handler
3. **`pages/Employee_Analytics_SQL.py`** - Updated Streamlit page
4. **`test_employee_analytics_sql.py`** - Comprehensive testing
5. **`EMPLOYEE_ANALYTICS_SQL_README.md`** - This documentation

## 🚀 Quick Start

### 1. Install SQL Functions

Run the SQL functions in your database:

```sql
-- Execute this in your PostgreSQL database
\i employee_analytics_sql_functions.sql
```

### 2. Update Database Connection

Update the connection parameters in `utils/employee_analytics_sql_handler.py`:

```python
connection_params = {
    'host': 'your_host',
    'database': 'your_database',
    'user': 'your_user',
    'password': 'your_password',
    'port': 5432
}
```

### 3. Run the Application

```bash
streamlit run pages/Employee_Analytics_SQL.py
```

## 🔧 SQL Functions Available

### Core Functions

1. **`get_employee_summary_data(user_id, start_date, end_date)`**
   - Returns employee summary with hours, days, clients, tasks
   - Format: `naveen| 01-08-2025| 11-09-2025| 250/40 -> 6.25| [clients] |[tasks]`

2. **`get_employee_daily_work_data(user_id, start_date, end_date)`**
   - Returns daily work breakdown
   - Format: `20-12-2025 |Shlegel | Wiring | 2`

3. **`get_employee_weekly_work_data(user_id, start_date, end_date)`**
   - Returns weekly work breakdown
   - Same format as daily but grouped by week

4. **`get_all_employees_summary(start_date, end_date)`**
   - Returns summary for all employees
   - For dashboard overview

### Analytics Functions

5. **`get_employee_productivity_metrics(user_id, start_date, end_date)`**
   - Returns productivity scores, utilization, overtime
   - Calculates performance metrics

6. **`get_employee_performance_rating(user_id, start_date, end_date)`**
   - Returns performance rating (Excellent/Good/Average/Needs Improvement)
   - Based on daily averages

7. **`get_employee_client_distribution(user_id, start_date, end_date)`**
   - Returns client time distribution
   - Shows hours per client with percentages

8. **`calculate_working_days(start_date, end_date)`**
   - Calculates working days excluding weekends
   - Manual counting, not date subtraction

## 📊 Data Structure

### First Table (Employee Summary)
```
employee_name | work_start_date | work_end_date | total_work_hours | actual_work_days | average_daily_hours | client_list | task_list
--------------|-----------------|---------------|-----------------|------------------|---------------------|-------------|----------
naveen        | 2024-01-01      | 2024-12-31    | 250.5           | 40               | 6.26                | [Shlegel,Ritvik] | [Wiring,Pipes]
```

### Second Table (Daily/Weekly Breakdown)
```
work_date  | client_name | task_name | hours_worked | job_code | custom_field_items
-----------|-------------|-----------|--------------|----------|-------------------
2024-12-20| Shlegel     | Wiring    | 2.0          | ELEC001  | [Priority:High]
2024-12-20| Shlegel     | Pipes     | 8.0          | PIPE001  | [Priority:Medium]
```

## 🐍 Python Integration

### Basic Usage

```python
from utils.employee_analytics_sql_handler import get_employee_analytics_handler

# Initialize handler
handler = get_employee_analytics_handler(connection_params)

# Get all employees
all_employees = handler.get_all_employees_summary('2024-01-01', '2024-12-31')

# Get specific employee
emp_data = handler.get_employee_summary(user_id, '2024-01-01', '2024-12-31')

# Get daily work
daily_data = handler.get_employee_daily_work(user_id, '2024-01-01', '2024-12-31')

# Get productivity metrics
productivity = handler.get_employee_productivity_metrics(user_id, '2024-01-01', '2024-12-31')

# Close connection
handler.close_connection()
```

### Streamlit Integration

```python
# In your Streamlit app
from utils.employee_analytics_sql_handler import get_employee_data_sql

# Get employee data
employee_data, kpis = get_employee_data_sql(connection_params, '2024-01-01', '2024-12-31')

# Display KPIs
st.metric("Total Employees", kpis['total_employees'])
st.metric("Avg Utilization", f"{kpis['avg_utilization']:.1f}%")
```

## 🧪 Testing

Run comprehensive tests:

```bash
python test_employee_analytics_sql.py
```

Tests include:
- ✅ Function execution
- ✅ Data validation
- ✅ Performance testing
- ✅ Error handling

## 📈 Performance Optimizations

### Indexes Created
- `idx_timesheets_user_date_analytics` - User and date filtering
- `idx_timesheets_jobcode_analytics` - Job code joins
- `idx_timesheet_customfield_values_analytics` - Custom field lookups
- `idx_jobcodes_name_analytics` - Client name lookups
- `idx_projects_jobcode_analytics` - Project associations
- `idx_users_active_analytics` - Active users

### Views Available
- `v_all_employees_summary` - Quick access to all summaries
- `v_daily_work_all_employees` - Daily breakdown for all
- `v_weekly_work_all_employees` - Weekly breakdown for all

## 🔍 Data Validation

The functions include built-in validation:

```sql
-- Check data consistency
SELECT 
    employee_id,
    employee_name,
    total_work_hours,
    actual_work_days,
    average_daily_hours,
    CASE 
        WHEN actual_work_days > 0 AND ABS(total_work_hours - (average_daily_hours * actual_work_days)) > 0.01 
        THEN 'INCONSISTENT'
        ELSE 'OK'
    END as data_consistency
FROM get_all_employees_summary('2024-01-01', '2024-12-31')
WHERE total_work_hours > 0;
```

## 🚨 Error Handling

All functions include comprehensive error handling:

- ✅ NULL parameter handling
- ✅ Date range validation
- ✅ Graceful degradation for missing data
- ✅ Performance optimization for large datasets
- ✅ Connection management

## 📋 Example Queries

### Get Employee Summary
```sql
SELECT * FROM get_employee_summary_data(503759, '2024-01-01', '2024-12-31');
```

### Get Daily Breakdown
```sql
SELECT * FROM get_employee_daily_work_data(503759, '2024-01-01', '2024-12-31');
```

### Get Productivity Metrics
```sql
SELECT * FROM get_employee_productivity_metrics(503759, '2024-01-01', '2024-12-31');
```

### Get Performance Rating
```sql
SELECT get_employee_performance_rating(503759, '2024-01-01', '2024-12-31');
```

## 🎯 Key Features

1. **Exact Data Format Match** - Matches your specified format exactly
2. **Manual Day Counting** - Excludes weekends, not simple date subtraction
3. **Custom Field Integration** - Links custom fields with time entries
4. **Client/Task Aggregation** - Automatic aggregation with arrays
5. **Performance Optimized** - Indexes and views for fast queries
6. **Streamlit Ready** - Direct integration with your existing page

## 🔧 Configuration

Update these parameters in your code:

```python
# Database connection
connection_params = {
    'host': 'your_host',
    'database': 'your_database',
    'user': 'your_user',
    'password': 'your_password',
    'port': 5432
}

# Date ranges
start_date = '2024-01-01'
end_date = '2024-12-31'
```

## 📞 Support

If you encounter any issues:

1. Check database connection parameters
2. Verify SQL functions are installed
3. Run the test suite to identify issues
4. Check the error logs for specific problems

## 🎉 Benefits

- ✅ **No Frontend Changes** - Works with existing Employee_Analytics.py
- ✅ **Exact Data Format** - Matches your requirements perfectly
- ✅ **Performance Optimized** - Fast queries with proper indexing
- ✅ **Comprehensive Testing** - Full test suite included
- ✅ **Easy Integration** - Simple Python handler
- ✅ **Scalable** - Handles large datasets efficiently

The solution provides exactly the data structure you specified while maintaining compatibility with your existing frontend code!
