#!/usr/bin/env python3
"""
Deploy Time Analytics Functions to Supabase
This script deploys the missing time analytics functions to your Supabase database.
"""

import os
import sys
from utils.supabase_queries import get_supabase_handler

def deploy_time_analytics_functions():
    """Deploy the time analytics functions to Supabase"""
    
    print("🚀 Deploying Time Analytics Functions to Supabase...")
    
    # Get the Supabase handler
    handler = get_supabase_handler()
    
    if not handler.connected:
        print("❌ Cannot connect to Supabase. Please check your credentials.")
        return False
    
    print("✅ Connected to Supabase successfully!")
    
    # Read the SQL functions from the file
    try:
        with open('supabase_functions.sql', 'r') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print("❌ supabase_functions.sql file not found!")
        return False
    
    # Extract only the time analytics functions (from line 1004 onwards)
    lines = sql_content.split('\n')
    time_analytics_start = None
    
    for i, line in enumerate(lines):
        if '-- 6. TIME ANALYTICS FUNCTIONS' in line:
            time_analytics_start = i
            break
    
    if time_analytics_start is None:
        print("❌ Time analytics functions section not found in SQL file!")
        return False
    
    # Extract the time analytics functions
    time_analytics_sql = '\n'.join(lines[time_analytics_start:])
    
    print("📝 Time analytics functions found in SQL file")
    print(f"📊 Functions to deploy:")
    print("  - get_time_period_overview")
    print("  - get_time_daily_distribution") 
    print("  - get_time_user_performance")
    print("  - get_time_client_activity")
    print("  - get_time_weekly_summary")
    print("  - get_time_session_analysis")
    
    # Deploy the functions
    try:
        print("\n🔄 Deploying functions to Supabase...")
        
        # Execute the SQL to create the functions
        result = handler.client.rpc('exec', {'sql': time_analytics_sql}).execute()
        
        print("✅ Time analytics functions deployed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error deploying functions: {str(e)}")
        print("\n💡 Manual deployment required:")
        print("1. Go to your Supabase SQL Editor")
        print("2. Copy the time analytics functions from supabase_functions.sql")
        print("3. Paste and run the SQL")
        return False

def test_deployed_functions():
    """Test that the deployed functions work"""
    
    print("\n🧪 Testing deployed functions...")
    
    handler = get_supabase_handler()
    
    # Test functions
    test_functions = [
        ('get_time_period_overview', {'start_date': '2020-09-01', 'end_date': '2025-09-24'}),
        ('get_time_daily_distribution', {'start_date': '2020-09-01', 'end_date': '2025-09-24'}),
        ('get_time_user_performance', {'start_date': '2020-09-01', 'end_date': '2025-09-24'}),
        ('get_time_client_activity', {'start_date': '2020-09-01', 'end_date': '2025-09-24'}),
        ('get_time_weekly_summary', {'start_date': '2020-09-01', 'end_date': '2025-09-24'}),
        ('get_time_session_analysis', {'start_date': '2020-09-01', 'end_date': '2025-09-24'})
    ]
    
    success_count = 0
    
    for func_name, params in test_functions:
        try:
            result = handler.execute_function(func_name, params)
            if not result.empty:
                print(f"✅ {func_name}: {len(result)} rows returned")
                success_count += 1
            else:
                print(f"⚠️ {func_name}: No data returned (may be normal if no data in date range)")
                success_count += 1
        except Exception as e:
            print(f"❌ {func_name}: {str(e)}")
    
    print(f"\n📊 Test Results: {success_count}/{len(test_functions)} functions working")
    
    if success_count == len(test_functions):
        print("🎉 All time analytics functions are working!")
        return True
    else:
        print("⚠️ Some functions may need manual deployment")
        return False

def main():
    """Main deployment function"""
    
    print("=" * 60)
    print("🔧 DDMac Analytics - Time Functions Deployment")
    print("=" * 60)
    
    # Deploy the functions
    if deploy_time_analytics_functions():
        # Test the deployed functions
        test_deployed_functions()
        
        print("\n" + "=" * 60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("=" * 60)
        print("🎯 Your EmailReportWriter should now show real data instead of sample data.")
        print("📊 Try generating a Time Analytics Report to see the difference!")
        
    else:
        print("\n" + "=" * 60)
        print("⚠️ MANUAL DEPLOYMENT REQUIRED")
        print("=" * 60)
        print("1. Go to your Supabase project dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy the time analytics functions from supabase_functions.sql")
        print("4. Paste and run the SQL")
        print("5. Test your EmailReportWriter again")

if __name__ == "__main__":
    main()
