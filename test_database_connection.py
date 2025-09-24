#!/usr/bin/env python3
"""
Test Database Connection and Functions
This script tests the current state of your database connection and functions.
"""

from utils.supabase_queries import get_supabase_handler
from datetime import datetime, timedelta

def test_database_connection():
    """Test the current database connection and available functions"""
    
    print("🔍 Testing DDMac Analytics Database Connection")
    print("=" * 50)
    
    # Get the handler
    handler = get_supabase_handler()
    
    # Test basic connection
    print(f"✅ Supabase Connected: {handler.connected}")
    
    if not handler.connected:
        print("❌ Cannot connect to Supabase. Check your credentials.")
        return False
    
    # Test basic functions
    print("\n📊 Testing Basic Functions:")
    
    # Test users
    try:
        users = handler.get_available_users()
        print(f"✅ Users: {len(users)} found")
        if users:
            print(f"   First user: {users[0].get('display_name', users[0].get('first_name', 'Unknown'))}")
    except Exception as e:
        print(f"❌ Users: {str(e)}")
    
    # Test clients
    try:
        clients = handler.get_available_clients()
        print(f"✅ Clients: {len(clients)} found")
        if clients:
            print(f"   First client: {clients[0].get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Clients: {str(e)}")
    
    # Test employee analytics
    try:
        emp_data = handler.get_employee_analytics()
        print(f"✅ Employee Analytics: {emp_data.get('total_employees', 0)} employees")
    except Exception as e:
        print(f"❌ Employee Analytics: {str(e)}")
    
    # Test time analytics functions (these should fail)
    print("\n⏰ Testing Time Analytics Functions:")
    
    time_functions = [
        'get_time_period_overview',
        'get_time_daily_distribution', 
        'get_time_user_performance',
        'get_time_client_activity',
        'get_time_weekly_summary',
        'get_time_session_analysis'
    ]
    
    working_functions = []
    missing_functions = []
    
    for func_name in time_functions:
        try:
            if func_name == 'get_time_period_overview':
                result = handler.get_time_period_overview('2020-09-01', '2025-09-24')
                if result and result.get('total_hours', 0) > 0:
                    print(f"✅ {func_name}: Working")
                    working_functions.append(func_name)
                else:
                    print(f"⚠️ {func_name}: No data returned")
                    working_functions.append(func_name)
            else:
                # Test other functions
                result = handler.execute_function(func_name, {
                    'start_date': '2020-09-01',
                    'end_date': '2025-09-24'
                })
                if not result.empty:
                    print(f"✅ {func_name}: Working ({len(result)} rows)")
                    working_functions.append(func_name)
                else:
                    print(f"⚠️ {func_name}: No data returned")
                    working_functions.append(func_name)
        except Exception as e:
            if "Could not find the function" in str(e):
                print(f"❌ {func_name}: Function not deployed")
                missing_functions.append(func_name)
            else:
                print(f"❌ {func_name}: {str(e)}")
                missing_functions.append(func_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    if len(working_functions) == len(time_functions):
        print("🎉 ALL TIME ANALYTICS FUNCTIONS ARE WORKING!")
        print("✅ Your EmailReportWriter should show real data now.")
        return True
    else:
        print(f"⚠️ {len(missing_functions)} functions are missing:")
        for func in missing_functions:
            print(f"   - {func}")
        
        print("\n🔧 TO FIX THIS:")
        print("1. Go to your Supabase SQL Editor")
        print("2. Copy the contents of 'time_analytics_functions.sql'")
        print("3. Paste and run the SQL")
        print("4. Run this test again")
        
        return False

def main():
    """Main test function"""
    success = test_database_connection()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Run your EmailReportWriter")
        print("2. Generate a Time Analytics Report")
        print("3. You should see real data instead of sample data!")
    else:
        print("\n📖 See 'DATABASE_CONNECTION_FIX.md' for detailed instructions")

if __name__ == "__main__":
    main()
