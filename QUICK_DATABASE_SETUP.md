# Quick Database Setup Guide

## 🚀 Get Real Data from Your Huge Database

You have a huge database but you're getting dummy data because Supabase isn't configured. Here's how to fix it:

## Step 1: Get Your Supabase Credentials

1. **Go to your Supabase project dashboard**
2. **Navigate to Settings > API**
3. **Copy these two values:**
   - **Project URL** (looks like: `https://your-project.supabase.co`)
   - **Anon/Public Key** (long string starting with `eyJ...`)

## Step 2: Run the Setup Script

```bash
python setup_supabase_credentials.py
```

This will:
- Ask for your Supabase URL and Key
- Save them to a `.env` file
- Test the connection
- Show you what to do next

## Step 3: Deploy Database Functions

1. **Go to your Supabase SQL Editor**
2. **Copy and paste the contents of `supabase_functions.sql`**
3. **Click "Run" to deploy all the functions**

## Step 4: Test Your Data

Run your EmailReportWriter and you should now see:
- **Real employee data** from your `users` table
- **Real project data** from your `projects` table  
- **Real time tracking** from your `timesheets` table
- **Real task data** from your `jobcodes` table

## What You'll Get Instead of Dummy Data:

### Before (Dummy Data):
```json
{
  "Employee Analytics": {"total_employees": 5, "avg_utilization": 0.85},
  "Project Analytics": {"total_projects": 8, "avg_progress": 0.84}
}
```

### After (Real Data):
```json
{
  "Employee Analytics": {
    "total_employees": 150,  // Real count from your users table
    "avg_utilization": 0.87, // Calculated from real timesheets
    "raw_data": [/* Real employee records */]
  },
  "Project Analytics": {
    "total_projects": 45,    // Real count from your projects table
    "avg_progress": 0.76,    // Calculated from real project data
    "raw_data": [/* Real project records */]
  }
}
```

## Troubleshooting

### "No data found"
- Make sure your database has data in the tables
- Check that the SQL functions are deployed
- Verify your credentials are correct

### "Function not found"
- Deploy the SQL functions from `supabase_functions.sql`
- Check function names match exactly

### "Connection failed"
- Verify your Supabase URL and Key
- Check your internet connection
- Ensure your Supabase project is active

## Database Schema Requirements

Your database should have these tables:
- `users` - Employee information
- `timesheets` - Time tracking data
- `jobcodes` - Task/project codes
- `projects` - Project information
- `accubid_breakdowns` - Project estimates (optional)

## Performance Tips for Huge Database

1. **Use date ranges** to limit data size
2. **Add database indexes** for better performance
3. **Group data** by daily/weekly/monthly periods
4. **Filter by active records** only

## Need Help?

- Check `SUPABASE_SETUP_GUIDE.md` for detailed instructions
- Look at `supabase_functions.sql` for the database functions
- Run `python setup_supabase_credentials.py` for interactive setup
