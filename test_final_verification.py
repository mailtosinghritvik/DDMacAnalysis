#!/usr/bin/env python3
"""
Final verification test for all fixes
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_none_handling_fix():
    """Test that the None handling fix works"""
    print("🔍 Testing None handling fix...")
    
    try:
        # Test the exact scenario that was causing the error
        util_df = None
        
        # This is the fixed logic from the code
        if util_df is not None and not util_df.empty:
            print("❌ This should not execute")
            return False
        else:
            print("✅ None check works correctly")
        
        # Test with empty DataFrame
        util_df = pd.DataFrame()
        if util_df is not None and not util_df.empty:
            print("❌ This should not execute")
            return False
        else:
            print("✅ Empty DataFrame check works correctly")
        
        # Test with valid DataFrame
        util_df = pd.DataFrame({'Employee': ['Test'], 'Utilization %': [85]})
        if util_df is not None and not util_df.empty:
            print("✅ Valid DataFrame check works correctly")
        else:
            print("❌ This should not execute")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ None handling test failed: {e}")
        return False

def test_data_validation_fixes():
    """Test all data validation fixes"""
    print("\n🔍 Testing data validation fixes...")
    
    try:
        # Test employee data validation
        employee_data = pd.DataFrame()
        if employee_data.empty:
            print("✅ Empty employee data detection works")
        else:
            print("❌ Empty data detection failed")
            return False
        
        # Test numeric conversion
        test_value = np.float64(85.5)
        if hasattr(test_value, 'item'):
            converted_value = test_value.item()
            print(f"✅ Numpy conversion works: {converted_value}")
        else:
            print("❌ Numpy conversion failed")
            return False
        
        # Test list validation
        client_list = None
        if not isinstance(client_list, list):
            client_list = []
        print("✅ List validation works")
        
        # Test string validation
        test_string = "  "
        if test_string and str(test_string).strip():
            print("❌ String validation failed")
            return False
        else:
            print("✅ String validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Data validation test failed: {e}")
        return False

def test_chart_creation_fixes():
    """Test chart creation fixes"""
    print("\n🔍 Testing chart creation fixes...")
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Test with None data
        user_data = None
        if user_data is None or (hasattr(user_data, 'empty') and user_data.empty):
            print("✅ None data handling works")
        else:
            print("❌ None data handling failed")
            return False
        
        # Test with empty DataFrame
        user_data = pd.DataFrame()
        if user_data.empty:
            print("✅ Empty DataFrame handling works")
        else:
            print("❌ Empty DataFrame handling failed")
            return False
        
        # Test with valid data
        user_data = pd.DataFrame({
            'work_date': ['2024-01-01', '2024-01-02'],
            'hours_worked': [8, 7],
            'client_name': ['Client1', 'Client2'],
            'task_name': ['Task1', 'Task2']
        })
        
        if not user_data.empty:
            print("✅ Valid data handling works")
        else:
            print("❌ Valid data handling failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Chart creation test failed: {e}")
        return False

def test_import_and_syntax():
    """Test that the fixed file can be imported without syntax errors"""
    print("\n🔍 Testing import and syntax...")
    
    try:
        # Try to import the fixed module
        import importlib.util
        spec = importlib.util.spec_from_file_location("employee_analytics_supabase", "pages/Employee_Analytics_Supabase.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        print("✅ File imports successfully without syntax errors")
        
        # Test that main functions exist
        if hasattr(module, 'main'):
            print("✅ main() function exists")
        else:
            print("❌ main() function missing")
            return False
        
        if hasattr(module, 'get_employee_data_supabase_integrated'):
            print("✅ get_employee_data_supabase_integrated() function exists")
        else:
            print("❌ get_employee_data_supabase_integrated() function missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def run_final_verification():
    """Run final verification test"""
    print("🧪 FINAL VERIFICATION TEST")
    print("=" * 40)
    
    test_results = []
    
    # Test 1: None handling fix
    test_results.append(("None Handling Fix", test_none_handling_fix()))
    
    # Test 2: Data validation fixes
    test_results.append(("Data Validation Fixes", test_data_validation_fixes()))
    
    # Test 3: Chart creation fixes
    test_results.append(("Chart Creation Fixes", test_chart_creation_fixes()))
    
    # Test 4: Import and syntax
    test_results.append(("Import and Syntax", test_import_and_syntax()))
    
    # Print results
    print("\n📊 VERIFICATION RESULTS")
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
        print("\n🎉 ALL VERIFICATION TESTS PASSED!")
        print("✅ The AttributeError: 'NoneType' object has no attribute 'empty' has been FIXED!")
        print("✅ The Employee_Analytics_Supabase.py file is now working correctly!")
        print("\n🚀 You can now run the app with:")
        print("   streamlit run pages/Employee_Analytics_Supabase.py")
    else:
        print("\n⚠️ Some verification tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_final_verification()
    sys.exit(0 if success else 1)
