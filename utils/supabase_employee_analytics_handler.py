"""
Supabase Employee Analytics Handler
Integrates with Supabase for employee analytics data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
from supabase import create_client, Client

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
        self.supabase_url = supabase_url or "https://tgendmgdrljuxxxyynpz.supabase.co"
        self.supabase_key = supabase_key or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
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
        Get summary for all employees using Supabase (optimized for performance)
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Employee summary data
        """
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Get all users (limit to active users only for performance)
            users_response = self.supabase.table('users').select('id, username, first_name, last_name, display_name').eq('active', True).execute()
            users_data = users_response.data
            
            if not users_data:
                return pd.DataFrame()
            
            # Get all timesheet data in one query (much faster)
            timesheet_query = self.supabase.table('timesheets').select('user_id, duration, date, jobcode_id')
            
            if start_date:
                timesheet_query = timesheet_query.gte('date', start_date)
            if end_date:
                timesheet_query = timesheet_query.lte('date', end_date)
            
            # Limit timesheet data for performance
            timesheet_query = timesheet_query.limit(10000)
            timesheets_response = timesheet_query.execute()
            timesheets_data = timesheets_response.data
            
            if not timesheets_data:
                return pd.DataFrame()
            
            # Group timesheet data by user_id for faster processing
            user_timesheets = {}
            for timesheet in timesheets_data:
                user_id = timesheet.get('user_id')
                if user_id not in user_timesheets:
                    user_timesheets[user_id] = []
                user_timesheets[user_id].append(timesheet)
            
            # Get all unique jobcode_ids
            all_jobcode_ids = list(set(t.get('jobcode_id') for t in timesheets_data if t.get('jobcode_id')))
            
            # Get jobcodes data in one query
            jobcodes_data = {}
            if all_jobcode_ids:
                jobcodes_response = self.supabase.table('jobcodes').select('id, name, short_code').in_('id', all_jobcode_ids).execute()
                jobcodes_data = {j['id']: j for j in jobcodes_response.data}
            
            # Get projects data in one query
            projects_data = {}
            if all_jobcode_ids:
                projects_response = self.supabase.table('projects').select('jobcode_id, name').in_('jobcode_id', all_jobcode_ids).execute()
                projects_data = {p['jobcode_id']: p for p in projects_response.data}
            
            # Process each user
            employee_summaries = []
            
            for user in users_data:
                user_id = user['id']
                
                # Get timesheet data for this user (empty list if no data)
                user_timesheet_data = user_timesheets.get(user_id, [])
                
                # Calculate summary metrics
                total_hours = sum(t.get('duration', 0) or 0 for t in user_timesheet_data) / 3600.0
                work_dates = list(set(t.get('date') for t in user_timesheet_data if t.get('date')))
                days_worked = len(work_dates)
                daily_average = total_hours / days_worked if days_worked > 0 else 0
                
                # Get unique jobcodes for this user
                jobcode_ids = list(set(t.get('jobcode_id') for t in user_timesheet_data if t.get('jobcode_id')))
                
                # Get jobcode names from cached data
                clients = []
                tasks = []
                for jobcode_id in jobcode_ids:
                    if jobcode_id in jobcodes_data:
                        jobcode = jobcodes_data[jobcode_id]
                        if jobcode.get('name'):
                            clients.append(jobcode['name'])
                        
                        # Get project name if available
                        if jobcode_id in projects_data:
                            project = projects_data[jobcode_id]
                            if project.get('name'):
                                tasks.append(project['name'])
                
                if not tasks:
                    tasks = clients  # Use jobcode names as tasks if no projects
                
                # Get date range
                dates = [t.get('date') for t in user_timesheet_data if t.get('date')]
                work_start_date = min(dates) if dates else None
                work_end_date = max(dates) if dates else None
                
                employee_summaries.append({
                    'employee_id': user_id,
                    'employee_name': user.get('username', 'Unknown'),
                    'full_name': user.get('display_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    'work_start_date': work_start_date,
                    'work_end_date': work_end_date,
                    'total_work_hours': total_hours,
                    'actual_work_days': days_worked,
                    'average_daily_hours': daily_average,
                    'client_list': clients,
                    'task_list': tasks,
                    'custom_field_values': []  # Skip custom fields for performance
                })
            
            return pd.DataFrame(employee_summaries)
            
        except Exception as e:
            st.error(f"Error fetching employee summary: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_summary(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get summary for specific employee (optimized with caching)
        
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
            # Get user data
            user_response = self.supabase.table('users').select('id, username, first_name, last_name, display_name').eq('id', user_id).execute()
            user_data = user_response.data
            
            if not user_data:
                return pd.DataFrame()
            
            user = user_data[0]
            
            # Get timesheet data (optimized query)
            timesheet_query = self.supabase.table('timesheets').select('duration, date, jobcode_id').eq('user_id', user_id)
            
            if start_date:
                timesheet_query = timesheet_query.gte('date', start_date)
            if end_date:
                timesheet_query = timesheet_query.lte('date', end_date)
            
            # Limit timesheet data for performance
            timesheet_query = timesheet_query.limit(5000)
            timesheets_response = timesheet_query.execute()
            timesheets_data = timesheets_response.data
            
            # Calculate summary metrics
            total_hours = sum(t.get('duration', 0) or 0 for t in timesheets_data) / 3600.0
            work_dates = list(set(t.get('date') for t in timesheets_data if t.get('date')))
            days_worked = len(work_dates)
            daily_average = total_hours / days_worked if days_worked > 0 else 0
            
            # Get jobcodes and projects (simplified)
            jobcode_ids = list(set(t.get('jobcode_id') for t in timesheets_data if t.get('jobcode_id')))
            
            clients = []
            tasks = []
            if jobcode_ids:
                # Use cached jobcodes data if available
                jobcodes_cache_key = f"jobcodes_{hash(tuple(jobcode_ids))}"
                jobcodes_data = self._get_from_cache(jobcodes_cache_key)
                
                if jobcodes_data is None:
                    jobcodes_response = self.supabase.table('jobcodes').select('id, name').in_('id', jobcode_ids).execute()
                    jobcodes_data = {j['id']: j for j in jobcodes_response.data}
                    self._set_cache(jobcodes_cache_key, jobcodes_data)
                
                for jobcode_id in jobcode_ids:
                    if jobcode_id in jobcodes_data:
                        jobcode = jobcodes_data[jobcode_id]
                        if jobcode.get('name'):
                            clients.append(jobcode['name'])
                
                tasks = clients  # Use jobcode names as tasks for simplicity
            
            # Get date range
            dates = [t.get('date') for t in timesheets_data if t.get('date')]
            work_start_date = min(dates) if dates else None
            work_end_date = max(dates) if dates else None
            
            result = pd.DataFrame([{
                'employee_id': user_id,
                'employee_name': user.get('username', 'Unknown'),
                'full_name': user.get('display_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                'work_start_date': work_start_date,
                'work_end_date': work_end_date,
                'total_work_hours': total_hours,
                'actual_work_days': days_worked,
                'average_daily_hours': daily_average,
                'client_list': clients,
                'task_list': tasks,
                'custom_field_values': []  # Skip for performance
            }])
            
            # Cache the result
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            st.error(f"Error fetching employee summary: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_daily_work(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get daily work breakdown for specific employee (optimized with caching)
        
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
            # Get timesheet data (optimized query)
            timesheet_query = self.supabase.table('timesheets').select('duration, date, jobcode_id').eq('user_id', user_id)
            
            if start_date:
                timesheet_query = timesheet_query.gte('date', start_date)
            if end_date:
                timesheet_query = timesheet_query.lte('date', end_date)
            
            # Limit timesheet data for performance
            timesheet_query = timesheet_query.limit(5000)
            timesheets_response = timesheet_query.execute()
            timesheets_data = timesheets_response.data
            
            if not timesheets_data:
                return pd.DataFrame()
            
            # Get jobcodes (use cache if available)
            jobcode_ids = list(set(t.get('jobcode_id') for t in timesheets_data if t.get('jobcode_id')))
            jobcodes_data = {}
            if jobcode_ids:
                jobcodes_cache_key = f"jobcodes_{hash(tuple(jobcode_ids))}"
                jobcodes_data = self._get_from_cache(jobcodes_cache_key)
                
                if jobcodes_data is None:
                    jobcodes_response = self.supabase.table('jobcodes').select('id, name, short_code').in_('id', jobcode_ids).execute()
                    jobcodes_data = {j['id']: j for j in jobcodes_response.data}
                    self._set_cache(jobcodes_cache_key, jobcodes_data)
            
            # Process timesheet data
            daily_work_data = []
            for timesheet in timesheets_data:
                jobcode_id = timesheet.get('jobcode_id')
                jobcode = jobcodes_data.get(jobcode_id, {})
                
                daily_work_data.append({
                    'work_date': timesheet.get('date'),
                    'client_name': jobcode.get('name', 'Unknown'),
                    'task_name': jobcode.get('name', 'Unknown'),  # Use jobcode name as task for simplicity
                    'hours_worked': (timesheet.get('duration', 0) or 0) / 3600.0,
                    'job_code': jobcode.get('short_code', ''),
                    'custom_field_items': []  # Skip for performance
                })
            
            result = pd.DataFrame(daily_work_data)
            
            # Cache the result
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            st.error(f"Error fetching daily work data: {str(e)}")
            return pd.DataFrame()
    
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
        if not self.supabase:
            return pd.DataFrame()
        
        try:
            # Get daily work data first
            daily_data = self.get_employee_daily_work(user_id, start_date, end_date)
            
            if daily_data.empty:
                return pd.DataFrame()
            
            # Group by week
            daily_data['work_date'] = pd.to_datetime(daily_data['work_date'])
            daily_data['work_week'] = daily_data['work_date'].dt.to_period('W').dt.start
            
            weekly_data = daily_data.groupby(['work_week', 'client_name', 'task_name', 'job_code']).agg({
                'hours_worked': 'sum',
                'custom_field_items': lambda x: list(set([item for sublist in x for item in sublist]))
            }).reset_index()
            
            weekly_data['work_week'] = weekly_data['work_week'].dt.date
            weekly_data = weekly_data.rename(columns={'work_week': 'work_week'})
            
            return weekly_data
            
        except Exception as e:
            st.error(f"Error fetching weekly work data: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_productivity_metrics(self, user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get productivity metrics for specific employee (optimized with caching)
        
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
            # Get employee summary (this will use its own cache)
            emp_summary = self.get_employee_summary(user_id, start_date, end_date)
            
            if emp_summary.empty:
                return pd.DataFrame()
            
            emp_data = emp_summary.iloc[0]
            total_hours = emp_data['total_work_hours']
            days_worked = emp_data['actual_work_days']
            daily_average = emp_data['average_daily_hours']
            
            # Calculate productivity metrics
            productivity_score = min(100, (daily_average / 8.0) * 100) if daily_average else 0
            utilization_percentage = (daily_average / 8.0) * 100 if daily_average else 0
            overtime_hours = max(0, daily_average - 8.0) * days_worked if daily_average else 0
            
            result = pd.DataFrame([{
                'employee_id': user_id,
                'employee_name': emp_data['employee_name'],
                'total_hours': total_hours,
                'days_worked': days_worked,
                'daily_average': daily_average,
                'productivity_score': productivity_score,
                'utilization_percentage': utilization_percentage,
                'overtime_hours': overtime_hours
            }])
            
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
        Get client distribution for specific employee
        
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
            # Get daily work data
            daily_data = self.get_employee_daily_work(user_id, start_date, end_date)
            
            if daily_data.empty:
                return pd.DataFrame()
            
            # Group by client
            client_dist = daily_data.groupby('client_name').agg({
                'hours_worked': 'sum'
            }).reset_index()
            
            total_hours = client_dist['hours_worked'].sum()
            
            client_dist['total_hours'] = client_dist['hours_worked']
            client_dist['billable_hours'] = client_dist['hours_worked']  # Assume all hours are billable
            client_dist['days_worked'] = daily_data.groupby('client_name')['work_date'].nunique().values
            client_dist['average_hours_per_day'] = client_dist['total_hours'] / client_dist['days_worked'].replace(0, 1)  # Avoid division by zero
            client_dist['percentage_of_total'] = (client_dist['total_hours'] / total_hours * 100) if total_hours > 0 else 0
            
            return client_dist[['client_name', 'total_hours', 'billable_hours', 'days_worked', 'average_hours_per_day', 'percentage_of_total']]
            
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
        Get employee KPIs for dashboard
        
        Args:
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            Dict: KPI metrics
        """
        try:
            # Get all employees summary
            all_employees = self.get_all_employees_summary(start_date, end_date)
            
            if all_employees.empty:
                return {
                    'total_employees': 0,
                    'avg_hours_per_employee': 0,
                    'avg_utilization': 0,
                    'team_productivity': 0,
                    'overtime_pct': 0
                }
            
            # Calculate KPIs
            total_employees = len(all_employees)
            total_hours = all_employees['total_work_hours'].sum() or 0
            avg_hours_per_employee = total_hours / max(1, total_employees)
            
            # Calculate average utilization (assuming 8 hours per day as standard)
            total_days_worked = all_employees['actual_work_days'].sum() or 0
            standard_hours = total_days_worked * 8  # 8 hours per day standard
            avg_utilization = (total_hours / max(1, standard_hours)) * 100 if standard_hours > 0 else 0
            
            # Calculate team productivity based on hours consistency
            daily_averages = all_employees[all_employees['average_daily_hours'] > 0]['average_daily_hours'].tolist()
            if daily_averages:
                productivity_scores = [min(100, (avg / 8) * 100) for avg in daily_averages if avg]
                team_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0
            else:
                team_productivity = 0
            
            # Calculate overtime percentage (hours over 8 per day)
            overtime_hours = sum(max(0, (avg or 0) - 8) * (days or 0) for avg, days in 
                               zip(all_employees['average_daily_hours'], all_employees['actual_work_days']))
            overtime_pct = (overtime_hours / max(1, total_hours)) * 100 if total_hours > 0 else 0
            
            return {
                'total_employees': total_employees,
                'avg_hours_per_employee': avg_hours_per_employee,
                'avg_utilization': avg_utilization,
                'team_productivity': team_productivity,
                'overtime_pct': overtime_pct
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
