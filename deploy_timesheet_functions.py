#!/usr/bin/env python3
"""
Deploy Timesheet 7969 SQL Functions to Supabase
This script deploys the SQL functions needed for timesheet resolution
"""

import os
import sys
from supabase import create_client, Client

def deploy_sql_functions():
    """Deploy the SQL functions to Supabase"""
    
    # Supabase connection
    url = "https://tgendmgdrljuxxxyynpz.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False
    
    # Read the SQL file
    try:
        with open('timesheet_7969_fix.sql', 'r') as f:
            sql_content = f.read()
        print("✅ Read SQL file")
    except Exception as e:
        print(f"❌ Failed to read SQL file: {e}")
        return False
    
    # Split the SQL content into individual functions
    # Remove comments and split by function definitions
    lines = sql_content.split('\n')
    functions = []
    current_function = []
    
    for line in lines:
        # Skip comment lines and empty lines
        if line.strip().startswith('--') or line.strip() == '':
            continue
        
        current_function.append(line)
        
        # Check if this is the end of a function
        if line.strip().endswith('$$ LANGUAGE plpgsql;'):
            functions.append('\n'.join(current_function))
            current_function = []
    
    print(f"📋 Found {len(functions)} functions to deploy")
    
    # Deploy each function
    success_count = 0
    for i, function_sql in enumerate(functions, 1):
        if not function_sql.strip():
            continue
            
        try:
            print(f"\n🔄 Deploying function {i}...")
            print(f"Function preview: {function_sql[:100]}...")
            
            # Execute the function creation
            result = supabase.rpc('exec_sql', {'sql': function_sql}).execute()
            
            print(f"✅ Function {i} deployed successfully")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to deploy function {i}: {e}")
            # Try alternative method - direct SQL execution
            try:
                # Some Supabase setups might require different approach
                print(f"🔄 Trying alternative deployment method for function {i}...")
                # This might not work in all Supabase setups
                print(f"⚠️ Function {i} deployment failed - may need manual deployment")
            except Exception as e2:
                print(f"❌ Alternative method also failed: {e2}")
    
    print(f"\n📊 Deployment Summary:")
    print(f"   - Total functions: {len(functions)}")
    print(f"   - Successfully deployed: {success_count}")
    print(f"   - Failed: {len(functions) - success_count}")
    
    if success_count == len(functions):
        print("🎉 All functions deployed successfully!")
        return True
    else:
        print("⚠️ Some functions failed to deploy - manual deployment may be required")
        return False

def create_individual_function_files():
    """Create individual SQL files for each function for manual deployment"""
    
    try:
        with open('timesheet_7969_fix.sql', 'r') as f:
            sql_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read SQL file: {e}")
        return
    
    # Split into individual functions
    lines = sql_content.split('\n')
    functions = []
    current_function = []
    
    for line in lines:
        if line.strip().startswith('--') or line.strip() == '':
            continue
        
        current_function.append(line)
        
        if line.strip().endswith('$$ LANGUAGE plpgsql;'):
            functions.append('\n'.join(current_function))
            current_function = []
    
    # Create individual files
    os.makedirs('sql_functions', exist_ok=True)
    
    function_names = [
        'get_timesheet_by_id',
        'get_user_summary_for_timesheet', 
        'get_daily_work_summary_for_timesheet',
        'get_client_time_distribution_for_timesheet',
        'get_task_time_distribution_for_timesheet'
    ]
    
    for i, (name, function_sql) in enumerate(zip(function_names, functions)):
        if function_sql.strip():
            filename = f'sql_functions/{name}.sql'
            with open(filename, 'w') as f:
                f.write(function_sql)
            print(f"✅ Created {filename}")

def main():
    """Main deployment function"""
    print("🚀 Deploying Timesheet 7969 SQL Functions to Supabase")
    print("=" * 60)
    
    # Try automated deployment
    success = deploy_sql_functions()
    
    if not success:
        print("\n📁 Creating individual function files for manual deployment...")
        create_individual_function_files()
        print("\n📋 Manual Deployment Instructions:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste each function from the sql_functions/ folder")
        print("4. Execute each function individually")
        print("5. Verify functions are created in the database")
    
    print("\n🎯 Next Steps:")
    print("1. Run: python test_timesheet_7969.py")
    print("2. Run: streamlit run pages/Employee_Analytics_Timesheet7969.py")
    print("3. Check the UI shows data for timesheet 7969")

if __name__ == "__main__":
    main()
