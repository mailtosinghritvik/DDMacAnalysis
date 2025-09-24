# Employee Analytics SQL Functions

This document provides comprehensive SQL functions to redesign the data structure for your employee analytics dashboard, exactly matching your requirements.

## Overview

The solution provides two main data structures:

1. **First Table**: User summary with start/end dates, daily average, clients, and tasks
2. **Second Table**: Daily/Weekly breakdown by client and task with hours

## Functions Created

### 1. `get_user_summary_analytics(user_id_param, start_date_param, end_date_param)`

**Purpose**: Returns the first table format as specified in your requirements.

**Returns**:
- `user_id`, `username`, `display_name`
- `start_date`, `end_date` 
- `total_hours`, `days_worked`, `daily_average`
- `list_of_clients` (array of client names)
- `list_of_tasks` (array of task names)
- `custom_field_items` (array of custom field values)

**Example Output**:
```
naveen| 01-08-2025| 11-09-2025| 250 (total time by naveen) / 40 (number of days naveen has worked) -> 6.25| [shlegel,ritvik,blahblah] |[shlegelWiring,shlegelPipes,ritvikCoding,ritvikCigarettes,blahblahTask1,blahblahTask2]
```

### 2. `get_user_daily_breakdown(user_id_param, start_date_param, end_date_param)`

**Purpose**: Returns daily work breakdown for a specific user.

**Returns**:
- `work_date`, `client`, `task`, `hours`, `job_code`, `custom_field_items`

**Example Output**:
```
20-12-2025 |Shlegel |  Wiring | 2
20-12-2025 |Shlegel |  Pipes | 8
27-12-2025 |ritvik |  Coding | 12
27-12-2025 |ritvik |  Coding | 15
2-1-2026 |blahblah |  Task1 | 31
2-1-2026 |blahblah |  Task2 | 12
```

### 3. `get_user_weekly_breakdown(user_id_param, start_date_param, end_date_param)`

**Purpose**: Returns weekly work breakdown for a specific user.

**Returns**: Same as daily but grouped by week.

### 4. `get_comprehensive_user_analytics(user_id_param, start_date_param, end_date_param, period_type)`

**Purpose**: Combines both tables in a single result set.

### 5. `get_all_users_summary(start_date_param, end_date_param)`

**Purpose**: Gets summary for all users (for dashboard overview).

## Usage Examples

### Get All Users Summary
```sql
SELECT * FROM get_all_users_summary('2024-01-01', '2024-12-31');
```

### Get Specific User Summary
```sql
SELECT * FROM get_user_summary_analytics(503759, '2024-01-01', '2024-12-31');
```

### Get Daily Breakdown for User
```sql
SELECT * FROM get_user_daily_breakdown(503759, '2024-01-01', '2024-12-31');
```

### Get Weekly Breakdown for User
```sql
SELECT * FROM get_user_weekly_breakdown(503759, '2024-01-01', '2024-12-31');
```

### Get Comprehensive Analytics
```sql
SELECT * FROM get_comprehensive_user_analytics(503759, '2024-01-01', '2024-12-31', 'daily');
```

## Key Features

### 1. Accurate Day Counting
- **DOES NOT** use simple date subtraction
- **Manually counts** working days excluding weekends
- Accounts for actual days worked vs. calendar days

### 2. Custom Field Integration
- Links custom field items with time entries
- Associates custom fields with specific job codes
- Provides arrays of custom field values

### 3. Client and Task Aggregation
- Automatically aggregates clients and tasks
- Handles multiple projects per user
- Provides clean arrays for frontend consumption

### 4. Flexible Date Ranges
- Optional start/end date parameters
- Defaults to full data range if not specified
- Supports both daily and weekly views

## Data Structure Mapping

### First Table (User Summary)
```
user | start_date | end_date | daily_average | list_of_clients | list_of_tasks
-----|------------|----------|---------------|-----------------|--------------
naveen| 01-08-2025| 11-09-2025| 6.25 | [shlegel,ritvik,blahblah] | [wiring,pipes,coding,cigarettes]
```

### Second Table (Daily/Weekly Breakdown)
```
Week/Day | Client | Task | Hours
---------|--------|------|-------
20-12-2025 | Shlegel | Wiring | 2
20-12-2025 | Shlegel | Pipes | 8
27-12-2025 | ritvik | Coding | 12
```

## Performance Optimizations

### Indexes Created
- `idx_timesheets_user_date` - For user and date filtering
- `idx_timesheets_jobcode` - For job code joins
- `idx_timesheet_customfield_values_timesheet` - For custom field lookups
- `idx_jobcodes_name` - For client name lookups
- `idx_projects_jobcode` - For project associations

### Views for Easy Access
- `v_user_summary` - Quick access to all user summaries
- `v_daily_work_breakdown` - Daily breakdown for all users
- `v_weekly_work_breakdown` - Weekly breakdown for all users

## Utility Functions

### `get_working_days_count(start_date, end_date)`
Calculates actual working days excluding weekends.

### `get_user_productivity_score(user_id, start_date, end_date)`
Calculates productivity score based on hours and days worked.

## Integration with Frontend

### For Dashboard Overview
```sql
-- Get all users for main dashboard
SELECT * FROM get_all_users_summary('2024-01-01', '2024-12-31');
```

### For Individual User Analysis
```sql
-- Get user summary
SELECT * FROM get_user_summary_analytics(503759, '2024-01-01', '2024-12-31');

-- Get daily breakdown
SELECT * FROM get_user_daily_breakdown(503759, '2024-01-01', '2024-12-31');

-- Get weekly breakdown  
SELECT * FROM get_user_weekly_breakdown(503759, '2024-01-01', '2024-12-31');
```

## Data Validation

The functions include built-in data validation:
- Handles NULL values gracefully
- Provides default values for missing data
- Validates date ranges
- Ensures data consistency

## Custom Field Integration

Custom fields are properly linked through:
- `timesheet_customfield_values` table
- `custom_fields` table for field definitions
- Arrays of custom field values per time entry

## Error Handling

All functions include:
- NULL parameter handling
- Date range validation
- Graceful degradation for missing data
- Performance optimization for large datasets

## Testing

Use the provided test queries in `test_employee_analytics.sql` to:
- Validate function outputs
- Test performance
- Verify data consistency
- Check format compliance

## Installation

1. Run `employee_analytics_functions.sql` to create all functions
2. Run `test_employee_analytics.sql` to test the functions
3. Use the functions in your frontend application

The functions are designed to work with your existing Supabase schema and provide exactly the data format you specified in your requirements.
