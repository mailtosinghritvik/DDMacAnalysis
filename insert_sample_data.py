#!/usr/bin/env python3
"""
Script to insert sample data into the project_progress table
This will populate the table with test data for the Foreman Analysis page
"""

import sys
import os
sys.path.append('.')

from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import random

# Supabase configuration
SUPABASE_URL = "https://tgendmgdrljuxxxyynpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"

def test_table_connection():
    """Test if we can connect to the project_progress table"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to select from the table
        result = supabase.table('project_progress').select('*').limit(1).execute()
        print("✅ Successfully connected to project_progress table")
        return supabase
    except Exception as e:
        print(f"❌ Error connecting to project_progress table: {str(e)}")
        return None

def clear_existing_data(supabase):
    """Clear any existing data from the table"""
    try:
        result = supabase.table('project_progress').delete().neq('id', 0).execute()
        print("✅ Cleared existing data from project_progress table")
        return True
    except Exception as e:
        print(f"⚠️ Could not clear existing data: {str(e)}")
        return False

def insert_sample_progress_data(supabase):
    """Insert sample progress data"""
    try:
        # Sample data for different projects and jobcodes
        sample_data = [
            # Project 1 - Office Building A
            {'project_id': 1, 'jobcode_id': 1, 'progress': 85.5, 'created_at': (datetime.now() - timedelta(days=5)).isoformat()},
            {'project_id': 1, 'jobcode_id': 2, 'progress': 92.0, 'created_at': (datetime.now() - timedelta(days=3)).isoformat()},
            {'project_id': 1, 'jobcode_id': 3, 'progress': 67.5, 'created_at': (datetime.now() - timedelta(days=1)).isoformat()},
            
            # Project 2 - Residential Complex B
            {'project_id': 2, 'jobcode_id': 1, 'progress': 45.0, 'created_at': (datetime.now() - timedelta(days=7)).isoformat()},
            {'project_id': 2, 'jobcode_id': 2, 'progress': 78.5, 'created_at': (datetime.now() - timedelta(days=4)).isoformat()},
            {'project_id': 2, 'jobcode_id': 4, 'progress': 23.0, 'created_at': (datetime.now() - timedelta(days=2)).isoformat()},
            
            # Project 3 - Warehouse C
            {'project_id': 3, 'jobcode_id': 1, 'progress': 100.0, 'created_at': (datetime.now() - timedelta(days=10)).isoformat()},
            {'project_id': 3, 'jobcode_id': 2, 'progress': 95.0, 'created_at': (datetime.now() - timedelta(days=8)).isoformat()},
            {'project_id': 3, 'jobcode_id': 3, 'progress': 88.0, 'created_at': (datetime.now() - timedelta(days=6)).isoformat()},
            
            # Project 4 - Retail Store D
            {'project_id': 4, 'jobcode_id': 2, 'progress': 12.5, 'created_at': (datetime.now() - timedelta(days=1)).isoformat()},
            {'project_id': 4, 'jobcode_id': 3, 'progress': 5.0, 'created_at': (datetime.now() - timedelta(hours=12)).isoformat()},
            
            # Project 5 - Hospital E
            {'project_id': 5, 'jobcode_id': 1, 'progress': 100.0, 'created_at': (datetime.now() - timedelta(days=15)).isoformat()},
            {'project_id': 5, 'jobcode_id': 2, 'progress': 100.0, 'created_at': (datetime.now() - timedelta(days=12)).isoformat()},
            {'project_id': 5, 'jobcode_id': 3, 'progress': 100.0, 'created_at': (datetime.now() - timedelta(days=10)).isoformat()},
            {'project_id': 5, 'jobcode_id': 4, 'progress': 100.0, 'created_at': (datetime.now() - timedelta(days=8)).isoformat()},
            {'project_id': 5, 'jobcode_id': 5, 'progress': 100.0, 'created_at': (datetime.now() - timedelta(days=5)).isoformat()},
        ]
        
        # Insert data in batches
        batch_size = 5
        for i in range(0, len(sample_data), batch_size):
            batch = sample_data[i:i + batch_size]
            result = supabase.table('project_progress').insert(batch).execute()
            
            if result.data:
                print(f"✅ Inserted batch {i//batch_size + 1} ({len(batch)} records)")
            else:
                print(f"❌ Failed to insert batch {i//batch_size + 1}")
                return False
        
        print(f"✅ Successfully inserted {len(sample_data)} sample records")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {str(e)}")
        return False

def verify_data_insertion(supabase):
    """Verify that data was inserted correctly"""
    try:
        result = supabase.table('project_progress').select('*').execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            print(f"✅ Verification successful: {len(df)} records found")
            
            # Show summary statistics
            print("\n📊 Data Summary:")
            print(f"   Total records: {len(df)}")
            print(f"   Unique projects: {df['project_id'].nunique()}")
            print(f"   Unique jobcodes: {df['jobcode_id'].nunique()}")
            print(f"   Average progress: {df['progress'].mean():.1f}%")
            print(f"   Min progress: {df['progress'].min():.1f}%")
            print(f"   Max progress: {df['progress'].max():.1f}%")
            
            # Show sample records
            print("\n📋 Sample Records:")
            sample_records = df.head(5)
            for _, record in sample_records.iterrows():
                print(f"   Project {record['project_id']}, Jobcode {record['jobcode_id']}: {record['progress']}%")
            
            return True
        else:
            print("❌ No data found after insertion")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying data: {str(e)}")
        return False

def main():
    """Main function to insert sample data"""
    print("📊 Inserting sample data into project_progress table...")
    print("=" * 60)
    
    # Step 1: Test connection
    print("Step 1: Testing table connection...")
    supabase = test_table_connection()
    if not supabase:
        print("❌ Cannot proceed without database connection")
        return False
    
    print()
    
    # Step 2: Clear existing data (optional)
    print("Step 2: Clearing existing data...")
    clear_existing_data(supabase)
    
    print()
    
    # Step 3: Insert sample data
    print("Step 3: Inserting sample progress data...")
    if insert_sample_progress_data(supabase):
        print("✅ Sample data inserted successfully")
    else:
        print("❌ Failed to insert sample data")
        return False
    
    print()
    
    # Step 4: Verify insertion
    print("Step 4: Verifying data insertion...")
    if verify_data_insertion(supabase):
        print("✅ Data verification successful")
    else:
        print("❌ Data verification failed")
        return False
    
    print()
    print("🎉 Sample data insertion completed successfully!")
    print("=" * 60)
    print("You can now:")
    print("1. Run the Streamlit app: streamlit run Home.py")
    print("2. Navigate to Foreman Analysis page")
    print("3. View the progress data and analytics")
    print("4. Test updating progress values")
    
    return True

if __name__ == "__main__":
    main()
