# Employee Analytics - Troubleshooting Guide

## 🔧 Database Connection Issues

### Error: "could not translate host name 'your_host' to address"

This error occurs when the database connection parameters are not properly configured.

#### Solution 1: Update Connection Parameters

1. **Edit the connection parameters directly in the code:**

```python
# In pages/Employee_Analytics_SQL.py, update the connection_params:
connection_params = {
    'host': 'your_actual_host',        # e.g., 'localhost' or '192.168.1.100'
    'database': 'your_actual_database', # e.g., 'postgres' or 'your_db_name'
    'user': 'your_actual_user',        # e.g., 'postgres' or 'your_username'
    'password': 'your_actual_password', # your actual password
    'port': 5432                       # your actual port
}
```

2. **Use the Database Configuration section in the app:**
   - Open the "🔧 Database Configuration" expander
   - Enter your actual database details
   - Click "🔍 Test Database Connection"

#### Solution 2: Use Streamlit Secrets

1. **Create a secrets file:**
```bash
mkdir -p .streamlit
```

2. **Create `.streamlit/secrets.toml`:**
```toml
[secrets]
DB_HOST = "your_actual_host"
DB_NAME = "your_actual_database"
DB_USER = "your_actual_user"
DB_PASSWORD = "your_actual_password"
DB_PORT = 5432
```

3. **Add to .gitignore:**
```bash
echo ".streamlit/secrets.toml" >> .gitignore
```

#### Solution 3: Use Environment Variables

```bash
export DB_HOST="your_actual_host"
export DB_NAME="your_actual_database"
export DB_USER="your_actual_user"
export DB_PASSWORD="your_actual_password"
export DB_PORT="5432"
```

### Common Database Connection Issues

#### 1. PostgreSQL Not Running
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

#### 2. Wrong Port
- Default PostgreSQL port: 5432
- Check your database configuration
- Some cloud providers use different ports

#### 3. Firewall Issues
```bash
# Check if port is accessible
telnet your_host 5432

# Open firewall port (Ubuntu/Debian)
sudo ufw allow 5432
```

#### 4. Authentication Issues
- Check username and password
- Verify database user has proper permissions
- Check pg_hba.conf for authentication method

### Database Setup Verification

#### 1. Test Connection Manually
```python
import psycopg2

try:
    conn = psycopg2.connect(
        host='your_host',
        database='your_database',
        user='your_user',
        password='your_password',
        port=5432
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

#### 2. Check Required Tables
```sql
-- Run this in your database to check if required tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'timesheets', 'jobcodes', 'projects')
ORDER BY table_name;
```

#### 3. Install SQL Functions
```sql
-- Run the SQL functions file in your database
\i employee_analytics_sql_functions.sql
```

## 🐍 Python Dependencies

### Missing Dependencies
```bash
pip install psycopg2-binary
pip install streamlit
pip install pandas
pip install plotly
pip install numpy
```

### Import Errors
```python
# If you get import errors, check your Python path
import sys
print(sys.path)

# Add the project directory to Python path
sys.path.append('/path/to/your/project')
```

## 🚀 Application Issues

### Streamlit Not Starting
```bash
# Check if Streamlit is installed
pip install streamlit

# Run the application
streamlit run pages/Employee_Analytics_SQL.py
```

### Port Already in Use
```bash
# Kill existing Streamlit processes
pkill -f streamlit

# Or use a different port
streamlit run pages/Employee_Analytics_SQL.py --server.port 8502
```

### Module Not Found Errors
```bash
# Make sure you're in the correct directory
cd /path/to/your/project

# Check if all files exist
ls -la pages/Employee_Analytics_SQL.py
ls -la utils/employee_analytics_sql_handler.py
ls -la config/database_config.py
```

## 🔍 Debugging Steps

### 1. Enable Debug Mode
```python
# Add this to your code for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Check Database Logs
```bash
# PostgreSQL logs (Ubuntu/Debian)
sudo tail -f /var/log/postgresql/postgresql-*.log

# Check connection attempts
sudo grep "connection" /var/log/postgresql/postgresql-*.log
```

### 3. Test SQL Functions
```sql
-- Test if functions exist
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name LIKE 'get_employee%';
```

### 4. Check Data
```sql
-- Check if you have data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM timesheets;
SELECT COUNT(*) FROM jobcodes;
```

## 🛠️ Quick Fixes

### 1. Reset Configuration
```bash
# Remove old secrets file
rm .streamlit/secrets.toml

# Run setup script
python setup_database.py
```

### 2. Update All Connection Parameters
```bash
# Find and replace all connection parameters
grep -r "your_host" . --include="*.py"
grep -r "your_database" . --include="*.py"
grep -r "your_user" . --include="*.py"
grep -r "your_password" . --include="*.py"
```

### 3. Verify Database Schema
```sql
-- Check if your database has the required schema
\d users
\d timesheets
\d jobcodes
\d projects
```

## 📞 Getting Help

### 1. Check Logs
```bash
# Streamlit logs
streamlit run pages/Employee_Analytics_SQL.py --logger.level debug

# Database logs
sudo journalctl -u postgresql
```

### 2. Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `could not translate host name` | Wrong hostname | Update DB_HOST |
| `authentication failed` | Wrong credentials | Check username/password |
| `database does not exist` | Wrong database name | Check DB_NAME |
| `connection refused` | Database not running | Start PostgreSQL |
| `permission denied` | User lacks permissions | Grant database access |

### 3. Test Commands
```bash
# Test database connection
psql -h your_host -U your_user -d your_database

# Test Python connection
python -c "import psycopg2; print('psycopg2 installed')"

# Test Streamlit
streamlit --version
```

## ✅ Success Checklist

- [ ] Database server is running
- [ ] Connection parameters are correct
- [ ] Required tables exist
- [ ] SQL functions are installed
- [ ] Python dependencies are installed
- [ ] Streamlit is running
- [ ] No firewall issues
- [ ] User has proper permissions

## 🎯 Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database
python setup_database.py

# 3. Run application
streamlit run pages/Employee_Analytics_SQL.py

# 4. Test connection
# Use the "🔧 Database Configuration" section in the app
```

If you're still having issues, please check:
1. Your database server is running
2. Your connection parameters are correct
3. Your database has the required tables
4. Your Python environment has all dependencies
5. Your firewall allows database connections
