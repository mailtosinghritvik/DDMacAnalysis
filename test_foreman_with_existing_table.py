#!/usr/bin/env python3
"""
Test script for Foreman Analysis with existing project_progress table
This script tests the functionality without inserting data
"""

import sys
import os
sys.path.append('.')

from supabase import create_client
import pandas as pd

# Supabase configuration
SUPABASE_URL = "https://tgendmgdrljuxxxyynpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"

def test_table_access():
    """Test if we can access the project_progress table"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to select from the table
        result = supabase.table('project_progress').select('*').limit(5).execute()
        
        if result.data is not None:
            print("✅ Successfully accessed project_progress table")
            print(f"   Found {len(result.data)} existing records")
            
            if result.data:
                df = pd.DataFrame(result.data)
                print("\n📊 Existing Data Summary:")
                print(f"   Columns: {list(df.columns)}")
                print(f"   Data types: {df.dtypes.to_dict()}")
                
                if 'progress' in df.columns:
                    print(f"   Progress range: {df['progress'].min():.1f}% - {df['progress'].max():.1f}%")
                    print(f"   Average progress: {df['progress'].mean():.1f}%")
                
                print("\n📋 Sample Records:")
                for i, record in df.head(3).iterrows():
                    print(f"   Record {i+1}: Project {record.get('project_id', 'N/A')}, Jobcode {record.get('jobcode_id', 'N/A')}, Progress {record.get('progress', 'N/A')}%")
            
            return True
        else:
            print("⚠️ Table exists but is empty")
            return True
            
    except Exception as e:
        print(f"❌ Error accessing project_progress table: {str(e)}")
        return False

def test_other_tables():
    """Test access to other required tables"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        tables_to_test = ['jobcodes', 'projects']
        
        for table_name in tables_to_test:
            try:
                result = supabase.table(table_name).select('*').limit(1).execute()
                if result.data is not None:
                    print(f"✅ {table_name} table accessible")
                else:
                    print(f"⚠️ {table_name} table empty")
            except Exception as e:
                print(f"❌ {table_name} table error: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing other tables: {str(e)}")
        return False

def test_foreman_page_import():
    """Test if the Foreman Analysis page can be imported"""
    try:
        # Try to import the Foreman Analysis page
        from pages.Foreman_Analysis import (
            get_tasks_data,
            get_jobcodes_data,
            get_projects_data,
            get_project_progress_data
        )
        
        print("✅ Foreman Analysis page imports successfully")
        
        # Test the data functions
        print("\n🧪 Testing data functions...")
        
        # Test tasks data
        tasks_df = get_tasks_data()
        print(f"   Tasks data: {len(tasks_df)} records")
        
        # Test jobcodes data
        jobcodes_df = get_jobcodes_data()
        print(f"   Jobcodes data: {len(jobcodes_df)} records")
        
        # Test projects data
        projects_df = get_projects_data()
        print(f"   Projects data: {len(projects_df)} records")
        
        # Test progress data
        progress_df = get_project_progress_data()
        print(f"   Progress data: {len(progress_df)} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing Foreman Analysis page: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Foreman Analysis with existing project_progress table...")
    print("=" * 70)
    
    # Test 1: Table access
    print("Test 1: Project Progress Table Access")
    table_ok = test_table_access()
    
    print()
    
    # Test 2: Other tables
    print("Test 2: Other Required Tables")
    other_tables_ok = test_other_tables()
    
    print()
    
    # Test 3: Foreman page import
    print("Test 3: Foreman Analysis Page Import")
    page_ok = test_foreman_page_import()
    
    print()
    print("=" * 70)
    
    if table_ok and other_tables_ok and page_ok:
        print("🎉 All tests passed! Foreman Analysis is ready to use!")
        print()
        print("Next steps:")
        print("1. Insert some sample data using the SQL provided earlier")
        print("2. Run: streamlit run Home.py")
        print("3. Navigate to Foreman Analysis page")
        print("4. Test the functionality with your data")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print()
        print("Common solutions:")
        print("• Make sure the project_progress table exists")
        print("• Check your Supabase permissions")
        print("• Verify the table structure matches the expected schema")

if __name__ == "__main__":
    main()
