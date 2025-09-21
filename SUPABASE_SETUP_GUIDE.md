# Supabase Database Integration Setup Guide

## Overview
This guide explains how to set up and use the Supabase database integration with your DDMac Analytics EmailReportWriter. The integration provides direct database access instead of relying on API calls, giving you real-time data from your PostgreSQL database.

## Prerequisites
- Supabase account and project
- Database schema deployed (see `supabase_functions.sql`)
- Python environment with required packages

## 1. Database Setup

### Step 1: Deploy Supabase Functions
Run the SQL functions in your Supabase SQL editor:

```sql
-- Copy and paste the contents of supabase_functions.sql
-- This creates all the necessary functions for analytics data retrieval
```

### Step 2: Verify Functions
Check that these functions are created in your database:
- `get_employee_analytics()`
- `get_project_analytics()`
- `get_task_analytics()`
- `get_time_tracking_summary()`
- `get_financial_metrics()`
- `get_dashboard_summary()`

## 2. Environment Configuration

### Step 1: Get Supabase Credentials
1. Go to your Supabase project dashboard
2. Navigate to Settings > API
3. Copy your:
   - Project URL
   - Anon/Public Key

### Step 2: Set Environment Variables
Create a `.env` file in your project root:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

Or set them in your system environment:
```bash
export SUPABASE_URL="your_supabase_project_url"
export SUPABASE_ANON_KEY="your_supabase_anon_key"
```

## 3. Database Schema Requirements

Your database should have these tables with the provided schema:

### Core Tables:
- `users` - Employee information
- `timesheets` - Time tracking data
- `jobcodes` - Task/project codes
- `projects` - Project information
- `accubid_breakdowns` - Project estimates
- `custom_fields` - Custom field definitions
- `files` - File attachments
- `locations` - Location data

### Key Relationships:
- `timesheets.user_id` → `users.id`
- `timesheets.jobcode_id` → `jobcodes.id`
- `projects.jobcode_id` → `jobcodes.id`
- `accubid_breakdowns.job_name` → `projects.name`

## 4. Usage

### Automatic Integration
The EmailReportWriter will automatically use Supabase if:
1. Environment variables are set
2. Supabase client is available
3. Database functions are deployed

### Manual Testing
Test the integration:

```python
from utils.supabase_queries import get_supabase_handler, is_supabase_available

# Check if Supabase is available
if is_supabase_available():
    handler = get_supabase_handler()
    
    # Get employee analytics
    employee_data = handler.get_employee_analytics('2025-01-01', '2025-01-31')
    print(f"Employees: {employee_data['total_employees']}")
    
    # Get project analytics
    project_data = handler.get_project_analytics('2025-01-01', '2025-01-31')
    print(f"Projects: {project_data['total_projects']}")
```

## 5. Data Flow

### With Supabase (Preferred):
```
EmailReportWriter → Supabase Functions → PostgreSQL Database → Real Data
```

### Without Supabase (Fallback):
```
EmailReportWriter → API Calls → Sample Data
```

## 6. Available Functions

### Employee Analytics
- **Function**: `get_employee_analytics(start_date, end_date)`
- **Returns**: Employee performance, utilization, productivity metrics
- **Data Source**: `users` + `timesheets` tables

### Project Analytics
- **Function**: `get_project_analytics(start_date, end_date)`
- **Returns**: Project progress, budget status, team allocation
- **Data Source**: `projects` + `jobcodes` + `timesheets` tables

### Task Analytics
- **Function**: `get_task_analytics(start_date, end_date)`
- **Returns**: Task performance, duration, efficiency metrics
- **Data Source**: `jobcodes` + `timesheets` tables

### Time Tracking
- **Function**: `get_time_tracking_summary(start_date, end_date)`
- **Returns**: Daily time summaries, billable hours, employee hours
- **Data Source**: `timesheets` table

### Financial Metrics
- **Function**: `get_financial_metrics(start_date, end_date)`
- **Returns**: Revenue, costs, profit margins, hourly rates
- **Data Source**: `timesheets` + `jobcodes` tables

### Dashboard Summary
- **Function**: `get_dashboard_summary(start_date, end_date)`
- **Returns**: Comprehensive overview of all metrics
- **Data Source**: All tables combined

## 7. Troubleshooting

### Common Issues:

1. **"Supabase credentials not found"**
   - Check environment variables are set
   - Verify `.env` file is in project root
   - Restart your application

2. **"Function not found"**
   - Ensure SQL functions are deployed
   - Check function names match exactly
   - Verify database permissions

3. **"No data returned"**
   - Check date range parameters
   - Verify data exists in tables
   - Check table relationships

4. **"Connection failed"**
   - Verify Supabase URL and key
   - Check network connectivity
   - Ensure Supabase project is active

### Debug Mode:
Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 8. Performance Optimization

### Database Indexes:
Add these indexes for better performance:

```sql
-- Timesheets table indexes
CREATE INDEX idx_timesheets_user_date ON timesheets(user_id, date);
CREATE INDEX idx_timesheets_jobcode_date ON timesheets(jobcode_id, date);
CREATE INDEX idx_timesheets_date ON timesheets(date);

-- Users table indexes
CREATE INDEX idx_users_active ON users(active);

-- Projects table indexes
CREATE INDEX idx_projects_active ON projects(active);
CREATE INDEX idx_projects_status ON projects(status);
```

### Query Optimization:
- Use date ranges to limit data
- Group by appropriate time periods
- Filter by active records only

## 9. Security Considerations

### Row Level Security (RLS):
Enable RLS on sensitive tables:

```sql
-- Enable RLS on timesheets
ALTER TABLE timesheets ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users
CREATE POLICY "Users can view their own timesheets" 
ON timesheets FOR SELECT 
USING (auth.uid()::text = user_id::text);
```

### API Key Security:
- Use environment variables for credentials
- Never commit credentials to version control
- Rotate keys regularly
- Use service role key only when necessary

## 10. Monitoring and Maintenance

### Health Checks:
```python
# Check database connectivity
from utils.supabase_queries import is_supabase_available
print(f"Supabase Available: {is_supabase_available()}")
```

### Data Validation:
- Verify data consistency across tables
- Check for missing relationships
- Monitor query performance
- Set up alerts for data quality issues

## 11. Migration from API to Database

### Gradual Migration:
1. Deploy Supabase functions
2. Set environment variables
3. Test with small date ranges
4. Monitor data accuracy
5. Switch to database-only mode

### Rollback Plan:
- Keep API fallback enabled
- Monitor error rates
- Have quick rollback procedure
- Maintain data backup

## Support

For issues with:
- **Database functions**: Check Supabase documentation
- **Python integration**: Check utils/supabase_queries.py
- **EmailReportWriter**: Check pages/EmailReportWriter.py
- **Data accuracy**: Verify table relationships and data quality

## Next Steps

1. Deploy the SQL functions to your Supabase database
2. Set up environment variables
3. Test the integration with a small date range
4. Monitor performance and data accuracy
5. Gradually expand usage to full date ranges
6. Set up monitoring and alerts
7. Optimize queries based on usage patterns
