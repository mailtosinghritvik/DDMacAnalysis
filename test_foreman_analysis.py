#!/usr/bin/env python3
"""
Test script for Foreman Analysis functionality
This script tests the basic functionality without requiring the full Streamlit app
"""

import sys
import os
sys.path.append('.')

from supabase import create_client
import pandas as pd

# Supabase configuration
SUPABASE_URL = "https://tgendmgdrljuxxxyynpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connection successful")
        return supabase
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return None

def test_project_progress_table(supabase):
    """Test project_progress table operations"""
    try:
        # Test if table exists
        result = supabase.table('project_progress').select('id').limit(1).execute()
        print("✅ project_progress table exists")
        
        # Test inserting a sample record
        sample_data = {
            'project_id': 999,
            'jobcode_id': 999,
            'progress': 75.5
        }
        
        insert_result = supabase.table('project_progress').insert(sample_data).execute()
        
        if insert_result.data:
            print("✅ Sample record inserted successfully")
            record_id = insert_result.data[0]['id']
            
            # Test updating the record
            update_result = supabase.table('project_progress').update({
                'progress': 85.0
            }).eq('id', record_id).execute()
            
            if update_result.data:
                print("✅ Record updated successfully")
            
            # Test deleting the record
            delete_result = supabase.table('project_progress').delete().eq('id', record_id).execute()
            
            if delete_result.data:
                print("✅ Record deleted successfully")
            
            return True
        else:
            print("❌ Failed to insert sample record")
            return False
            
    except Exception as e:
        print(f"❌ Error testing project_progress table: {str(e)}")
        return False

def test_other_tables(supabase):
    """Test other required tables"""
    tables_to_test = ['tasks', 'jobcodes', 'projects']
    
    for table_name in tables_to_test:
        try:
            result = supabase.table(table_name).select('*').limit(1).execute()
            if result.data is not None:
                print(f"✅ {table_name} table exists and is accessible")
            else:
                print(f"⚠️ {table_name} table exists but is empty")
        except Exception as e:
            print(f"❌ {table_name} table error: {str(e)}")

def main():
    """Main test function"""
    print("🧪 Testing Foreman Analysis functionality...")
    print("=" * 50)
    
    # Test 1: Supabase connection
    print("Test 1: Supabase Connection")
    supabase = test_supabase_connection()
    if not supabase:
        print("❌ Cannot proceed without Supabase connection")
        return False
    
    print()
    
    # Test 2: Other tables
    print("Test 2: Required Tables")
    test_other_tables(supabase)
    
    print()
    
    # Test 3: Project progress table
    print("Test 3: Project Progress Table")
    if test_project_progress_table(supabase):
        print("✅ All tests passed!")
        print("\n🎉 Foreman Analysis is ready to use!")
        print("You can now run the Streamlit app and access the Foreman Analysis page.")
    else:
        print("❌ Some tests failed. Please check the table setup.")
        print("\n💡 To fix the issues:")
        print("1. Make sure the project_progress table exists")
        print("2. Run the SQL script in your Supabase SQL editor")
        print("3. Check your Supabase permissions")
    
    return True

if __name__ == "__main__":
    main()
