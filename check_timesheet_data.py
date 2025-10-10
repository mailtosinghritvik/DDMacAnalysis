#!/usr/bin/env python3
"""
Check what timesheet data actually exists in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client

def check_timesheet_data():
    """Check what timesheet data exists in the database"""
    
    # Supabase connection
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return
    
    # Check if timesheet 7969 exists
    print("\n1. Checking for timesheet 7969...")
    try:
        result = supabase.table("timesheets").select("*").eq("id", 7969).execute()
        if result.data:
            print(f"✅ Timesheet 7969 found: {result.data[0]}")
        else:
            print("❌ Timesheet 7969 not found")
    except Exception as e:
        print(f"❌ Error checking timesheet 7969: {e}")
    
    # Check what timesheets exist
    print("\n2. Checking existing timesheets...")
    try:
        result = supabase.table("timesheets").select("id, user_id, jobcode_id, duration, date").limit(10).execute()
        if result.data:
            print(f"✅ Found {len(result.data)} timesheets:")
            for ts in result.data:
                print(f"   - ID: {ts['id']}, User: {ts['user_id']}, Jobcode: {ts['jobcode_id']}, Duration: {ts['duration']/3600:.1f}h, Date: {ts['date']}")
        else:
            print("❌ No timesheets found")
    except Exception as e:
        print(f"❌ Error checking timesheets: {e}")
    
    # Check users
    print("\n3. Checking users...")
    try:
        result = supabase.table("users").select("id, username, display_name, first_name, last_name").limit(10).execute()
        if result.data:
            print(f"✅ Found {len(result.data)} users:")
            for user in result.data:
                display_name = user.get('display_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                print(f"   - ID: {user['id']}, Username: {user['username']}, Display: {display_name}")
        else:
            print("❌ No users found")
    except Exception as e:
        print(f"❌ Error checking users: {e}")
    
    # Check jobcodes
    print("\n4. Checking jobcodes...")
    try:
        result = supabase.table("jobcodes").select("id, name, billable").limit(10).execute()
        if result.data:
            print(f"✅ Found {len(result.data)} jobcodes:")
            for jc in result.data:
                print(f"   - ID: {jc['id']}, Name: {jc['name']}, Billable: {jc['billable']}")
        else:
            print("❌ No jobcodes found")
    except Exception as e:
        print(f"❌ Error checking jobcodes: {e}")
    
    # Look for timesheets with high hours (like the ones in the performance table)
    print("\n5. Looking for timesheets with high hours...")
    try:
        result = supabase.table("timesheets").select("id, user_id, duration, date").order("duration", desc=True).limit(10).execute()
        if result.data:
            print(f"✅ Found timesheets with high hours:")
            for ts in result.data:
                hours = ts['duration'] / 3600.0
                print(f"   - ID: {ts['id']}, User: {ts['user_id']}, Hours: {hours:.1f}h, Date: {ts['date']}")
        else:
            print("❌ No timesheets found")
    except Exception as e:
        print(f"❌ Error checking high hours timesheets: {e}")

if __name__ == "__main__":
    check_timesheet_data()
