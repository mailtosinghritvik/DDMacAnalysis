"""
Supabase Employee Analytics Handler
Integrates with Supabase for employee analytics data
"""

import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

class SupabaseEmployeeAnalyticsHandler:
    """
    Handles employee analytics data using Supabase
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize Supabase handler
        
        Args:
            supabase_url (str): Supabase project URL
            supabase_key (str): Supabase API key
        """
        # Use your existing Supabase credentials
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        # Initialize Supabase client
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        except Exception as e:
            st.error(f"Supabase connection failed: {str(e)}")
            self.supabase = None
        
        # Add caching for performance
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_duration = 300  # 5 minutes cache
    
    def _get_from_cache(self, key: str):
        """Get data from cache if not expired"""
        import time
        if key in self._cache and key in self._cache_timestamp:
            if time.time() - self._cache_timestamp[key] < self._cache_duration:
                return self._cache[key]
        return None
    
    def _set_cache(self, key: str, data):
        """Set data in cache with timestamp"""
        import time
        self._cache[key] = data
        self._cache_timestamp[key] = time.time()
    
    def get_all_employees_summary(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get summary for all employees using Supabase function (optimized for performance)
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Employee summary data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Use the comprehensive Supabase function instead of complex Python queries
            response = self.supabase.rpc(
                'get_comprehensive_employee_analytics',
                {
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            df = pd.DataFrame(response.data)
            
            # Convert arrays to lists for better compatibility
            if 'client_list' in df.columns:
                df['client_list'] = df['client_list'].apply(lambda x: x if isinstance(x, list) else [])
            if 'task_list' in df.columns:
                df['task_list'] = df['task_list'].apply(lambda x: x if isinstance(x, list) else [])
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching employee summary: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_summary(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get summary for specific employee using Supabase function
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Employee summary data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        # Check cache first
        cache_key = f"employee_summary_{user_id}_{start_date}_{end_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Use the comprehensive employee analytics function and filter
            response = self.supabase.rpc(
                'get_comprehensive_employee_analytics',
                {
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            # Filter for the specific user
            if response.data:
                user_data = [emp for emp in response.data if emp.get('employee_id') == user_id]
                if user_data:
                    response.data = user_data
                else:
                    response.data = []
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            df = pd.DataFrame(response.data)
            
            # Convert arrays to lists for better compatibility
            if 'client_list' in df.columns:
                df['client_list'] = df['client_list'].apply(lambda x: x if isinstance(x, list) else [])
            if 'task_list' in df.columns:
                df['task_list'] = df['task_list'].apply(lambda x: x if isinstance(x, list) else [])
            
            # Add custom_field_values for compatibility
            df['custom_field_values'] = [[] for _ in range(len(df))]
            
            # Cache the result
            self._set_cache(cache_key, df)
            return df
            
        except Exception as e:
            st.error(f"Error fetching employee summary: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_daily_work(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get daily work breakdown for specific employee using Supabase function
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Daily work data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        # Check cache first
        cache_key = f"daily_work_{user_id}_{start_date}_{end_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Use the individual daily work summary Supabase function
            response = self.supabase.rpc(
                'get_individual_daily_work_summary',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            result = pd.DataFrame(response.data)
            
            # Add custom_field_items column for compatibility
            result['custom_field_items'] = [[] for _ in range(len(result))]
            
            # Cache the result
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            st.error(f"Error fetching daily work data: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_task_distribution(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get task distribution for specific employee using Supabase function
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Task distribution data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Use the individual task distribution Supabase function
            response = self.supabase.rpc(
                'get_individual_task_distribution',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            return pd.DataFrame(response.data)
            
        except Exception as e:
            st.error(f"Error fetching task distribution: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_weekly_work(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get weekly work breakdown for specific employee using Supabase function
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Weekly work data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Use the individual weekly work summary Supabase function
            response = self.supabase.rpc(
                'get_individual_weekly_work_summary',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            result = pd.DataFrame(response.data)
            
            # Add custom_field_items column for compatibility
            result['custom_field_items'] = [[] for _ in range(len(result))]
            
            return result
            
        except Exception as e:
            st.error(f"Error fetching weekly work data: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_productivity_metrics(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get productivity metrics for specific employee using Supabase function
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Productivity metrics
        """
        if not self.supabase:
            return pd.DataFrame()
        
        # Check cache first
        cache_key = f"productivity_{user_id}_{start_date}_{end_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Use the comprehensive employee analytics function and filter
            response = self.supabase.rpc(
                'get_comprehensive_employee_analytics',
                {
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            # Filter for the specific user and extract productivity metrics
            if response.data:
                user_data = [emp for emp in response.data if emp.get('employee_id') == user_id]
                if user_data:
                    emp_data = user_data[0]
                    # Convert to productivity metrics format
                    response.data = [{
                        'employee_id': emp_data.get('employee_id'),
                        'employee_name': emp_data.get('employee_name'),
                        'total_hours': emp_data.get('total_work_hours'),
                        'days_worked': emp_data.get('actual_work_days'),
                        'daily_average': emp_data.get('average_daily_hours'),
                        'productivity_score': emp_data.get('productivity_score'),
                        'utilization_percentage': emp_data.get('utilization_percentage'),
                        'overtime_hours': emp_data.get('overtime_hours'),
                        'performance_rating': emp_data.get('performance_rating')
                    }]
                else:
                    response.data = []
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            result = pd.DataFrame(response.data)
            
            # Cache the result
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            st.error(f"Error fetching productivity metrics: {str(e)}")
            return pd.DataFrame()
    
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
        try:
            productivity_data = self.get_employee_productivity_metrics(user_id, start_date, end_date)
            
            if productivity_data.empty:
                return 'Unknown'
            
            daily_average = productivity_data.iloc[0]['daily_average']
            
            if daily_average >= 8.0:
                return 'Excellent'
            elif daily_average >= 6.0:
                return 'Good'
            elif daily_average >= 4.0:
                return 'Average'
            else:
                return 'Needs Improvement'
                
        except Exception as e:
            st.error(f"Error fetching performance rating: {str(e)}")
            return 'Unknown'
    
    def get_employee_client_distribution(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get client distribution for specific employee using Supabase function
        
        Args:
            user_id (int): Employee user ID
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Client distribution data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Use the individual client distribution Supabase function
            response = self.supabase.rpc(
                'get_individual_client_distribution',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            # Convert the response to DataFrame
            return pd.DataFrame(response.data)
            
        except Exception as e:
            st.error(f"Error fetching client distribution: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_list(self) -> pd.DataFrame:
        """
        Get list of all employees (optimized for performance)
        
        Returns:
            pd.DataFrame: Employee list
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Only get active users
            users_response = self.supabase.table('users').select('id, username, first_name, last_name, display_name').eq('active', True).execute()
            users_data = users_response.data
            
            if not users_data:
                return pd.DataFrame()
            
            employee_list = []
            for user in users_data:
                employee_list.append({
                    'user_id': user['id'],
                    'username': user.get('username', 'Unknown'),
                    'full_name': user.get('display_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    'active': True
                })
            
            return pd.DataFrame(employee_list)
            
        except Exception as e:
            st.error(f"Error fetching employee list: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_kpis(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get employee KPIs for dashboard using Supabase function
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            Dict: KPI metrics
        """
        if not self.supabase:
            return {
                'total_employees': 0,
                'avg_hours_per_employee': 0,
                'avg_utilization': 0,
                'team_productivity': 0,
                'overtime_pct': 0
            }
        
        try:
            # Use the comprehensive KPI Supabase function
            response = self.supabase.rpc(
                'get_employee_kpis_comprehensive',
                {
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return {
                    'total_employees': 0,
                    'avg_hours_per_employee': 0,
                    'avg_utilization': 0,
                    'team_productivity': 0,
                    'overtime_pct': 0
                }
            
            # Extract the first (and only) row of results
            kpi_data = response.data[0]
            
            return {
                'total_employees': kpi_data.get('total_employees', 0),
                'avg_hours_per_employee': kpi_data.get('avg_daily_hours_per_employee', 0),
                'avg_utilization': kpi_data.get('avg_utilization', 0),
                'team_productivity': kpi_data.get('team_productivity', 0),
                'overtime_pct': kpi_data.get('overtime_percentage', 0)
            }
            
        except Exception as e:
            st.error(f"Error calculating KPIs: {str(e)}")
            return {
                'total_employees': 0,
                'avg_hours_per_employee': 0,
                'avg_utilization': 0,
                'team_productivity': 0,
                'overtime_pct': 0
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
        try:
            all_employees = self.get_all_employees_summary(start_date, end_date)
            
            if all_employees.empty:
                return pd.DataFrame()
            
            # Create utilization data
            utilization_data = []
            for _, emp in all_employees.head(10).iterrows():  # Show top 10 employees
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
            
        except Exception as e:
            st.error(f"Error fetching utilization chart data: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_project_allocation_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get employee project allocation data for charts
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Project allocation data
        """
        try:
            all_employees = self.get_all_employees_summary(start_date, end_date)
            
            if all_employees.empty:
                return pd.DataFrame()
            
            # Create allocation data
            allocation_data = []
            for _, emp in all_employees.head(15).iterrows():  # Show top 15 employees
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
            
        except Exception as e:
            st.error(f"Error fetching project allocation data: {str(e)}")
            return pd.DataFrame()
    
    def get_user_summary_data(self, user_id: int, period: str = 'daily', start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get user summary data for individual employee view using Supabase function
        
        Args:
            user_id (int): Employee user ID
            period (str): 'daily' or 'weekly'
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: User summary data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            if period == 'daily':
                # Use the detailed data Supabase function for daily data
                response = self.supabase.rpc(
                    'get_employee_detailed_data',
                    {
                        'user_id_param': user_id,
                        'start_date_param': start_date,
                        'end_date_param': end_date
                    }
                ).execute()
                
                if not response.data:
                    return pd.DataFrame()
                
                df = pd.DataFrame(response.data)
                
                # Add custom_field_items column for compatibility
                df['custom_field_items'] = [[] for _ in range(len(df))]
                
                return df
            else:
                # For weekly data, get daily data and group by week
                daily_data = self.get_user_summary_data(user_id, 'daily', start_date, end_date)
                
                if daily_data.empty:
                    return pd.DataFrame()
                
                # Group by week
                daily_data['work_date'] = pd.to_datetime(daily_data['work_date'], errors='coerce')
                daily_data = daily_data.dropna(subset=['work_date'])
                
                if daily_data.empty:
                    return pd.DataFrame()
                
                # Convert to week start date
                daily_data['work_week'] = (daily_data['work_date'] - pd.to_timedelta(daily_data['work_date'].dt.dayofweek, unit='D')).dt.date
                
                weekly_data = daily_data.groupby(['work_week', 'client_name', 'task_name', 'job_code']).agg({
                    'hours_worked': 'sum',
                    'custom_field_items': lambda x: list(set([item for sublist in x for item in sublist]))
                }).reset_index()
                
                return weekly_data.rename(columns={'work_week': 'work_week'})
                
        except Exception as e:
            st.error(f"Error fetching user summary data: {str(e)}")
            return pd.DataFrame()

# Convenience functions for easy integration
def get_supabase_employee_analytics_handler(supabase_url: str = None, supabase_key: str = None) -> SupabaseEmployeeAnalyticsHandler:
    """Get configured Supabase employee analytics handler instance"""
    return SupabaseEmployeeAnalyticsHandler(supabase_url, supabase_key)

def get_employee_data_supabase(supabase_url: str = None, supabase_key: str = None, start_date: str = None, end_date: str = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Get employee data using Supabase
    
    Args:
        supabase_url (str): Supabase project URL
        supabase_key (str): Supabase API key
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        
    Returns:
        Tuple[pd.DataFrame, Dict]: Employee data and KPIs
    """
    handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
    
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
        # Supabase client doesn't need explicit closing
        pass

def get_employee_detailed_data_supabase(user_id: int, period: str = 'daily', start_date: str = None, end_date: str = None, supabase_url: str = None, supabase_key: str = None) -> pd.DataFrame:
    """
    Get detailed employee data using Supabase
    
    Args:
        user_id (int): Employee user ID
        period (str): 'daily' or 'weekly'
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        supabase_url (str): Supabase project URL
        supabase_key (str): Supabase API key
        
    Returns:
        pd.DataFrame: Detailed employee data
    """
    handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
    
    try:
        return handler.get_user_summary_data(user_id, period, start_date, end_date)
    except Exception as e:
        st.error(f"Error fetching detailed employee data: {str(e)}")
        return pd.DataFrame()
