#!/usr/bin/env python3
"""
Quick Test - Check if time analytics functions are deployed
"""

from utils.supabase_queries import get_supabase_handler

def main():
    print("🔍 Quick Database Test")
    print("=" * 30)
    
    handler = get_supabase_handler()
    print(f"✅ Connected: {handler.connected}")
    
    # Test one function
    try:
        result = handler.get_time_period_overview('2020-09-01', '2025-09-24')
        print(f"✅ get_time_period_overview: {result}")
        if result.get('total_hours', 0) > 0:
            print("🎉 REAL DATA FOUND!")
        else:
            print("⚠️ No data in date range")
    except Exception as e:
        if "Could not find the function" in str(e):
            print("❌ Function not deployed")
            print("\n🔧 SOLUTION:")
            print("1. Go to Supabase SQL Editor")
            print("2. Copy contents of 'time_analytics_functions.sql'")
            print("3. Paste and run the SQL")
        else:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
