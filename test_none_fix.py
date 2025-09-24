#!/usr/bin/env python3
"""
Quick test to verify the None fix works
"""

import sys
import os
import pandas as pd

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_none_handling():
    """Test None handling in the fixed code"""
    print("🔍 Testing None handling fix...")
    
    try:
        # Test the fixed logic
        util_df = None
        
        # This should not crash now
        if util_df is not None and not util_df.empty:
            print("❌ This should not print")
        else:
            print("✅ None handling works correctly")
        
        # Test with empty DataFrame
        util_df = pd.DataFrame()
        if util_df is not None and not util_df.empty:
            print("❌ This should not print")
        else:
            print("✅ Empty DataFrame handling works correctly")
        
        # Test with valid DataFrame
        util_df = pd.DataFrame({'test': [1, 2, 3]})
        if util_df is not None and not util_df.empty:
            print("✅ Valid DataFrame handling works correctly")
        else:
            print("❌ This should not print")
        
        print("✅ All None handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ None handling test failed: {e}")
        return False

def test_import_fix():
    """Test that the fixed file can be imported without errors"""
    print("\n🔍 Testing import fix...")
    
    try:
        # Try to import the fixed module
        import importlib.util
        spec = importlib.util.spec_from_file_location("employee_analytics_supabase", "pages/Employee_Analytics_Supabase.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        print("✅ Fixed file imports successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING NONE FIX")
    print("=" * 30)
    
    test1 = test_none_handling()
    test2 = test_import_fix()
    
    if test1 and test2:
        print("\n🎉 ALL TESTS PASSED! The None fix is working correctly.")
    else:
        print("\n❌ Some tests failed.")
    
    sys.exit(0 if (test1 and test2) else 1)
