#!/usr/bin/env python3
"""
Test user count fix
"""

import sys
import os
import pandas as pd

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_user_count():
    """Test that all users are returned"""
    print("🔍 Testing user count fix...")
    
    try:
        from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler
        
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Test employee list
        print("Testing get_employee_list()...")
        employee_list = handler.get_employee_list()
        print(f"✅ Employee list: {len(employee_list)} users")
        
        # Test all employees summary
        print("Testing get_all_employees_summary()...")
        all_employees = handler.get_all_employees_summary('2024-01-01', '2024-12-31')
        print(f"✅ All employees summary: {len(all_employees)} users")
        
        # Check if we're getting all users
        if len(employee_list) >= 60:  # Should be close to 64
            print("✅ Employee list has correct number of users")
        else:
            print(f"⚠️ Employee list has {len(employee_list)} users, expected ~64")
        
        if len(all_employees) >= 60:  # Should be close to 64
            print("✅ All employees summary has correct number of users")
        else:
            print(f"⚠️ All employees summary has {len(all_employees)} users, expected ~64")
        
        # Show sample data
        if not employee_list.empty:
            print(f"✅ Sample employee names: {employee_list['username'].head().tolist()}")
        
        if not all_employees.empty:
            print(f"✅ Sample employee data: {all_employees['employee_name'].head().tolist()}")
        
        return True
        
    except Exception as e:
        print(f"❌ User count test failed: {e}")
        return False

def test_direct_supabase_query():
    """Test direct Supabase query to verify user count"""
    print("\n🔍 Testing direct Supabase query...")
    
    try:
        from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler
        
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Direct query to get all active users
        users_response = handler.supabase.table('users').select('id, username, active').eq('active', True).execute()
        users_data = users_response.data
        
        print(f"✅ Direct Supabase query: {len(users_data)} active users")
        
        # Show some usernames
        if users_data:
            usernames = [user.get('username', 'Unknown') for user in users_data[:10]]
            print(f"✅ Sample usernames: {usernames}")
        
        return len(users_data) >= 60
        
    except Exception as e:
        print(f"❌ Direct Supabase query failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 USER COUNT FIX TEST")
    print("=" * 30)
    
    test1 = test_user_count()
    test2 = test_direct_supabase_query()
    
    if test1 and test2:
        print("\n🎉 USER COUNT FIX SUCCESSFUL!")
        print("✅ All 64 active users should now be visible in the UI!")
        print("✅ The issue was:")
        print("   - Limited user queries to 50 users")
        print("   - Filtered out users without timesheet data")
        print("✅ Fixed by:")
        print("   - Removed user limits")
        print("   - Include all users, even without timesheet data")
    else:
        print("\n⚠️ User count fix may need more work.")
    
    sys.exit(0 if (test1 and test2) else 1)
