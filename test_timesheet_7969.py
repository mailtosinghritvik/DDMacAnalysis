#!/usr/bin/env python3
"""
Test script for Timesheet 7969 resolution
Tests the SQL functions and Python resolver
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.timesheet_resolver import get_timesheet_resolver, resolve_timesheet_7969
import json

def test_timesheet_resolution():
    """Test the timesheet resolution functionality"""
    print("🧪 Testing Timesheet 7969 Resolution")
    print("=" * 50)
    
    # Get the resolver
    resolver = get_timesheet_resolver()
    
    # Test 1: Resolve timesheet to user
    print("\n1. Testing timesheet to user resolution...")
    user_data = resolver.resolve_timesheet_to_user(7969)
    if user_data:
        print("✅ User data resolved successfully:")
        print(f"   - Timesheet ID: {user_data['timesheet_id']}")
        print(f"   - User ID: {user_data['user_id']}")
        print(f"   - Username: {user_data['username']}")
        print(f"   - Display Name: {user_data['display_name']}")
    else:
        print("❌ Failed to resolve user data")
    
    # Test 2: Get user summary
    print("\n2. Testing user summary...")
    user_summary = resolver.get_user_summary_for_timesheet(7969)
    if user_summary:
        print("✅ User summary retrieved successfully:")
        print(f"   - Total Hours: {user_summary['total_hours']}")
        print(f"   - Days Worked: {user_summary['days_worked']}")
        print(f"   - Daily Average: {user_summary['daily_average']}")
        print(f"   - Active Projects: {user_summary['active_projects']}")
        print(f"   - Productivity Score: {user_summary['productivity_score']}")
    else:
        print("❌ Failed to get user summary")
    
    # Test 3: Get daily work summary
    print("\n3. Testing daily work summary...")
    daily_work = resolver.get_daily_work_summary_for_timesheet(7969, 'daily')
    if daily_work:
        print(f"✅ Daily work summary retrieved successfully ({len(daily_work)} records)")
        for i, record in enumerate(daily_work[:3]):  # Show first 3 records
            print(f"   Record {i+1}: {record['work_date']} - {record['total_hours']}h - {record['client']}")
    else:
        print("❌ Failed to get daily work summary")
    
    # Test 4: Get client distribution
    print("\n4. Testing client distribution...")
    client_dist = resolver.get_client_time_distribution_for_timesheet(7969)
    if client_dist:
        print(f"✅ Client distribution retrieved successfully ({len(client_dist)} records)")
        for record in client_dist:
            print(f"   - {record['client']}: {record['total_hours']}h ({record['percentage_of_total']:.1f}%)")
    else:
        print("❌ Failed to get client distribution")
    
    # Test 5: Get task distribution
    print("\n5. Testing task distribution...")
    task_dist = resolver.get_task_time_distribution_for_timesheet(7969)
    if task_dist:
        print(f"✅ Task distribution retrieved successfully ({len(task_dist)} records)")
        for record in task_dist:
            print(f"   - {record['task']}: {record['total_hours']}h ({record['percentage_of_total']:.1f}%)")
    else:
        print("❌ Failed to get task distribution")
    
    # Test 6: Get complete user data
    print("\n6. Testing complete user data...")
    complete_data = resolver.get_complete_user_data_for_timesheet(7969)
    if complete_data:
        print("✅ Complete user data retrieved successfully")
        print(f"   - User Info: {complete_data['user_info']['display_name']}")
        print(f"   - Daily Work Records: {len(complete_data['daily_work_data'])}")
        print(f"   - Client Records: {len(complete_data['client_distribution'])}")
        print(f"   - Task Records: {len(complete_data['task_distribution'])}")
    else:
        print("❌ Failed to get complete user data")
    
    # Test 7: Test convenience function
    print("\n7. Testing convenience function...")
    convenience_data = resolve_timesheet_7969()
    if convenience_data:
        print("✅ Convenience function works successfully")
        print(f"   - Timesheet ID: {convenience_data['timesheet_id']}")
        print(f"   - User: {convenience_data['user_info']['display_name']}")
    else:
        print("❌ Convenience function failed")
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")
    
    # Show sample data structure
    print("\n📋 Sample Data Structure:")
    print(json.dumps(complete_data, indent=2, default=str))

def test_sql_functions():
    """Test SQL functions (if Supabase is connected)"""
    print("\n🗄️ Testing SQL Functions")
    print("=" * 30)
    
    resolver = get_timesheet_resolver()
    
    if resolver.connected:
        print("✅ Supabase connected - testing SQL functions")
        # The resolver will automatically use the SQL functions
        # when Supabase is connected
    else:
        print("⚠️ Supabase not connected - using mock data")
        print("   To test with real data, ensure Supabase is properly configured")

if __name__ == "__main__":
    test_timesheet_resolution()
    test_sql_functions()
