#!/usr/bin/env python3
"""
Test individual insights performance optimization
"""

import sys
import os
import time
import pandas as pd

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_individual_insights_performance():
    """Test performance of individual insights functions"""
    print("🔍 Testing individual insights performance...")
    
    try:
        from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler
        
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Get a test user ID
        employee_list = handler.get_employee_list()
        if employee_list.empty:
            print("❌ No employees found for testing")
            return False
        
        test_user_id = employee_list.iloc[0]['user_id']
        test_username = employee_list.iloc[0]['username']
        
        print(f"Testing with user: {test_username} (ID: {test_user_id})")
        
        # Test 1: Employee summary (first call - should be slow)
        print("\n1. Testing get_employee_summary() - First call...")
        start_time = time.time()
        emp_summary = handler.get_employee_summary(test_user_id, '2024-01-01', '2024-12-31')
        end_time = time.time()
        first_call_time = end_time - start_time
        print(f"✅ First call: {first_call_time:.3f} seconds")
        
        # Test 2: Employee summary (second call - should be fast due to cache)
        print("\n2. Testing get_employee_summary() - Second call (cached)...")
        start_time = time.time()
        emp_summary_cached = handler.get_employee_summary(test_user_id, '2024-01-01', '2024-12-31')
        end_time = time.time()
        second_call_time = end_time - start_time
        print(f"✅ Second call (cached): {second_call_time:.3f} seconds")
        
        # Test 3: Daily work data
        print("\n3. Testing get_employee_daily_work()...")
        start_time = time.time()
        daily_data = handler.get_employee_daily_work(test_user_id, '2024-01-01', '2024-12-31')
        end_time = time.time()
        daily_time = end_time - start_time
        print(f"✅ Daily work data: {daily_time:.3f} seconds")
        
        # Test 4: Productivity metrics
        print("\n4. Testing get_employee_productivity_metrics()...")
        start_time = time.time()
        productivity = handler.get_employee_productivity_metrics(test_user_id, '2024-01-01', '2024-12-31')
        end_time = time.time()
        productivity_time = end_time - start_time
        print(f"✅ Productivity metrics: {productivity_time:.3f} seconds")
        
        # Test 5: Cached productivity metrics
        print("\n5. Testing get_employee_productivity_metrics() - Cached...")
        start_time = time.time()
        productivity_cached = handler.get_employee_productivity_metrics(test_user_id, '2024-01-01', '2024-12-31')
        end_time = time.time()
        productivity_cached_time = end_time - start_time
        print(f"✅ Productivity metrics (cached): {productivity_cached_time:.3f} seconds")
        
        # Performance analysis
        print("\n📊 Performance Analysis:")
        print(f"   First call time: {first_call_time:.3f}s")
        print(f"   Cached call time: {second_call_time:.3f}s")
        print(f"   Cache speedup: {first_call_time / max(second_call_time, 0.001):.1f}x faster")
        
        # Check if performance is acceptable
        total_time = first_call_time + daily_time + productivity_time
        print(f"   Total time for all functions: {total_time:.3f}s")
        
        if total_time < 10:  # Should be under 10 seconds
            print("✅ Performance is acceptable!")
            return True
        else:
            print("⚠️ Performance may still be slow")
            return False
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_caching_effectiveness():
    """Test caching effectiveness"""
    print("\n🔍 Testing caching effectiveness...")
    
    try:
        from utils.supabase_employee_analytics_handler import get_supabase_employee_analytics_handler
        
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
        
        # Get a test user ID
        employee_list = handler.get_employee_list()
        if employee_list.empty:
            print("❌ No employees found for testing")
            return False
        
        test_user_id = employee_list.iloc[0]['user_id']
        
        # Test cache hit rate
        cache_hits = 0
        total_calls = 5
        
        for i in range(total_calls):
            start_time = time.time()
            emp_summary = handler.get_employee_summary(test_user_id, '2024-01-01', '2024-12-31')
            end_time = time.time()
            
            call_time = end_time - start_time
            if call_time < 0.1:  # Very fast = cache hit
                cache_hits += 1
                print(f"   Call {i+1}: {call_time:.3f}s (CACHE HIT)")
            else:
                print(f"   Call {i+1}: {call_time:.3f}s (cache miss)")
        
        cache_hit_rate = (cache_hits / total_calls) * 100
        print(f"✅ Cache hit rate: {cache_hit_rate:.1f}%")
        
        return cache_hit_rate >= 80  # Should have high cache hit rate
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 INDIVIDUAL INSIGHTS PERFORMANCE TEST")
    print("=" * 50)
    
    test1 = test_individual_insights_performance()
    test2 = test_caching_effectiveness()
    
    if test1 and test2:
        print("\n🎉 INDIVIDUAL INSIGHTS PERFORMANCE OPTIMIZED!")
        print("✅ The individual insights section should now load much faster!")
        print("✅ Optimizations applied:")
        print("   - Added caching for all individual functions")
        print("   - Optimized database queries")
        print("   - Limited timesheet data to 5,000 records")
        print("   - Removed expensive custom field queries")
        print("   - Added progress indicators in UI")
        print("   - Cache duration: 5 minutes")
    else:
        print("\n⚠️ Performance optimization may need more work.")
    
    sys.exit(0 if (test1 and test2) else 1)
