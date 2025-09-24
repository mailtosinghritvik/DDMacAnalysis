"""
Employee Analytics SQL Handler
Integrates SQL functions with Employee_Analytics.py page
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import os
import sys

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from database_config import get_streamlit_secrets_config, get_database_config
except ImportError:
    # Fallback if config module is not available
    def get_streamlit_secrets_config():
        return {
            'host': 'localhost',
            'database': 'postgres',
            'user': 'postgres',
            'password': 'password',
            'port': 5432
        }
    
    def get_database_config():
        return get_streamlit_secrets_config()

class EmployeeAnalyticsSQLHandler:
    """
    Handles employee analytics data using SQL functions
    """
    
    def __init__(self, connection_params: Dict = None):
        """
        Initialize SQL handler with database connection
        
        Args:
            connection_params (Dict): Database connection parameters
        """
        # Default connection parameters - try to get from configuration
        if connection_params is None:
            try:
                self.connection_params = get_streamlit_secrets_config()
            except:
                self.connection_params = get_database_config()
        else:
            self.connection_params = connection_params
        self.connection = None
    
    def get_connection(self):
        """Get database connection"""
        if self.connection is None or self.connection.closed:
            try:
                self.connection = psycopg2.connect(**self.connection_params)
            except Exception as e:
                st.error(f"Database connection failed: {str(e)}")
                return None
        return self.connection
    
    def execute_query(self, query: str, params: Tuple = None) -> pd.DataFrame:
        """
        Execute SQL query and return DataFrame
        
        Args:
            query (str): SQL query
            params (Tuple): Query parameters
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            conn = self.get_connection()
            if conn is None:
                return pd.DataFrame()
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                if results:
                    df = pd.DataFrame(results)
                    return df
                else:
                    return pd.DataFrame()
                    
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            return pd.DataFrame()
    
    def get_all_employees_summary(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get summary for all employees
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Employee summary data
        """
        query = """
        SELECT * FROM get_all_employees_summary(%s, %s)
        ORDER BY total_work_hours DESC
        """
        return self.execute_query(query, (start_date, end_date))
    
    def get_employee_summary(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get summary for specific employee
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Employee summary data
        """
        query = """
        SELECT * FROM get_employee_summary_data(%s, %s, %s)
        """
        return self.execute_query(query, (user_id, start_date, end_date))
    
    def get_employee_daily_work(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get daily work breakdown for specific employee
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Daily work data
        """
        query = """
        SELECT * FROM get_employee_daily_work_data(%s, %s, %s)
        ORDER BY work_date DESC, client_name, task_name
        """
        return self.execute_query(query, (user_id, start_date, end_date))
    
    def get_employee_weekly_work(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get weekly work breakdown for specific employee
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Weekly work data
        """
        query = """
        SELECT * FROM get_employee_weekly_work_data(%s, %s, %s)
        ORDER BY work_week DESC, client_name, task_name
        """
        return self.execute_query(query, (user_id, start_date, end_date))
    
    def get_employee_productivity_metrics(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get productivity metrics for specific employee
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Productivity metrics
        """
        query = """
        SELECT * FROM get_employee_productivity_metrics(%s, %s, %s)
        """
        return self.execute_query(query, (user_id, start_date, end_date))
    
    def get_employee_performance_rating(self, user_id: int, start_date: str = None, end_date: str = None) -> str:
        """
        Get performance rating for specific employee
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            str: Performance rating
        """
        query = """
        SELECT get_employee_performance_rating(%s, %s, %s) as performance_rating
        """
        result = self.execute_query(query, (user_id, start_date, end_date))
        if not result.empty:
            return result.iloc[0]['performance_rating']
        return 'Unknown'
    
    def get_employee_client_distribution(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get client distribution for specific employee
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Client distribution data
        """
        query = """
        SELECT * FROM get_employee_client_distribution(%s, %s, %s)
        ORDER BY total_hours DESC
        """
        return self.execute_query(query, (user_id, start_date, end_date))
    
    def get_employee_list(self) -> pd.DataFrame:
        """
        Get list of all employees
        
        Returns:
            pd.DataFrame: Employee list
        """
        query = """
        SELECT 
            u.id as user_id,
            u.username,
            COALESCE(u.display_name, CONCAT(u.first_name, ' ', u.last_name)) as full_name,
            u.active
        FROM users u
        WHERE u.active = true
        ORDER BY u.username
        """
        return self.execute_query(query)
    
    def get_employee_kpis(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get employee KPIs for dashboard
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            Dict: KPI metrics
        """
        # Get all employees summary
        df = self.get_all_employees_summary(start_date, end_date)
        
        if df.empty:
            return {
                'total_employees': 0,
                'avg_hours_per_employee': 0,
                'avg_utilization': 0,
                'team_productivity': 0,
                'overtime_pct': 0
            }
        
        # Calculate KPIs
        total_employees = len(df)
        total_hours = df['total_work_hours'].sum()
        avg_hours_per_employee = total_hours / max(1, total_employees)
        
        # Calculate average utilization (assuming 8 hours per day as standard)
        total_days_worked = df['actual_work_days'].sum()
        standard_hours = total_days_worked * 8  # 8 hours per day standard
        avg_utilization = (total_hours / max(1, standard_hours)) * 100 if standard_hours > 0 else 0
        
        # Calculate team productivity based on hours consistency
        daily_averages = df[df['average_daily_hours'] > 0]['average_daily_hours'].tolist()
        if daily_averages:
            productivity_scores = [min(100, (avg / 8) * 100) for avg in daily_averages]
            team_productivity = sum(productivity_scores) / len(productivity_scores)
        else:
            team_productivity = 0
        
        # Calculate overtime percentage (hours over 8 per day)
        overtime_hours = sum(max(0, avg - 8) * days for avg, days in 
                           zip(df['average_daily_hours'], df['actual_work_days']))
        overtime_pct = (overtime_hours / max(1, total_hours)) * 100
        
        return {
            'total_employees': total_employees,
            'avg_hours_per_employee': avg_hours_per_employee,
            'avg_utilization': avg_utilization,
            'team_productivity': team_productivity,
            'overtime_pct': overtime_pct
        }
    
    def get_employee_utilization_chart_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get employee utilization data for charts
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Utilization chart data
        """
        df = self.get_all_employees_summary(start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # Create utilization data
        utilization_data = []
        for _, emp in df.head(10).iterrows():  # Show top 10 employees
            username = emp.get('employee_name', 'Unknown')
            total_hours = emp.get('total_work_hours', 0)
            days_worked = emp.get('actual_work_days', 0)
            
            # Calculate planned hours (assuming 8 hours per day standard)
            planned_hours = days_worked * 8
            actual_hours = total_hours
            utilization_pct = (actual_hours / max(1, planned_hours)) * 100 if planned_hours > 0 else 0
            
            utilization_data.append({
                'Employee': username,
                'Planned Hours': planned_hours,
                'Actual Hours': actual_hours,
                'Utilization %': utilization_pct
            })
        
        return pd.DataFrame(utilization_data)
    
    def get_employee_project_allocation_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get employee project allocation data for charts
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Project allocation data
        """
        df = self.get_all_employees_summary(start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # Create allocation data
        allocation_data = []
        for _, emp in df.head(15).iterrows():  # Show top 15 employees
            username = emp.get('employee_name', 'Unknown')
            clients = emp.get('client_list', [])
            total_hours = emp.get('total_work_hours', 0)
            
            if clients and total_hours > 0:
                # Distribute hours among clients
                hours_per_client = total_hours / len(clients) if clients else 0
                
                for client in clients:
                    allocation_data.append({
                        'Employee': username,
                        'Project': client,
                        'Hours': hours_per_client,
                        'Estimated': hours_per_client * 0.9  # Assume 10% over-estimation
                    })
        
        return pd.DataFrame(allocation_data)
    
    def get_user_summary_data(self, user_id: int, period: str = 'daily', start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get user summary data for individual employee view
        
        Args:
            user_id (int): Employee user ID
            period (str): 'daily' or 'weekly'
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: User summary data
        """
        if period == 'daily':
            return self.get_employee_daily_work(user_id, start_date, end_date)
        else:
            return self.get_employee_weekly_work(user_id, start_date, end_date)
    
    def close_connection(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()

# Convenience functions for easy integration
def get_employee_analytics_handler(connection_params: Dict = None) -> EmployeeAnalyticsSQLHandler:
    """Get configured employee analytics SQL handler instance"""
    return EmployeeAnalyticsSQLHandler(connection_params)

def get_employee_data_sql(connection_params: Dict = None, start_date: str = None, end_date: str = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Get employee data using SQL functions
    
    Args:
        connection_params (Dict): Database connection parameters
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        
    Returns:
        Tuple[pd.DataFrame, Dict]: Employee data and KPIs
    """
    handler = get_employee_analytics_handler(connection_params)
    
    try:
        # Get employee data
        employee_data = handler.get_all_employees_summary(start_date, end_date)
        
        # Get KPIs
        kpis = handler.get_employee_kpis(start_date, end_date)
        
        return employee_data, kpis
        
    except Exception as e:
        st.error(f"Error fetching employee data: {str(e)}")
        return pd.DataFrame(), {}
    finally:
        handler.close_connection()

def get_employee_detailed_data_sql(user_id: int, period: str = 'daily', start_date: str = None, end_date: str = None, connection_params: Dict = None) -> pd.DataFrame:
    """
    Get detailed employee data using SQL functions
    
    Args:
        user_id (int): Employee user ID
        period (str): 'daily' or 'weekly'
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        connection_params (Dict): Database connection parameters
        
    Returns:
        pd.DataFrame: Detailed employee data
    """
    handler = get_employee_analytics_handler(connection_params)
    
    try:
        return handler.get_user_summary_data(user_id, period, start_date, end_date)
    except Exception as e:
        st.error(f"Error fetching detailed employee data: {str(e)}")
        return pd.DataFrame()
    finally:
        handler.close_connection()
