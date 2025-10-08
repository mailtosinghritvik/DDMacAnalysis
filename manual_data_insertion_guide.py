#!/usr/bin/env python3
"""
Manual data insertion guide for project_progress table
This script provides SQL commands and guidance for inserting data
"""

def print_insertion_guide():
    """Print manual insertion guide"""
    print("📊 Manual Data Insertion Guide for project_progress Table")
    print("=" * 70)
    print()
    print("Since there are RLS (Row Level Security) policies on your table,")
    print("you'll need to insert data manually through the Supabase dashboard.")
    print()
    print("🔧 Method 1: Using Supabase Dashboard")
    print("-" * 40)
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to Table Editor")
    print("3. Select the 'project_progress' table")
    print("4. Click 'Insert' and add records manually")
    print()
    print("🔧 Method 2: Using SQL Editor")
    print("-" * 40)
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the following SQL commands:")
    print()
    
    # Sample SQL insert statements
    sample_sql = """
-- Insert sample progress data
INSERT INTO public.project_progress (project_id, jobcode_id, progress, created_at) VALUES
-- Project 1 - Office Building A
(1, 1, 85.5, NOW() - INTERVAL '5 days'),
(1, 2, 92.0, NOW() - INTERVAL '3 days'),
(1, 3, 67.5, NOW() - INTERVAL '1 day'),

-- Project 2 - Residential Complex B
(2, 1, 45.0, NOW() - INTERVAL '7 days'),
(2, 2, 78.5, NOW() - INTERVAL '4 days'),
(2, 4, 23.0, NOW() - INTERVAL '2 days'),

-- Project 3 - Warehouse C
(3, 1, 100.0, NOW() - INTERVAL '10 days'),
(3, 2, 95.0, NOW() - INTERVAL '8 days'),
(3, 3, 88.0, NOW() - INTERVAL '6 days'),

-- Project 4 - Retail Store D
(4, 2, 12.5, NOW() - INTERVAL '1 day'),
(4, 3, 5.0, NOW() - INTERVAL '12 hours'),

-- Project 5 - Hospital E (Completed)
(5, 1, 100.0, NOW() - INTERVAL '15 days'),
(5, 2, 100.0, NOW() - INTERVAL '12 days'),
(5, 3, 100.0, NOW() - INTERVAL '10 days'),
(5, 4, 100.0, NOW() - INTERVAL '8 days'),
(5, 5, 100.0, NOW() - INTERVAL '5 days');
"""
    
    print(sample_sql)
    print()
    print("🔧 Method 3: Disable RLS Temporarily")
    print("-" * 40)
    print("If you have admin access, you can temporarily disable RLS:")
    print()
    print("-- Disable RLS (run as admin)")
    print("ALTER TABLE public.project_progress DISABLE ROW LEVEL SECURITY;")
    print()
    print("-- Insert your data here")
    print("-- (use the SQL above)")
    print()
    print("-- Re-enable RLS (run as admin)")
    print("ALTER TABLE public.project_progress ENABLE ROW LEVEL SECURITY;")
    print()
    print("🔧 Method 4: Create RLS Policy")
    print("-" * 40)
    print("Create a policy that allows inserts:")
    print()
    print("-- Allow inserts for authenticated users")
    print("CREATE POLICY \"Allow inserts for authenticated users\" ON public.project_progress")
    print("FOR INSERT TO authenticated")
    print("WITH CHECK (true);")
    print()
    print("-- Allow selects for authenticated users")
    print("CREATE POLICY \"Allow selects for authenticated users\" ON public.project_progress")
    print("FOR SELECT TO authenticated")
    print("USING (true);")
    print()
    print("-- Allow updates for authenticated users")
    print("CREATE POLICY \"Allow updates for authenticated users\" ON public.project_progress")
    print("FOR UPDATE TO authenticated")
    print("USING (true)")
    print("WITH CHECK (true);")
    print()
    print("-- Allow deletes for authenticated users")
    print("CREATE POLICY \"Allow deletes for authenticated users\" ON public.project_progress")
    print("FOR DELETE TO authenticated")
    print("USING (true);")
    print()
    print("📋 Sample Data Structure")
    print("-" * 40)
    print("The sample data includes:")
    print("• 5 different projects (IDs: 1-5)")
    print("• 5 different jobcodes (IDs: 1-5)")
    print("• Progress values ranging from 5% to 100%")
    print("• Various completion statuses")
    print("• Different timestamps for realistic data")
    print()
    print("🎯 After Inserting Data")
    print("-" * 40)
    print("1. Run: streamlit run Home.py")
    print("2. Navigate to Foreman Analysis page")
    print("3. You should see the progress data and analytics")
    print("4. Test updating progress values using the sliders")

def main():
    """Main function"""
    print_insertion_guide()

if __name__ == "__main__":
    main()
