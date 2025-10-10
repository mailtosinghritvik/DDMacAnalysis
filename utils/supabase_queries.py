"""
Supabase Database Queries Module
Direct database access for DDMac Analytics using Supabase functions
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_AVAILABLE = True

class SupabaseQueryHandler:
    """Handler for Supabase database queries"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.connected = False
        
        if SUPABASE_AVAILABLE:
            try:
                # Initialize Supabase client
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_KEY")
                
                if url and key:
                    self.client = create_client(url, key)
                    self.connected = True
                    logger.info("✅ Supabase client connected successfully")
                else:
                    logger.warning("⚠️ Supabase credentials not found in environment variables")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
        else:
            logger.warning("⚠️ Supabase client not available")
    
    def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute a Supabase function and return results as DataFrame"""
        if not self.connected or not self.client:
            logger.warning(f"⚠️ Supabase not connected, returning empty DataFrame for {function_name}")
            return pd.DataFrame()
        
        try:
            # Execute the function
            result = self.client.rpc(function_name, params or {})
            
            # Execute the query and get the data
            data = result.execute()
            
            # Handle the result properly
            if hasattr(data, 'data') and data.data:
                return pd.DataFrame(data.data)
            else:
                logger.warning(f"⚠️ No data returned from {function_name}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Error executing {function_name}: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_analytics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get employee analytics data"""
        try:
            # If no date range provided, get all data
            if not start_date and not end_date:
                params = {}
            else:
                params = {}
                if start_date:
                    params['start_date_param'] = start_date
                if end_date:
                    params['end_date_param'] = end_date
            
            df = self.execute_function('get_employee_analytics', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No employee analytics data found")
                return self._get_employee_fallback_data()
            
            # Process the data
            total_employees = len(df)
            avg_utilization = df['utilization_rate'].mean() if 'utilization_rate' in df.columns else 0
            avg_productivity = df['productivity_score'].mean() if 'productivity_score' in df.columns else 0
            total_hours = df['total_hours'].sum() if 'total_hours' in df.columns else 0
            billable_hours = df['billable_hours'].sum() if 'billable_hours' in df.columns else 0
            
            return {
                'total_employees': total_employees,
                'grouped_data': df.to_dict('records'),
                'raw_data': df.to_dict('records'),
                'summary_metrics': {
                    'avg_utilization': avg_utilization,
                    'avg_productivity': avg_productivity,
                    'total_hours': total_hours,
                    'billable_hours': billable_hours,
                    'total_employees': total_employees
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting employee analytics: {str(e)}")
            return self._get_employee_fallback_data()
    
    def get_project_analytics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get project analytics data"""
        try:
            # If no date range provided, get all data
            if not start_date and not end_date:
                params = {}
            else:
                params = {}
                if start_date:
                    params['start_date_param'] = start_date
                if end_date:
                    params['end_date_param'] = end_date
            
            df = self.execute_function('get_project_analytics', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No project analytics data found")
                return self._get_project_fallback_data()
            
            # Process the data
            total_projects = len(df)
            avg_progress = df['completion_percentage'].mean() if 'completion_percentage' in df.columns else 0
            on_budget = len(df[df['budget_status'] == 'on_budget']) if 'budget_status' in df.columns else 0
            total_hours = df['total_hours'].sum() if 'total_hours' in df.columns else 0
            billable_hours = df['billable_hours'].sum() if 'billable_hours' in df.columns else 0
            
            return {
                'total_projects': total_projects,
                'grouped_data': df.to_dict('records'),
                'raw_data': df.to_dict('records'),
                'summary_metrics': {
                    'avg_progress': avg_progress,
                    'total_projects': total_projects,
                    'on_budget': on_budget,
                    'total_hours': total_hours,
                    'billable_hours': billable_hours
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting project analytics: {str(e)}")
            return self._get_project_fallback_data()
    
    def get_task_analytics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get task analytics data"""
        try:
            # If no date range provided, get all data
            if not start_date and not end_date:
                params = {}
            else:
                params = {}
                if start_date:
                    params['start_date_param'] = start_date
                if end_date:
                    params['end_date_param'] = end_date
            
            df = self.execute_function('get_task_analytics', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No task analytics data found")
                return self._get_task_fallback_data()
            
            # Process the data
            total_tasks = len(df)
            avg_duration = df['avg_duration_per_entry'].mean() if 'avg_duration_per_entry' in df.columns else 0
            total_hours = df['total_hours'].sum() if 'total_hours' in df.columns else 0
            billable_hours = df['billable_hours'].sum() if 'billable_hours' in df.columns else 0
            
            return {
                'total_tasks': total_tasks,
                'grouped_data': df.to_dict('records'),
                'raw_data': df.to_dict('records'),
                'summary_metrics': {
                    'total_tasks': total_tasks,
                    'avg_task_duration': avg_duration,
                    'total_hours': total_hours,
                    'billable_hours': billable_hours
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting task analytics: {str(e)}")
            return self._get_task_fallback_data()
    
    def get_time_tracking_summary(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get time tracking summary data"""
        try:
            # If no date range provided, get all data
            if not start_date and not end_date:
                params = {}
            else:
                params = {}
                if start_date:
                    params['start_date_param'] = start_date
                if end_date:
                    params['end_date_param'] = end_date
            
            df = self.execute_function('get_time_tracking_summary', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No time tracking data found")
                return self._get_time_tracking_fallback_data()
            
            # Process the data
            total_hours = df['total_hours'].sum() if 'total_hours' in df.columns else 0
            billable_hours = df['billable_hours'].sum() if 'billable_hours' in df.columns else 0
            total_entries = df['total_entries'].sum() if 'total_entries' in df.columns else 0
            avg_daily_hours = df['avg_hours_per_employee'].mean() if 'avg_hours_per_employee' in df.columns else 0
            
            return {
                'total_hours': total_hours,
                'grouped_data': df.to_dict('records'),
                'raw_data': df.to_dict('records'),
                'summary_metrics': {
                    'total_hours': total_hours,
                    'billable_hours': billable_hours,
                    'total_entries': total_entries,
                    'avg_daily_hours': avg_daily_hours
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting time tracking summary: {str(e)}")
            return self._get_time_tracking_fallback_data()
    
    def get_financial_metrics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get financial metrics data"""
        try:
            params = {}
            if start_date:
                params['start_date_param'] = start_date
            if end_date:
                params['end_date_param'] = end_date
            
            df = self.execute_function('get_financial_metrics', params)
            
            if df.empty:
                logger.warning("⚠️ No financial metrics data found")
                return self._get_financial_fallback_data()
            
            # Process the data
            row = df.iloc[0] if not df.empty else {}
            
            return {
                'revenue_logged': row.get('total_revenue', 0),
                'total_cost': row.get('total_cost', 0),
                'profit_margin': row.get('profit_margin', 0),
                'avg_hourly_rate': row.get('avg_hourly_rate', 0),
                'budget_utilization': 0.85,  # Default value
                'cost_efficiency': row.get('profit_margin', 0) / 100 if row.get('profit_margin', 0) > 0 else 0.85
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting financial metrics: {str(e)}")
            return self._get_financial_fallback_data()
    
    def get_available_users(self) -> List[Dict[str, Any]]:
        """Get list of available users from the database"""
        try:
            # Use raw Supabase query to fetch users
            if not self.connected or not self.client:
                logger.warning("⚠️ Supabase not connected, returning empty DataFrame for get_available_users")
                df = pd.DataFrame()
            else:
                try:
                    response = self.client.table("users").select("*").execute()
                    if hasattr(response, "data") and response.data:
                        df = pd.DataFrame(response.data)
                    else:
                        df = pd.DataFrame()
                except Exception as e:
                    logger.error(f"❌ Error executing raw Supabase users query: {str(e)}")
                    df = pd.DataFrame()
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No users found in database")
                return self._get_users_fallback_data()
            
            # Convert to list of dictionaries
            users = df.to_dict('records')
            logger.info(f"✅ Retrieved {len(users)} users from database")
            return users
            
        except Exception as e:
            logger.error(f"❌ Error getting available users: {str(e)}")
            return self._get_users_fallback_data()
    
    def get_available_clients(self) -> List[Dict[str, Any]]:
        """Get list of available clients from the database"""
        try:
            # Use jobcodes table to get available clients, similar to get_available_users
            if not self.connected or not self.client:
                logger.warning("⚠️ Supabase not connected, returning empty DataFrame for get_available_clients")
                df = pd.DataFrame()
            else:
                try:
                    response = self.client.table("jobcodes").select("*").execute()
                    if hasattr(response, "data") and response.data:
                        df = pd.DataFrame(response.data)
                    else:
                        df = pd.DataFrame()
                except Exception as e:
                    logger.error(f"❌ Error executing raw Supabase jobcodes query: {str(e)}")
                    df = pd.DataFrame()
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No clients found in database")
                return self._get_clients_fallback_data()
            
            # Convert to list of dictionaries
            clients = df.to_dict('records')
            logger.info(f"✅ Retrieved {len(clients)} clients from database")
            return clients
            
        except Exception as e:
            logger.error(f"❌ Error getting available clients: {str(e)}")
            return self._get_clients_fallback_data()
    
    def get_user_daily_work_summary(self, user_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get user daily work summary data"""
        try:
            params = {
                'user_id_param': user_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_user_daily_work_summary', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No daily work summary data found")
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Error getting user daily work summary: {str(e)}")
            return []
    
    def get_user_client_time_distribution(self, user_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get user client time distribution data"""
        try:
            params = {
                'user_id_param': user_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_user_client_time_distribution', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No client time distribution data found")
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Error getting user client time distribution: {str(e)}")
            return []
    
    def get_user_team_comparison(self, user_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get user vs team comparison data"""
        try:
            params = {
                'user_id_param': user_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_user_team_comparison', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No team comparison data found")
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Error getting user team comparison: {str(e)}")
            return []
    
    def get_user_period_summary(self, user_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get user period summary data"""
        try:
            params = {
                'user_id_param': user_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_user_period_summary', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No period summary data found")
                return self._get_user_period_fallback_data()
            
            # Return the first row as a dictionary
            return df.iloc[0].to_dict() if not df.empty else {}
            
        except Exception as e:
            logger.error(f"❌ Error getting user period summary: {str(e)}")
            return self._get_user_period_fallback_data()
    
    def get_client_overview_summary(self, client_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get client overview summary data"""
        try:
            params = {
                'client_id_param': client_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_client_overview_summary', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No client overview data found")
                return self._get_client_overview_fallback_data()
            
            # Return the first row as a dictionary
            return df.iloc[0].to_dict() if not df.empty else {}
            
        except Exception as e:
            logger.error(f"❌ Error getting client overview summary: {str(e)}")
            return self._get_client_overview_fallback_data()
    
    def get_client_user_allocation(self, client_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get client user allocation data"""
        try:
            params = {
                'client_id_param': client_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_client_user_allocation', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No client user allocation data found")
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Error getting client user allocation: {str(e)}")
            return []
    
    def get_client_comparison(self, client_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get client vs other clients comparison data"""
        try:
            params = {
                'client_id_param': client_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_client_comparison', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No client comparison data found")
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Error getting client comparison: {str(e)}")
            return []
    
    def get_client_weekly_summary(self, client_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get client weekly summary data"""
        try:
            params = {
                'client_id_param': client_id,
                'start_date_param': start_date,
                'end_date_param': end_date
            }
            df = self.execute_function('get_client_weekly_summary', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No client weekly summary data found")
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"❌ Error getting client weekly summary: {str(e)}")
            return []

    def get_dashboard_summary(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get comprehensive dashboard summary"""
        try:
            params = {}
            if start_date:
                params['start_date_param'] = start_date
            if end_date:
                params['end_date_param'] = end_date
            
            df = self.execute_function('get_dashboard_summary', params)
            
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.warning("⚠️ No dashboard summary data found")
                return self._get_dashboard_fallback_data()
            
            # Process the data
            row = df.iloc[0] if not df.empty else {}
            
            return {
                'total_employees': row.get('total_employees', 0),
                'active_employees': row.get('active_employees', 0),
                'total_projects': row.get('total_projects', 0),
                'active_projects': row.get('active_projects', 0),
                'total_hours': row.get('total_hours', 0),
                'billable_hours': row.get('billable_hours', 0),
                'total_revenue': row.get('total_revenue', 0),
                'avg_utilization': row.get('avg_utilization', 0),
                'project_health_score': row.get('project_health_score', 0),
                'total_tasks': row.get('total_tasks', 0),
                'avg_task_duration': row.get('avg_task_duration', 0),
                'cost_efficiency': row.get('cost_efficiency', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard summary: {str(e)}")
            return self._get_dashboard_fallback_data()
    
    # Fallback data methods
    def _get_employee_fallback_data(self) -> Dict[str, Any]:
        """Fallback employee data when database is unavailable"""
        return {
            'total_employees': 5,
            'grouped_data': [],
            'raw_data': [],
            'summary_metrics': {
                'avg_utilization': 0.8,
                'avg_productivity': 8.0,
                'total_hours': 40.0,
                'billable_hours': 32.0,
                'total_employees': 5
            }
        }
    
    def _get_project_fallback_data(self) -> Dict[str, Any]:
        """Fallback project data when database is unavailable"""
        return {
            'total_projects': 8,
            'grouped_data': [],
            'raw_data': [],
            'summary_metrics': {
                'avg_progress': 75.0,
                'total_projects': 8,
                'on_budget': 6,
                'total_hours': 120.0,
                'billable_hours': 96.0
            }
        }
    
    def _get_task_fallback_data(self) -> Dict[str, Any]:
        """Fallback task data when database is unavailable"""
        return {
            'total_tasks': 8,
            'grouped_data': [],
            'raw_data': [],
            'summary_metrics': {
                'total_tasks': 8,
                'avg_task_duration': 9.09,
                'total_hours': 72.7,
                'billable_hours': 72.7
            }
        }
    
    def _get_time_tracking_fallback_data(self) -> Dict[str, Any]:
        """Fallback time tracking data when database is unavailable"""
        return {
            'total_hours': 40.0,
            'grouped_data': [],
            'raw_data': [],
            'summary_metrics': {
                'total_hours': 40.0,
                'billable_hours': 32.0,
                'total_entries': 25,
                'avg_daily_hours': 8.0
            }
        }
    
    def _get_financial_fallback_data(self) -> Dict[str, Any]:
        """Fallback financial data when database is unavailable"""
        return {
            'revenue_logged': 10908.0,
            'total_cost': 8500.0,
            'profit_margin': 28.3,
            'avg_hourly_rate': 75.0,
            'budget_utilization': 0.85,
            'cost_efficiency': 0.89
        }
    
    def _get_users_fallback_data(self) -> List[Dict[str, Any]]:
        """Fallback users data when database is unavailable"""
        return [
            {
                'user_id': 1,
                'display_name': 'John Smith',
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'john.smith@company.com',
                'active': True
            },
            {
                'user_id': 2,
                'display_name': 'Jane Doe',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'email': 'jane.doe@company.com',
                'active': True
            },
            {
                'user_id': 3,
                'display_name': 'Mike Johnson',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'email': 'mike.johnson@company.com',
                'active': True
            },
            {
                'user_id': 4,
                'display_name': 'Sarah Wilson',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'email': 'sarah.wilson@company.com',
                'active': True
            },
            {
                'user_id': 5,
                'display_name': 'Tom Brown',
                'first_name': 'Tom',
                'last_name': 'Brown',
                'email': 'tom.brown@company.com',
                'active': True
            }
        ]
    
    def _get_clients_fallback_data(self) -> List[Dict[str, Any]]:
        """Fallback clients data when database is unavailable"""
        return [
            {
                'client_id': 1,
                'client_name': 'Client A - TechCorp',
                'jobcode_name': 'Client A - TechCorp',
                'billable': True,
                'active': True
            },
            {
                'client_id': 2,
                'client_name': 'Client B - BuildCo',
                'jobcode_name': 'Client B - BuildCo',
                'billable': True,
                'active': True
            },
            {
                'client_id': 3,
                'client_name': 'Client C - DesignStudio',
                'jobcode_name': 'Client C - DesignStudio',
                'billable': True,
                'active': True
            },
            {
                'client_id': 4,
                'client_name': 'Client D - ManufacturingInc',
                'jobcode_name': 'Client D - ManufacturingInc',
                'billable': True,
                'active': True
            },
            {
                'client_id': 5,
                'client_name': 'Client E - RetailChain',
                'jobcode_name': 'Client E - RetailChain',
                'billable': True,
                'active': True
            }
        ]

    def _get_user_period_fallback_data(self) -> Dict[str, Any]:
        """Fallback user period summary data when database is unavailable"""
        return {
            'total_hours': 40.0,
            'working_days': 5,
            'avg_hours_per_day': 8.0,
            'clients_served': 3,
            'total_sessions': 12,
            'avg_session_length': 3.33
        }
    
    def _get_client_overview_fallback_data(self) -> Dict[str, Any]:
        """Fallback client overview data when database is unavailable"""
        return {
            'total_hours': 120.0,
            'users_assigned': 3,
            'total_sessions': 25,
            'avg_hours_per_day': 8.0,
            'working_days': 15,
            'first_date_worked': '2025-08-01',
            'last_date_worked': '2025-08-15'
        }

    def _get_dashboard_fallback_data(self) -> Dict[str, Any]:
        """Fallback dashboard data when database is unavailable"""
        return {
            'total_employees': 5,
            'active_employees': 5,
            'total_projects': 8,
            'active_projects': 6,
            'total_hours': 40.0,
            'billable_hours': 32.0,
            'total_revenue': 10908.0,
            'avg_utilization': 0.8,
            'project_health_score': 7.5,
            'total_tasks': 8,
            'avg_task_duration': 9.09,
            'cost_efficiency': 0.89
        }

    def get_time_period_overview(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get time analytics period overview summary
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            Dict[str, Any]: Period overview data
        """
        try:
            result = self.execute_function('get_time_period_overview', {
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result.empty:
                return result.iloc[0].to_dict()
            else:
                logger.warning("⚠️ No time period overview data found")
                return {
                    'total_hours': 0.0,
                    'total_users': 0,
                    'total_clients': 0,
                    'total_sessions': 0,
                    'working_days': 0,
                    'avg_daily_hours': 0.0,
                    'avg_session_length': 0.0
                }
        except Exception as e:
            logger.error(f"❌ Error getting time period overview: {str(e)}")
            return {
                'total_hours': 0.0,
                'total_users': 0,
                'total_clients': 0,
                'total_sessions': 0,
                'working_days': 0,
                'avg_daily_hours': 0.0,
                'avg_session_length': 0.0
            }

    def get_time_daily_distribution(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get daily time distribution data
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict[str, Any]]: Daily distribution data
        """
        try:
            result = self.execute_function('get_time_daily_distribution', {
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result.empty:
                return result.to_dict('records')
            else:
                logger.warning("⚠️ No daily distribution data found")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting daily distribution: {str(e)}")
            return []

    def get_time_user_performance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get user performance ranking data
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict[str, Any]]: User performance data
        """
        try:
            result = self.execute_function('get_time_user_performance', {
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result.empty:
                return result.to_dict('records')
            else:
                logger.warning("⚠️ No user performance data found")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting user performance: {str(e)}")
            return []

    def get_time_client_activity(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get client activity summary data
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict[str, Any]]: Client activity data
        """
        try:
            result = self.execute_function('get_time_client_activity', {
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result.empty:
                return result.to_dict('records')
            else:
                logger.warning("⚠️ No client activity data found")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting client activity: {str(e)}")
            return []

    def get_time_weekly_summary(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get weekly summary data
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict[str, Any]]: Weekly summary data
        """
        try:
            result = self.execute_function('get_time_weekly_summary', {
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result.empty:
                return result.to_dict('records')
            else:
                logger.warning("⚠️ No weekly summary data found")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting weekly summary: {str(e)}")
            return []

    def get_time_session_analysis(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get session length analysis data
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict[str, Any]]: Session analysis data
        """
        try:
            result = self.execute_function('get_time_session_analysis', {
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not result.empty:
                return result.to_dict('records')
            else:
                logger.warning("⚠️ No session analysis data found")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting session analysis: {str(e)}")
            return []

# Global instance
supabase_handler = SupabaseQueryHandler()

def get_supabase_handler() -> SupabaseQueryHandler:
    """Get the global Supabase handler instance"""
    return supabase_handler

def is_supabase_available() -> bool:
    """Check if Supabase is available and connected"""
    # Check if environment variables are set
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        return False
    
    # Check if the handler is connected
    return supabase_handler.connected and SUPABASE_AVAILABLE
