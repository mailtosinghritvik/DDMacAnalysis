#!/usr/bin/env python3
"""
Test script for Simple Timesheet 7969 resolution
Tests the simple resolver that uses direct database queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.timesheet_resolver_simple import get_simple_timesheet_resolver, resolve_timesheet_7969_simple
import json

def test_simple_timesheet_resolution():
    """Test the simple timesheet resolution functionality"""
    print("🧪 Testing Simple Timesheet 7969 Resolution")
    print("=" * 50)
    
    # Get the resolver
    resolver = get_simple_timesheet_resolver()
    
    # Test: Get timesheet 7969 data
    print("\n1. Testing timesheet 7969 data retrieval...")
    timesheet_data = resolver.get_timesheet_7969_data()
    
    if timesheet_data:
        print("✅ Timesheet data retrieved successfully:")
        print(f"   - Timesheet ID: {timesheet_data['timesheet_id']}")
        print(f"   - User ID: {timesheet_data['user_info']['user_id']}")
        print(f"   - Username: {timesheet_data['user_info']['username']}")
        print(f"   - Display Name: {timesheet_data['user_info']['display_name']}")
        print(f"   - Total Hours: {timesheet_data['user_info']['total_hours']}")
        print(f"   - Days Worked: {timesheet_data['user_info']['days_worked']}")
        print(f"   - Daily Average: {timesheet_data['user_info']['daily_average']}")
        print(f"   - Active Projects: {timesheet_data['user_info']['active_projects']}")
        print(f"   - Productivity Score: {timesheet_data['user_info']['productivity_score']}")
        
        # Show timesheet info
        if 'timesheet_info' in timesheet_data:
            ts_info = timesheet_data['timesheet_info']
            print(f"\n   Timesheet Details:")
            print(f"   - Jobcode ID: {ts_info['jobcode_id']}")
            print(f"   - Jobcode Name: {ts_info['jobcode_name']}")
            print(f"   - Date: {ts_info['date']}")
            print(f"   - Duration: {ts_info['duration_hours']} hours")
            print(f"   - Notes: {ts_info['notes']}")
        
        # Show daily work data
        daily_work = timesheet_data.get('daily_work_data', [])
        print(f"\n   Daily Work Data ({len(daily_work)} records):")
        for i, record in enumerate(daily_work[:3]):  # Show first 3
            print(f"   - {record['work_date']}: {record['total_hours']}h - {record['client']}")
        
        # Show client distribution
        client_dist = timesheet_data.get('client_distribution', [])
        print(f"\n   Client Distribution ({len(client_dist)} clients):")
        for record in client_dist:
            print(f"   - {record['client']}: {record['total_hours']}h ({record['percentage_of_total']:.1f}%)")
        
        # Show task distribution
        task_dist = timesheet_data.get('task_distribution', [])
        print(f"\n   Task Distribution ({len(task_dist)} tasks):")
        for record in task_dist:
            print(f"   - {record['task']}: {record['total_hours']}h ({record['percentage_of_total']:.1f}%)")
        
    else:
        print("❌ Failed to retrieve timesheet data")
    
    # Test convenience function
    print("\n2. Testing convenience function...")
    convenience_data = resolve_timesheet_7969_simple()
    if convenience_data:
        print("✅ Convenience function works successfully")
        print(f"   - Timesheet ID: {convenience_data['timesheet_id']}")
        print(f"   - User: {convenience_data['user_info']['display_name']}")
    else:
        print("❌ Convenience function failed")
    
    print("\n" + "=" * 50)
    print("🎉 Simple testing completed!")
    
    # Show sample data structure
    print("\n📋 Sample Data Structure:")
    print(json.dumps(timesheet_data, indent=2, default=str))

if __name__ == "__main__":
    test_simple_timesheet_resolution()
