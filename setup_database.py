#!/usr/bin/env python3
"""
Database Setup Script for Employee Analytics
This script helps you configure the database connection
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def test_database_connection(host, database, user, password, port):
    """Test database connection"""
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        print("✅ Database connection successful!")
        
        # Test if required tables exist
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'timesheets', 'jobcodes', 'projects')
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            required_tables = ['users', 'timesheets', 'jobcodes', 'projects']
            existing_tables = [table['table_name'] for table in tables]
            
            print(f"📋 Found tables: {existing_tables}")
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                print(f"⚠️ Missing required tables: {missing_tables}")
                return False
            else:
                print("✅ All required tables found!")
                return True
                
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_secrets_file(host, database, user, password, port):
    """Create Streamlit secrets file"""
    secrets_content = f"""[secrets]
DB_HOST = "{host}"
DB_NAME = "{database}"
DB_USER = "{user}"
DB_PASSWORD = "{password}"
DB_PORT = {port}
"""
    
    # Create .streamlit directory if it doesn't exist
    os.makedirs('.streamlit', exist_ok=True)
    
    # Write secrets file
    with open('.streamlit/secrets.toml', 'w') as f:
        f.write(secrets_content)
    
    print("✅ Created .streamlit/secrets.toml file")
    print("🔒 Make sure to add .streamlit/secrets.toml to your .gitignore file!")

def main():
    """Main setup function"""
    print("🔧 Employee Analytics Database Setup")
    print("=" * 40)
    
    # Get database connection details
    print("Please enter your database connection details:")
    host = input("Database Host [localhost]: ").strip() or "localhost"
    database = input("Database Name [postgres]: ").strip() or "postgres"
    user = input("Database User [postgres]: ").strip() or "postgres"
    password = input("Database Password: ").strip()
    port = input("Database Port [5432]: ").strip() or "5432"
    
    try:
        port = int(port)
    except ValueError:
        print("❌ Invalid port number. Using default 5432.")
        port = 5432
    
    print(f"\n🔍 Testing connection to {host}:{port}/{database}...")
    
    # Test connection
    if test_database_connection(host, database, user, password, port):
        print("\n🎉 Database connection successful!")
        
        # Ask if user wants to create secrets file
        create_secrets = input("\nDo you want to create a Streamlit secrets file? (y/n): ").strip().lower()
        if create_secrets in ['y', 'yes']:
            create_secrets_file(host, database, user, password, port)
            print("\n✅ Setup complete! You can now run the Employee Analytics application.")
        else:
            print("\n✅ Database connection verified. You can manually configure the connection parameters.")
    else:
        print("\n❌ Setup failed. Please check your database connection details.")
        print("\nTroubleshooting tips:")
        print("1. Make sure your database server is running")
        print("2. Check if the host, port, and credentials are correct")
        print("3. Ensure the database exists and is accessible")
        print("4. Check if your firewall allows connections to the database port")

if __name__ == "__main__":
    main()
