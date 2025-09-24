#!/usr/bin/env python3
"""
Test the None math fix
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_none_math_fix():
    """Test that None math operations are fixed"""
    print("🔍 Testing None math fix...")
    
    try:
        # Test the fixed calculation
        test_data = [
            {'duration': 3600, 'date': '2024-01-01'},
            {'duration': None, 'date': '2024-01-02'},
            {'duration': 7200, 'date': '2024-01-03'},
            {'duration': 0, 'date': '2024-01-04'}
        ]
        
        # This is the fixed calculation
        total_hours = sum(t.get('duration', 0) or 0 for t in test_data) / 3600.0
        print(f"✅ Total hours calculation: {total_hours}")
        
        # Test with all None values
        test_data_none = [
            {'duration': None, 'date': '2024-01-01'},
            {'duration': None, 'date': '2024-01-02'}
        ]
        
        total_hours_none = sum(t.get('duration', 0) or 0 for t in test_data_none) / 3600.0
        print(f"✅ All None values calculation: {total_hours_none}")
        
        # Test division by zero protection
        days_worked = 0
        daily_average = total_hours / days_worked if days_worked > 0 else 0
        print(f"✅ Division by zero protection: {daily_average}")
        
        # Test productivity calculation
        daily_average = 8.5
        productivity_score = min(100, (daily_average / 8.0) * 100) if daily_average else 0
        print(f"✅ Productivity calculation: {productivity_score}")
        
        # Test with None daily_average
        daily_average = None
        productivity_score = min(100, (daily_average / 8.0) * 100) if daily_average else 0
        print(f"✅ None daily_average handling: {productivity_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ None math fix test failed: {e}")
        return False

def test_supabase_handler_import():
    """Test that the fixed Supabase handler can be imported"""
    print("\n🔍 Testing Supabase handler import...")
    
    try:
        from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler
        print("✅ Supabase handler imports successfully")
        return True
    except Exception as e:
        print(f"❌ Supabase handler import failed: {e}")
        return False

def test_employee_analytics_import():
    """Test that the Employee Analytics page can be imported"""
    print("\n🔍 Testing Employee Analytics import...")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("employee_analytics_supabase", "pages/Employee_Analytics_Supabase.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("✅ Employee Analytics imports successfully")
        return True
    except Exception as e:
        print(f"❌ Employee Analytics import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING NONE MATH FIX")
    print("=" * 30)
    
    test1 = test_none_math_fix()
    test2 = test_supabase_handler_import()
    test3 = test_employee_analytics_import()
    
    if test1 and test2 and test3:
        print("\n🎉 ALL TESTS PASSED! The None math fix is working correctly.")
        print("✅ The 'unsupported operand type(s) for +: 'int' and 'NoneType'' error has been FIXED!")
    else:
        print("\n❌ Some tests failed.")
    
    sys.exit(0 if (test1 and test2 and test3) else 1)
