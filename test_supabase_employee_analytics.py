"""
Test Supabase Employee Analytics Functions
Comprehensive testing for all Supabase functions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler

def test_supabase_employee_analytics_functions():
    """Test all Supabase employee analytics functions"""
    
    # Supabase connection parameters
    supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
    
    print("🧪 Testing Supabase Employee Analytics Functions")
    print("=" * 50)
    
    try:
        # Initialize handler
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Test 1: Get all employees summary
        print("\n1. Testing get_all_employees_summary()...")
        all_employees = handler.get_all_employees_summary('2024-01-01', '2024-12-31')
        print(f"✅ Found {len(all_employees)} employees")
        if not all_employees.empty:
            print(f"   Sample data: {all_employees[['employee_name', 'total_work_hours']].head()}")
        
        # Test 2: Get specific employee summary
        print("\n2. Testing get_employee_summary()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            emp_summary = handler.get_employee_summary(test_user_id, '2024-01-01', '2024-12-31')
            print(f"✅ Employee summary for user {test_user_id}: {len(emp_summary)} records")
            if not emp_summary.empty:
                print(f"   Total hours: {emp_summary.iloc[0]['total_work_hours']}")
                print(f"   Clients: {emp_summary.iloc[0]['client_list']}")
        else:
            print("⚠️ No employees found for testing")
        
        # Test 3: Get daily work data
        print("\n3. Testing get_employee_daily_work()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            daily_data = handler.get_employee_daily_work(test_user_id, '2024-01-01', '2024-12-31')
            print(f"✅ Daily work data for user {test_user_id}: {len(daily_data)} records")
            if not daily_data.empty:
                print(f"   Date range: {daily_data['work_date'].min()} to {daily_data['work_date'].max()}")
                print(f"   Total hours: {daily_data['hours_worked'].sum():.2f}")
        else:
            print("⚠️ No employees found for testing")
        
        # Test 4: Get weekly work data
        print("\n4. Testing get_employee_weekly_work()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            weekly_data = handler.get_employee_weekly_work(test_user_id, '2024-01-01', '2024-12-31')
            print(f"✅ Weekly work data for user {test_user_id}: {len(weekly_data)} records")
            if not weekly_data.empty:
                print(f"   Week range: {weekly_data['work_week'].min()} to {weekly_data['work_week'].max()}")
                print(f"   Total hours: {weekly_data['hours_worked'].sum():.2f}")
        else:
            print("⚠️ No employees found for testing")
        
        # Test 5: Get productivity metrics
        print("\n5. Testing get_employee_productivity_metrics()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            productivity = handler.get_employee_productivity_metrics(test_user_id, '2024-01-01', '2024-12-31')
            print(f"✅ Productivity metrics for user {test_user_id}: {len(productivity)} records")
            if not productivity.empty:
                print(f"   Productivity score: {productivity.iloc[0]['productivity_score']:.2f}")
                print(f"   Utilization: {productivity.iloc[0]['utilization_percentage']:.2f}%")
        else:
            print("⚠️ No employees found for testing")
        
        # Test 6: Get performance rating
        print("\n6. Testing get_employee_performance_rating()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            rating = handler.get_employee_performance_rating(test_user_id, '2024-01-01', '2024-12-31')
            print(f"✅ Performance rating for user {test_user_id}: {rating}")
        else:
            print("⚠️ No employees found for testing")
        
        # Test 7: Get client distribution
        print("\n7. Testing get_employee_client_distribution()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            client_dist = handler.get_employee_client_distribution(test_user_id, '2024-01-01', '2024-12-31')
            print(f"✅ Client distribution for user {test_user_id}: {len(client_dist)} records")
            if not client_dist.empty:
                print(f"   Top client: {client_dist.iloc[0]['client_name']} ({client_dist.iloc[0]['total_hours']:.2f} hours)")
        else:
            print("⚠️ No employees found for testing")
        
        # Test 8: Get employee list
        print("\n8. Testing get_employee_list()...")
        employee_list = handler.get_employee_list()
        print(f"✅ Employee list: {len(employee_list)} employees")
        if not employee_list.empty:
            print(f"   Sample employees: {employee_list['username'].head().tolist()}")
        
        # Test 9: Get KPIs
        print("\n9. Testing get_employee_kpis()...")
        kpis = handler.get_employee_kpis('2024-01-01', '2024-12-31')
        print(f"✅ KPIs calculated: {kpis}")
        
        # Test 10: Get utilization chart data
        print("\n10. Testing get_employee_utilization_chart_data()...")
        util_data = handler.get_employee_utilization_chart_data('2024-01-01', '2024-12-31')
        print(f"✅ Utilization chart data: {len(util_data)} records")
        if not util_data.empty:
            print(f"   Top employee: {util_data.iloc[0]['Employee']} ({util_data.iloc[0]['Utilization %']:.2f}%)")
        
        # Test 11: Get project allocation data
        print("\n11. Testing get_employee_project_allocation_data()...")
        allocation_data = handler.get_employee_project_allocation_data('2024-01-01', '2024-12-31')
        print(f"✅ Project allocation data: {len(allocation_data)} records")
        if not allocation_data.empty:
            print(f"   Top project: {allocation_data.iloc[0]['Project']} ({allocation_data.iloc[0]['Hours']:.2f} hours)")
        
        # Test 12: Get user summary data
        print("\n12. Testing get_user_summary_data()...")
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            user_summary = handler.get_user_summary_data(test_user_id, 'daily', '2024-01-01', '2024-12-31')
            print(f"✅ User summary data for user {test_user_id}: {len(user_summary)} records")
            if not user_summary.empty:
                print(f"   Date range: {user_summary['work_date'].min()} to {user_summary['work_date'].max()}")
                print(f"   Total hours: {user_summary['hours_worked'].sum():.2f}")
        else:
            print("⚠️ No employees found for testing")
        
        print("\n🎉 All Supabase tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print("=" * 50)

def test_supabase_data_validation():
    """Test data validation and consistency"""
    
    print("\n🔍 Testing Supabase Data Validation")
    print("=" * 30)
    
    supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
    
    try:
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Test data consistency
        all_employees = handler.get_all_employees_summary('2024-01-01', '2024-12-31')
        
        if not all_employees.empty:
            # Check for data consistency
            inconsistent_data = []
            for _, emp in all_employees.iterrows():
                total_hours = emp['total_work_hours']
                days_worked = emp['actual_work_days']
                daily_avg = emp['average_daily_hours']
                
                # Check if daily average calculation is correct
                if days_worked > 0 and abs(total_hours - (daily_avg * days_worked)) > 0.01:
                    inconsistent_data.append({
                        'employee': emp['employee_name'],
                        'total_hours': total_hours,
                        'days_worked': days_worked,
                        'daily_avg': daily_avg,
                        'calculated_total': daily_avg * days_worked
                    })
            
            if inconsistent_data:
                print(f"⚠️ Found {len(inconsistent_data)} employees with inconsistent data:")
                for data in inconsistent_data[:5]:  # Show first 5
                    print(f"   {data['employee']}: {data['total_hours']} vs {data['calculated_total']}")
            else:
                print("✅ All employee data is consistent")
            
            # Check for missing data
            missing_data = all_employees[
                (all_employees['total_work_hours'] == 0) | 
                (all_employees['actual_work_days'] == 0)
            ]
            
            if not missing_data.empty:
                print(f"⚠️ Found {len(missing_data)} employees with missing data:")
                print(f"   {missing_data['employee_name'].tolist()}")
            else:
                print("✅ No missing data found")
        
    except Exception as e:
        print(f"❌ Data validation failed: {str(e)}")

def test_supabase_performance():
    """Test function performance"""
    
    print("\n⚡ Testing Supabase Performance")
    print("=" * 20)
    
    supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
    
    try:
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Test performance of main functions
        import time
        
        start_time = time.time()
        all_employees = handler.get_all_employees_summary('2024-01-01', '2024-12-31')
        end_time = time.time()
        print(f"✅ get_all_employees_summary(): {end_time - start_time:.3f} seconds")
        
        if not all_employees.empty:
            test_user_id = all_employees.iloc[0]['employee_id']
            
            start_time = time.time()
            daily_data = handler.get_employee_daily_work(test_user_id, '2024-01-01', '2024-12-31')
            end_time = time.time()
            print(f"✅ get_employee_daily_work(): {end_time - start_time:.3f} seconds")
            
            start_time = time.time()
            productivity = handler.get_employee_productivity_metrics(test_user_id, '2024-01-01', '2024-12-31')
            end_time = time.time()
            print(f"✅ get_employee_productivity_metrics(): {end_time - start_time:.3f} seconds")
        
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")

def test_supabase_connection():
    """Test Supabase connection"""
    
    print("\n🔗 Testing Supabase Connection")
    print("=" * 25)
    
    supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
    
    try:
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Test basic connection
        if handler.supabase:
            print("✅ Supabase connection successful!")
            
            # Test table access
            try:
                users_response = handler.supabase.table('users').select('id').limit(1).execute()
                print("✅ Users table accessible")
            except Exception as e:
                print(f"⚠️ Users table access issue: {e}")
            
            try:
                timesheets_response = handler.supabase.table('timesheets').select('id').limit(1).execute()
                print("✅ Timesheets table accessible")
            except Exception as e:
                print(f"⚠️ Timesheets table access issue: {e}")
            
            try:
                jobcodes_response = handler.supabase.table('jobcodes').select('id').limit(1).execute()
                print("✅ Jobcodes table accessible")
            except Exception as e:
                print(f"⚠️ Jobcodes table access issue: {e}")
            
            try:
                projects_response = handler.supabase.table('projects').select('id').limit(1).execute()
                print("✅ Projects table accessible")
            except Exception as e:
                print(f"⚠️ Projects table access issue: {e}")
                
        else:
            print("❌ Supabase connection failed")
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")

if __name__ == "__main__":
    # Run all tests
    test_supabase_connection()
    test_supabase_employee_analytics_functions()
    test_supabase_data_validation()
    test_supabase_performance()
    
    print("\n🏁 All Supabase tests completed!")
    print("=" * 50)
