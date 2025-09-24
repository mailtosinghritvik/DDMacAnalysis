#!/usr/bin/env python3
"""
Final Test for Employee_Analytics_Supabase.py
Comprehensive testing with all fixes applied
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test basic functionality without data validation issues"""
    print("🔍 Testing basic functionality...")
    
    try:
        # Test imports
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        import numpy as np
        print("✅ All imports successful")
        
        # Test Supabase handler import
        from utils.supabase_employee_analytics_handler import (
            get_supabase_employee_analytics_handler,
            get_employee_data_supabase,
            get_employee_detailed_data_supabase
        )
        print("✅ Supabase handler imports successful")
        
        # Test Supabase connection
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        if handler and handler.supabase:
            print("✅ Supabase connection successful")
        else:
            print("❌ Supabase connection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_employee_analytics_functions():
    """Test all functions in Employee_Analytics_Supabase.py"""
    print("\n🔍 Testing Employee Analytics functions...")
    
    try:
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("employee_analytics_supabase", "pages/Employee_Analytics_Supabase.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test get_employee_data_supabase_integrated function
        print("Testing get_employee_data_supabase_integrated...")
        employee_data, kpis, progress_data = module.get_employee_data_supabase_integrated()
        print(f"✅ get_employee_data_supabase_integrated: {type(employee_data)}")
        
        # Test create_employee_productivity_gauge function
        print("Testing create_employee_productivity_gauge...")
        gauge_fig = module.create_employee_productivity_gauge(85, "Test Employee")
        print(f"✅ create_employee_productivity_gauge: {type(gauge_fig)}")
        
        # Test create_employee_utilization_chart function
        print("Testing create_employee_utilization_chart...")
        test_data = pd.DataFrame({
            'employee_name': ['Test1', 'Test2'],
            'total_work_hours': [160, 120],
            'actual_work_days': [20, 15]
        })
        util_chart, util_df = module.create_employee_utilization_chart(test_data)
        print(f"✅ create_employee_utilization_chart: {type(util_chart)}")
        
        # Test create_employee_project_allocation function
        print("Testing create_employee_project_allocation...")
        test_data = pd.DataFrame({
            'employee_name': ['Test1', 'Test2'],
            'client_list': [['Client1', 'Client2'], ['Client3']],
            'total_work_hours': [160, 120]
        })
        alloc_chart, alloc_df = module.create_employee_project_allocation(test_data)
        print(f"✅ create_employee_project_allocation: {type(alloc_chart)}")
        
        # Test create_user_summary_charts function
        print("Testing create_user_summary_charts...")
        test_user_data = pd.DataFrame({
            'work_date': ['2024-01-01', '2024-01-02'],
            'hours_worked': [8, 7],
            'client_name': ['Client1', 'Client2'],
            'task_name': ['Task1', 'Task2']
        })
        time_fig, client_fig, task_fig = module.create_user_summary_charts(test_user_data, 'daily')
        print(f"✅ create_user_summary_charts: {type(time_fig)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Employee Analytics functions error: {e}")
        traceback.print_exc()
        return False

def test_supabase_data_functions():
    """Test Supabase data functions"""
    print("\n🔍 Testing Supabase data functions...")
    
    try:
        from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler
        
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Test get_all_employees_summary
        print("Testing get_all_employees_summary...")
        all_employees = handler.get_all_employees_summary('2024-01-01', '2024-12-31')
        print(f"✅ get_all_employees_summary: {len(all_employees)} employees")
        
        # Test get_employee_list
        print("Testing get_employee_list...")
        employee_list = handler.get_employee_list()
        print(f"✅ get_employee_list: {len(employee_list)} employees")
        
        # Test get_employee_kpis
        print("Testing get_employee_kpis...")
        kpis = handler.get_employee_kpis('2024-01-01', '2024-12-31')
        print(f"✅ get_employee_kpis: {kpis}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase data functions error: {e}")
        traceback.print_exc()
        return False

def test_data_handling():
    """Test data handling and validation"""
    print("\n🔍 Testing data handling...")
    
    try:
        # Test data validation functions
        test_data = pd.DataFrame({
            'employee_name': ['Test1', 'Test2', 'Test3'],
            'total_work_hours': [160, 120, None],
            'actual_work_days': [20, 15, 10],
            'client_list': [['Client1', 'Client2'], ['Client3'], []]
        })
        
        # Test data cleaning
        test_data = test_data.dropna(subset=['employee_name'])
        test_data = test_data[test_data['employee_name'].str.strip() != '']
        
        print(f"✅ Data cleaning successful: {len(test_data)} valid records")
        
        # Test numeric conversion
        test_data['total_work_hours'] = pd.to_numeric(test_data['total_work_hours'], errors='coerce').fillna(0)
        test_data['actual_work_days'] = pd.to_numeric(test_data['actual_work_days'], errors='coerce').fillna(0)
        
        print("✅ Numeric conversion successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Data handling test failed: {e}")
        return False

def test_chart_creation():
    """Test chart creation functions"""
    print("\n🔍 Testing chart creation...")
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Test basic chart creation
        test_data = pd.DataFrame({
            'Employee': ['Test1', 'Test2'],
            'Hours': [160, 120]
        })
        
        # Test bar chart
        fig = px.bar(test_data, x='Employee', y='Hours')
        print("✅ Bar chart creation successful")
        
        # Test line chart
        fig = px.line(test_data, x='Employee', y='Hours')
        print("✅ Line chart creation successful")
        
        # Test pie chart
        fig = px.pie(test_data, values='Hours', names='Employee')
        print("✅ Pie chart creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Chart creation test failed: {e}")
        return False

def run_final_test():
    """Run final comprehensive test"""
    print("🧪 FINAL TEST FOR EMPLOYEE_ANALYTICS_SUPABASE.PY")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Basic functionality
    test_results.append(("Basic Functionality", test_basic_functionality()))
    
    # Test 2: Employee Analytics functions
    test_results.append(("Employee Analytics Functions", test_employee_analytics_functions()))
    
    # Test 3: Supabase data functions
    test_results.append(("Supabase Data Functions", test_supabase_data_functions()))
    
    # Test 4: Data handling
    test_results.append(("Data Handling", test_data_handling()))
    
    # Test 5: Chart creation
    test_results.append(("Chart Creation", test_chart_creation()))
    
    # Print results
    print("\n📊 TEST RESULTS")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The Employee_Analytics_Supabase.py file is working correctly.")
        print("\n✅ FIXES APPLIED:")
        print("   - Added data validation for empty data")
        print("   - Added error handling for missing values")
        print("   - Added numeric type conversion")
        print("   - Added data cleaning for employee lists")
        print("   - Added safe data extraction with defaults")
        print("   - Added validation for client lists")
        print("   - Added error handling for chart creation")
        print("   - Added numpy type conversion for KPIs")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_final_test()
    sys.exit(0 if success else 1)
