"""
Real-time T-sheet API Data Handler
Handles all API calls to external timesheet system and processes real-time employee data
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional
import random

class TimesheetAPIHandler:
    """
    Handles real-time timesheet data from external API
    Implements all 4 functions specified in README requirements
    """
    
    def __init__(self, api_base_url: str = None, api_key: str = None):
        """
        Initialize API handler
        
        Args:
            api_base_url (str): Base URL for timesheet API
            api_key (str): API authentication key
        """
        self.api_base_url = api_base_url or "https://api.timesheet.ddmac.com"
        self.api_key = api_key or "demo_api_key_12345"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._cache = {}  # Simple caching for API responses
    
    def fetch_timesheet_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetch raw timesheet data from API
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            pd.DataFrame: Raw timesheet data with columns [employee, client, project, date, hours]
        """
        # For demo purposes, we'll use mock data
        # In production, this would make actual API calls
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        cache_key = f"timesheet_{start_date}_{end_date}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Mock API call - replace with actual requests.get()
            data = self._generate_mock_api_data(start_date, end_date)
            
            # In production:
            # response = requests.get(
            #     f"{self.api_base_url}/timesheet",
            #     headers=self.headers,
            #     params={"start_date": start_date, "end_date": end_date}
            # )
            # response.raise_for_status()
            # data = response.json()
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Cache the result
            self._cache[cache_key] = df
            
            return df
            
        except Exception as e:
            print(f"Error fetching timesheet data: {e}")
            return pd.DataFrame()
    
    def analyze_clients(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        README Function 1: Client Time Summary Analysis
        
        Returns:
            pd.DataFrame: Client, Total_Hours, Start_Date, End_Date, Weekly_Average_Hours
        """
        if data is None:
            data = self.fetch_timesheet_data()
        
        if data.empty:
            return pd.DataFrame(columns=['Client', 'Total_Hours', 'Start_Date', 'End_Date', 'Weekly_Average_Hours'])
        
        # Group by client and calculate metrics
        client_summary = data.groupby('client').agg({
            'hours': 'sum',
            'date': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        client_summary.columns = ['Total_Hours', 'Start_Date', 'End_Date']
        
        # Calculate weekly averages
        data_copy = data.copy()
        data_copy['week'] = data_copy['date'].dt.to_period('W')
        weekly_totals = data_copy.groupby(['client', 'week'])['hours'].sum().reset_index()
        weekly_avg = weekly_totals.groupby('client')['hours'].mean().round(2)
        
        client_summary['Weekly_Average_Hours'] = weekly_avg
        client_summary = client_summary.reset_index()
        client_summary.rename(columns={'client': 'Client'}, inplace=True)
        
        return client_summary
    
    def analyze_projects_for_client(self, client_name: str, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        README Function 2: Project Analysis for Specific Client
        
        Args:
            client_name (str): Name of the client to analyze
            
        Returns:
            pd.DataFrame: Project, Total_Hours, Start_Date, End_Date, Weekly_Average_Hours
        """
        if data is None:
            data = self.fetch_timesheet_data()
        
        client_data = data[data['client'] == client_name].copy()
        
        if client_data.empty:
            return pd.DataFrame(columns=['Project', 'Total_Hours', 'Start_Date', 'End_Date', 'Weekly_Average_Hours'])
        
        # Group by project and calculate metrics
        project_summary = client_data.groupby('project').agg({
            'hours': 'sum',
            'date': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        project_summary.columns = ['Total_Hours', 'Start_Date', 'End_Date']
        
        # Calculate weekly averages for projects
        client_data['week'] = client_data['date'].dt.to_period('W')
        weekly_totals = client_data.groupby(['project', 'week'])['hours'].sum().reset_index()
        weekly_avg = weekly_totals.groupby('project')['hours'].mean().round(2)
        
        project_summary['Weekly_Average_Hours'] = weekly_avg
        project_summary = project_summary.reset_index()
        project_summary.rename(columns={'project': 'Project'}, inplace=True)
        
        return project_summary
    
    def analyze_employees_overview(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        README Function 3A: Employee Overview Report
        
        Returns:
            pd.DataFrame: Employee, Start_Date, End_Date, Daily_Average_Hours, 
                         Total_Hours, Clients_List, Projects_List
        """
        if data is None:
            data = self.fetch_timesheet_data()
        
        if data.empty:
            return pd.DataFrame(columns=['Employee', 'Start_Date', 'End_Date', 'Daily_Average_Hours', 
                                       'Total_Hours', 'Clients_List', 'Projects_List'])
        
        # Group by employee for primary metrics
        employee_overview = data.groupby('employee').agg({
            'date': ['min', 'max'],
            'hours': 'sum',
            'client': lambda x: list(sorted(set(x))),
            'project': lambda x: list(sorted(set(x)))
        })
        
        # Flatten column names
        employee_overview.columns = ['Start_Date', 'End_Date', 'Total_Hours', 'Clients_List', 'Projects_List']
        
        # Calculate daily averages - ACTUAL working days, not date range (per README)
        for employee in employee_overview.index:
            emp_data = data[data['employee'] == employee]
            working_days = emp_data['date'].nunique()  # Count unique working days only
            total_hours = emp_data['hours'].sum()
            daily_avg = total_hours / working_days if working_days > 0 else 0
            employee_overview.loc[employee, 'Daily_Average_Hours'] = round(daily_avg, 2)
        
        # Format lists as strings for display
        employee_overview['Clients_List'] = employee_overview['Clients_List'].apply(
            lambda x: '[' + ', '.join(x) + ']'
        )
        employee_overview['Projects_List'] = employee_overview['Projects_List'].apply(
            lambda x: '[' + ', '.join(x) + ']'
        )
        
        employee_overview = employee_overview.reset_index()
        employee_overview.rename(columns={'employee': 'Employee'}, inplace=True)
        
        # Final column order as per README
        result = employee_overview[['Employee', 'Start_Date', 'End_Date', 'Daily_Average_Hours', 
                                  'Total_Hours', 'Clients_List', 'Projects_List']]
        
        return result
    
    def analyze_employee_detailed(self, employee_name: str = None, frequency: str = 'daily', 
                                 data: pd.DataFrame = None) -> pd.DataFrame:
        """
        README Function 3B: Employee Detailed Report
        
        Args:
            employee_name (str): Specific employee or None for all
            frequency (str): 'daily' or 'weekly' reporting granularity
            
        Returns:
            pd.DataFrame: Employee, Date/Week, Client, Project, Hours
            (Matches exactly the example table in README)
        """
        if data is None:
            data = self.fetch_timesheet_data()
        
        if data.empty:
            columns = ['Employee', 'Week', 'Client', 'Project', 'Hours'] if frequency == 'weekly' else ['Employee', 'Date', 'Client', 'Project', 'Hours']
            return pd.DataFrame(columns=columns)
        
        # Filter for specific employee if provided
        if employee_name:
            filtered_data = data[data['employee'] == employee_name].copy()
        else:
            filtered_data = data.copy()
                
        if filtered_data.empty:
            columns = ['Employee', 'Week', 'Client', 'Project', 'Hours'] if frequency == 'weekly' else ['Employee', 'Date', 'Client', 'Project', 'Hours']
            return pd.DataFrame(columns=columns)
        
        if frequency.lower() == 'weekly':
            # Weekly breakdown with separate rows for each project/client
            filtered_data['week'] = filtered_data['date'].dt.to_period('W')
            result = filtered_data.groupby(['employee', 'week', 'client', 'project'])['hours'].sum().reset_index()
            result['Week'] = result['week'].astype(str)
            result = result[['employee', 'Week', 'client', 'project', 'hours']]
            result.columns = ['Employee', 'Week', 'Client', 'Project', 'Hours']
        else:
            # Daily breakdown with separate rows for each project/client
            result = filtered_data.groupby(['employee', 'date', 'client', 'project'])['hours'].sum().reset_index()
            result['Date'] = result['date'].dt.strftime('%Y-%m-%d')
            result = result[['employee', 'Date', 'client', 'project', 'hours']]
            result.columns = ['Employee', 'Date', 'Client', 'Project', 'Hours']
        
        return result.round(2)
    
    def analyze_project_details(self, project_name: str, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        README Function 4: Project Details with User Lists
        
        Args:
            project_name (str): Project to analyze
            
        Returns:
            pd.DataFrame: Project, Start, End, ListUsers, Employee, Date, Hours, Daily_Total_For_Project
        """
        if data is None:
            data = self.fetch_timesheet_data()
        
        project_data = data[data['project'] == project_name].copy()
        
        if project_data.empty:
            return pd.DataFrame(columns=['Project', 'Start', 'End', 'ListUsers', 'Employee', 'Date', 'Hours', 'Daily_Total_For_Project'])
        
        # Get project summary
        start_date = project_data['date'].min()
        end_date = project_data['date'].max()
        users_list = sorted(project_data['employee'].unique())
        users_str = '[' + ', '.join(users_list) + ']'
        
        # Individual employee daily work
        daily_work = project_data.groupby(['employee', 'date'])['hours'].sum().reset_index()
        daily_work['Date'] = daily_work['date'].dt.strftime('%Y-%m-%d')
        
        # Calculate project daily totals (all employees)
        daily_totals = project_data.groupby('date')['hours'].sum().reset_index()
        daily_totals['Date'] = daily_totals['date'].dt.strftime('%Y-%m-%d')
        daily_totals = daily_totals.set_index('Date')['hours'].to_dict()
        
        # Add project metadata and daily totals
        daily_work['Project'] = project_name
        daily_work['Start'] = start_date.strftime('%Y-%m-%d')
        daily_work['End'] = end_date.strftime('%Y-%m-%d')
        daily_work['ListUsers'] = users_str
        daily_work['Daily_Total_For_Project'] = daily_work['Date'].map(daily_totals)
        
        result = daily_work[['Project', 'Start', 'End', 'ListUsers', 'employee', 'Date', 'hours', 'Daily_Total_For_Project']]
        result.columns = ['Project', 'Start', 'End', 'ListUsers', 'Employee', 'Date', 'Hours', 'Daily_Total_For_Project']
        
        return result.round(2)
    
    def analyze_all_projects(self, data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Get summary of all projects
        
        Returns:
            pd.DataFrame: Project, Start, End, ListUsers
        """
        if data is None:
            data = self.fetch_timesheet_data()
        
        if data.empty:
            return pd.DataFrame(columns=['Project', 'Start', 'End', 'ListUsers'])
        
        project_summary = data.groupby('project').agg({
            'date': ['min', 'max'],
            'employee': lambda x: list(sorted(set(x))),
            'hours': 'sum'
        })
        
        # Flatten column names
        project_summary.columns = ['Start', 'End', 'ListUsers', 'Total_Hours']
        
        # Format users list as requested in README
        project_summary['ListUsers'] = project_summary['ListUsers'].apply(lambda x: '[' + ', '.join(x) + ']')
        project_summary = project_summary.reset_index()
        
        # Reorder columns as shown in README
        result = project_summary[['project', 'Start', 'End', 'ListUsers']]
        result.columns = ['Project', 'Start', 'End', 'ListUsers']
        
        return result
    
    def fetch_client_time_summary(self, page: int = 1, limit: int = 10) -> dict:
        """
        Fetch client time summary data from the API endpoint
        
        Args:
            page (int): Page number for pagination
            limit (int): Number of records per page
            
        Returns:
            dict: API response with client time summary data
        """
        try:
            # Make actual API call to the real endpoint
            api_url = "http://127.0.0.1:8000/api/v1/client-time-summary"
            params = {
                "page": page,
                "limit": limit
            }
            
            response = requests.get(
                api_url,
                params=params,
                timeout=30  # 30 second timeout
            )
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Add pagination info if not present
            if 'total_pages' not in data:
                total = data.get('total', 0)
                data['total_pages'] = (total + limit - 1) // limit if total > 0 else 0
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            # Return fallback data structure
            return {
                "total": 0,
                "limit": limit,
                "offset": (page - 1) * limit,
                "page": page - 1,
                "total_pages": 0,
                "data": []
            }
        except Exception as e:
            print(f"Error fetching client time summary: {e}")
            return {"total": 0, "data": []}

    def fetch_client_user_data(self, jobcode_id: int, user_id: int = None, period: str = "daily", page: int = 1, limit: int = 10) -> dict:
        """
        Fetch detailed client user data from the API endpoint
        
        Args:
            jobcode_id (int): Job code ID for the client
            user_id (int): User ID for the specific user (optional)
            period (str): Time period for data (daily, weekly, monthly)
            page (int): Page number for pagination
            limit (int): Number of records per page
            
        Returns:
            dict: API response with user timesheet data for the jobcode
        """
        try:
            # Mock API response based on the provided structure
            mock_response = {
                "total": 2,
                "limit": limit,
                "offset": (page - 1) * limit,
                "page": page,
                "total_pages": 1,
                "data": [
                    {
                        "user_id": 745004,
                        "username": "hutchisona",
                        "jobcode_id": jobcode_id,
                        "total_duration": 16.1,
                        "start_date": "2020-01-03T07:01:00-05:00",
                        "end_date": "2020-02-24T16:20:00-05:00",
                        "days_worked": 4
                    },
                    {
                        "user_id": 745044,
                        "username": "caldwellj",
                        "jobcode_id": jobcode_id,
                        "total_duration": 8.35,
                        "start_date": "2020-01-06T07:15:00-05:00",
                        "end_date": "2020-02-24T16:00:00-05:00",
                        "days_worked": 2
                    }
                ]
            }
            
            # In production, this would be:
            # response = requests.get(
            #     f"{self.api_base_url}/api/v1/client-user-data/{jobcode_id}",
            #     headers=self.headers,
            #     params={"period": period, "page": page, "limit": limit, "user_id": user_id}
            # )
            # response.raise_for_status()
            # return response.json()
            
            return mock_response
            
        except Exception as e:
            print(f"Error fetching client user data: {e}")
            return {"total": 0, "data": []}

    def fetch_user_daily_data(self, jobcode_id: int, user_id: int, period: str = "daily", page: int = 1, limit: int = 10) -> dict:
        """
        Fetch detailed daily timesheet data for a specific user and jobcode
        
        Args:
            jobcode_id (int): Job code ID for the client
            user_id (int): User ID for the specific user
            period (str): Time period for data (daily, weekly, monthly)
            page (int): Page number for pagination
            limit (int): Number of records per page
            
        Returns:
            dict: API response with detailed daily timesheet data
        """
        try:
            # Mock API response for daily timesheet data
            mock_response = {
                "total": 15,
                "limit": limit,
                "offset": (page - 1) * limit,
                "page": page,
                "total_pages": 2,
                "data": [
                    {
                        "id": 1,
                        "user_id": user_id,
                        "jobcode_id": jobcode_id,
                        "date": "2020-01-03",
                        "start_time": "07:01:00",
                        "end_time": "15:30:00",
                        "duration": 8.5,
                        "description": "Project development work",
                        "status": "approved",
                        "created_at": "2020-01-03T07:01:00Z"
                    },
                    {
                        "id": 2,
                        "user_id": user_id,
                        "jobcode_id": jobcode_id,
                        "date": "2020-01-06",
                        "start_time": "08:15:00",
                        "end_time": "16:45:00",
                        "duration": 8.5,
                        "description": "Code review and testing",
                        "status": "approved",
                        "created_at": "2020-01-06T08:15:00Z"
                    },
                    {
                        "id": 3,
                        "user_id": user_id,
                        "jobcode_id": jobcode_id,
                        "date": "2020-01-10",
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "duration": 8.0,
                        "description": "Client meeting and documentation",
                        "status": "approved",
                        "created_at": "2020-01-10T09:00:00Z"
                    }
                ]
            }
            
            # In production, this would be:
            # response = requests.get(
            #     f"{self.api_base_url}/api/v1/client-user-data/{jobcode_id}",
            #     headers=self.headers,
            #     params={"period": period, "page": page, "limit": limit, "user_id": user_id}
            # )
            # response.raise_for_status()
            # return response.json()
            
            return mock_response
            
        except Exception as e:
            print(f"Error fetching user daily data: {e}")
            return {"total": 0, "data": []}

    def analyze_team_allocation(self, client_data: dict = None) -> pd.DataFrame:
        """
        Analyze team allocation from client time summary data
        
        Args:
            client_data (dict): Client time summary data from API
            
        Returns:
            pd.DataFrame: Team allocation analysis with client, hours, days, efficiency
        """
        if client_data is None:
            client_data = self.fetch_client_time_summary()
        
        if not client_data or not client_data.get('data'):
            return pd.DataFrame(columns=['Client', 'Total_Hours', 'Days_Worked', 'Avg_Hours_Per_Day', 'Efficiency_Score', 'Status'])
        
        allocation_data = []
        
        for item in client_data['data']:
            # Skip items with no duration or invalid data
            if item.get('total_duration') is None or item.get('total_duration') == 0:
                continue
                
            total_hours = item.get('total_duration', 0)
            days_worked = item.get('days_worked', 0)
            
            # Calculate average hours per day
            avg_hours_per_day = total_hours / days_worked if days_worked > 0 else 0
            
            # Calculate efficiency score (0-100)
            # Higher efficiency = more hours per day worked
            efficiency_score = min(100, (avg_hours_per_day / 8) * 100) if avg_hours_per_day > 0 else 0
            
            # Determine status based on efficiency
            if efficiency_score >= 80:
                status = "High Performance"
            elif efficiency_score >= 60:
                status = "Good Performance"
            elif efficiency_score >= 40:
                status = "Average Performance"
            else:
                status = "Low Performance"
            
            allocation_data.append({
                'Client': item.get('name', 'Unknown'),
                'Total_Hours': round(total_hours, 2),
                'Days_Worked': days_worked,
                'Avg_Hours_Per_Day': round(avg_hours_per_day, 2),
                'Efficiency_Score': round(efficiency_score, 1),
                'Status': status,
                'Jobcode_ID': item.get('jobcode_id', 0),
                'User_ID': 2521428  # Default user ID for demo
            })
        
        return pd.DataFrame(allocation_data)

    def get_sample_data(self) -> dict:
        """
        Get comprehensive sample data for demo purposes
        
        Returns:
            dict: Complete sample data structure with all analytics
        """
        # Get base timesheet data
        timesheet_df = self.fetch_timesheet_data()
        
        # Generate all analytics
        clients_analysis = self.analyze_clients(timesheet_df)
        employees_analysis = self.analyze_employees_overview(timesheet_df)
        projects_analysis = self.analyze_all_projects(timesheet_df)
        
        # Get client time summary data
        client_time_summary = self.fetch_client_time_summary()
        team_allocation = self.analyze_team_allocation(client_time_summary)
        
        # Extract key lists
        employees = timesheet_df['employee'].unique().tolist() if not timesheet_df.empty else ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
        clients = timesheet_df['client'].unique().tolist() if not timesheet_df.empty else ['TechCorp', 'StartupXYZ', 'Enterprise Inc', 'Innovation Labs']
        projects = timesheet_df['project'].unique().tolist() if not timesheet_df.empty else ['Website Redesign', 'Mobile App', 'Database Migration', 'API Development']
        
        # Calculate summary metrics
        total_hours = timesheet_df['hours'].sum() if not timesheet_df.empty else 1250.5
        total_employees = len(employees)
        total_projects = len(projects)
        total_clients = len(clients)
        
        # Calculate efficiency (demo metric)
        efficiency = min(85 + random.randint(0, 15), 100)  # 85-100% efficiency
        
        return {
            'timesheet_data': timesheet_df,
            'clients': clients,
            'employees': employees,
            'projects': projects,
            'clients_analysis': clients_analysis,
            'employees_analysis': employees_analysis,
            'projects_analysis': projects_analysis,
            'client_time_summary': client_time_summary,
            'team_allocation': team_allocation,
            'total_hours': total_hours,
            'total_employees': total_employees,
            'total_projects': total_projects,
            'total_clients': total_clients,
            'efficiency': efficiency,
            'revenue': total_hours * 85,  # $85/hour average
            'active_projects': max(1, total_projects - random.randint(0, 2))  # Most projects are active
        }

    def _generate_mock_api_data(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Generate mock API data for testing
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict]: Mock timesheet records
        """
        # Sample data pools
        employees = ['Naveen Kumar', 'Ritvik Singh', 'Sarah Johnson', 'Mike Chen', 'Lisa Wang', 'Alex Rodriguez']
        clients = ['Shlegel Construction', 'TechCorp Solutions', 'BuildCo Inc', 'DataSys Analytics', 'WebFlow Digital']
        
        # Projects mapped to clients
        client_projects = {
            'Shlegel Construction': ['Electrical Wiring', 'Pipe Installation', 'Safety Systems'],
            'TechCorp Solutions': ['Database Migration', 'API Development', 'Frontend Redesign'],
            'BuildCo Inc': ['Foundation Work', 'Roofing Project', 'Plumbing Systems'],
            'DataSys Analytics': ['Data Analytics', 'Report Migration', 'Dashboard Development'],
            'WebFlow Digital': ['Website Design', 'Mobile Development', 'QA Testing']
        }
        
        # Generate date range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        date_range = []
        current_date = start
        while current_date <= end:
            # Skip some weekends randomly (simulate real work patterns)
            if current_date.weekday() < 5 or random.random() < 0.2:  # Weekdays + some weekend work
                date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Generate data records
        data = []
        
        for employee in employees:
            # Each employee works on random clients
            employee_clients = random.sample(clients, k=random.randint(2, 4))
            
            # Generate random work days
            working_days = random.sample(date_range, k=random.randint(len(date_range)//3, int(len(date_range) * 0.8)))
            
            for date in working_days:
                # Employee might work on 1-3 projects in a day
                num_entries = random.randint(1, 3)
                
                for _ in range(num_entries):
                    client = random.choice(employee_clients)
                    project = random.choice(client_projects[client])
                    hours = round(random.uniform(1, 8), 1)  # 1-8 hours per entry
                    
                    data.append({
                        'employee': employee,
                        'client': client,
                        'project': project,
                        'date': date.strftime('%Y-%m-%d'),
                        'hours': hours
                    })
        
        # Sort by employee and date for consistency
        data.sort(key=lambda x: (x['employee'], x['date']))
        
        return data

# Convenience functions for easy import
def get_api_handler() -> TimesheetAPIHandler:
    """Get configured API handler instance"""
    return TimesheetAPIHandler()

def fetch_real_time_data(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Fetch real-time timesheet data"""
    handler = get_api_handler()
    return handler.fetch_timesheet_data(start_date, end_date)

def analyze_clients_api(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """README Function 1 using API data"""
    handler = get_api_handler()
    data = handler.fetch_timesheet_data(start_date, end_date)
    return handler.analyze_clients(data)

def analyze_projects_for_client_api(client_name: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """README Function 2 using API data"""
    handler = get_api_handler()
    data = handler.fetch_timesheet_data(start_date, end_date)
    return handler.analyze_projects_for_client(client_name, data)

def analyze_employees_overview_api(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """README Function 3A using API data"""
    handler = get_api_handler()
    data = handler.fetch_timesheet_data(start_date, end_date)
    return handler.analyze_employees_overview(data)

def analyze_employee_detailed_api(employee_name: str, frequency: str = 'daily', 
                                 start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """README Function 3B using API data"""
    handler = get_api_handler()
    data = handler.fetch_timesheet_data(start_date, end_date)
    return handler.analyze_employee_detailed(employee_name, frequency, data)

def analyze_project_details_api(project_name: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """README Function 4 using API data"""
    handler = get_api_handler()
    data = handler.fetch_timesheet_data(start_date, end_date)
    return handler.analyze_project_details(project_name, data)

def fetch_client_user_data_api(jobcode_id: int, user_id: int = None, period: str = "daily", page: int = 1, limit: int = 10) -> dict:
    """Fetch detailed client user data using API"""
    handler = get_api_handler()
    return handler.fetch_client_user_data(jobcode_id, user_id, period, page, limit)

def fetch_user_daily_data_api(jobcode_id: int, user_id: int, period: str = "daily", page: int = 1, limit: int = 10) -> dict:
    """Fetch detailed daily timesheet data for a specific user using API"""
    handler = get_api_handler()
    return handler.fetch_user_daily_data(jobcode_id, user_id, period, page, limit)
