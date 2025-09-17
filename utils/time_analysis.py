"""
Time Tracking Analysis utilities for DDMac Analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

class TimeTrackingAnalyzer:
    """
    A comprehensive time tracking analyzer for employee work data.
    
    Expected data format:
    - employee/user: Employee name
    - client: Client name  
    - project: Project name
    - date: Work date (YYYY-MM-DD format)
    - hours: Hours worked
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the analyzer with time tracking data.
        
        Args:
            data (pd.DataFrame): DataFrame with columns: employee, client, project, date, hours
        """
        self.data = data.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare and validate the data for analysis."""
        # Ensure date column is datetime
        self.data['date'] = pd.to_datetime(self.data['date'])
        
        # Add week column for weekly analysis
        self.data['week'] = self.data['date'].dt.to_period('W')
        self.data['month'] = self.data['date'].dt.to_period('M')
        
        # Ensure hours is numeric
        self.data['hours'] = pd.to_numeric(self.data['hours'], errors='coerce').fillna(0)
        
        # Sort by date
        self.data = self.data.sort_values('date')
    
    def get_client_summary(self) -> pd.DataFrame:
        """
        Function 1: Client Summary Report
        
        Returns a summary of all clients with total time spent, date ranges, and weekly averages.
        
        Returns:
            pd.DataFrame: Columns - Client, Total_Hours, Start_Date, End_Date, Weekly_Average_Hours
        """
        client_summary = self.data.groupby('client').agg({
            'hours': 'sum',
            'date': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        client_summary.columns = ['Total_Hours', 'Start_Date', 'End_Date']
        
        # Calculate weekly averages
        weekly_totals = self.data.groupby(['client', 'week'])['hours'].sum().reset_index()
        weekly_avg = weekly_totals.groupby('client')['hours'].mean().round(2)
        
        client_summary['Weekly_Average_Hours'] = weekly_avg
        client_summary = client_summary.reset_index()
        
        # Rename the column to match expected naming convention
        client_summary = client_summary.rename(columns={'client': 'Client'})
        
        return client_summary
    
    def get_project_summary(self, client_name: str) -> pd.DataFrame:
        """
        Function 2: Project Summary Report for a specific client
        
        Args:
            client_name (str): Name of the client to analyze
            
        Returns:
            pd.DataFrame: Columns - Project, Total_Hours, Start_Date, End_Date, Weekly_Average_Hours
        """
        client_data = self.data[self.data['client'] == client_name]
        
        if client_data.empty:
            return pd.DataFrame(columns=['Project', 'Total_Hours', 'Start_Date', 'End_Date', 'Weekly_Average_Hours'])
        
        project_summary = client_data.groupby('project').agg({
            'hours': 'sum',
            'date': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        project_summary.columns = ['Total_Hours', 'Start_Date', 'End_Date']
        
        # Calculate weekly averages for projects
        weekly_totals = client_data.groupby(['project', 'week'])['hours'].sum().reset_index()
        weekly_avg = weekly_totals.groupby('project')['hours'].mean().round(2)
        
        project_summary['Weekly_Average_Hours'] = weekly_avg
        project_summary = project_summary.reset_index()
        
        return project_summary
    
    def get_employee_overview(self) -> pd.DataFrame:
        """
        Function 3A: Employee Overview Report
        
        Returns overview of each employee with proper daily average calculation.
        IMPORTANT: Daily average = Total Hours / Number of actual working days (not date range)
        
        Returns:
            pd.DataFrame: Columns - Employee, Start_Date, End_Date, Daily_Average_Hours, Clients_List, Projects_List
        """
        employee_overview = self.data.groupby('employee').agg({
            'date': ['min', 'max'],
            'hours': 'sum',
            'client': lambda x: list(sorted(set(x))),
            'project': lambda x: list(sorted(set(x)))
        })
        
        # Flatten column names
        employee_overview.columns = ['Start_Date', 'End_Date', 'Total_Hours', 'Clients_List', 'Projects_List']
        
        # Calculate daily averages - ACTUAL working days, not date range
        for employee in employee_overview.index:
            emp_data = self.data[self.data['employee'] == employee]
            working_days = emp_data['date'].nunique()  # Count unique working days only
            total_hours = emp_data['hours'].sum()
            daily_avg = total_hours / working_days if working_days > 0 else 0
            employee_overview.loc[employee, 'Daily_Average_Hours'] = round(daily_avg, 2)
        
        employee_overview = employee_overview.reset_index()
        
        # Rename columns to match expected naming convention
        employee_overview = employee_overview.rename(columns={'employee': 'Employee'})
        
        # Reorder columns as specified: user, start, end, daily average, list of clients, list of projects
        employee_overview = employee_overview[['Employee', 'Start_Date', 'End_Date', 'Total_Hours', 'Daily_Average_Hours', 'Clients_List', 'Projects_List']]
        
        return employee_overview
    
    def get_employee_detailed_report(self, employee_name: str = None, frequency: str = 'daily') -> pd.DataFrame:
        """
        Function 3B: Employee Detailed Time Report
        
        Args:
            employee_name (str): Specific employee name or None for all employees
            frequency (str): 'daily' or 'weekly' - the granularity of the report
            
        Returns:
            pd.DataFrame: Individual rows for each client/project combination per day/week
                Format: Employee, Date/Week, Client, Project, Hours
        """
        # Filter data for specific employee if provided
        if employee_name:
            filtered_data = self.data[self.data['employee'] == employee_name].copy()
        else:
            filtered_data = self.data.copy()
            
        if filtered_data.empty:
            columns = ['Employee', 'Week', 'Client', 'Project', 'Hours'] if frequency == 'weekly' else ['Employee', 'Date', 'Client', 'Project', 'Hours']
            return pd.DataFrame(columns=columns)
        
        if frequency.lower() == 'weekly':
            # Weekly breakdown - separate row for each client/project combination
            result = filtered_data.groupby(['employee', 'week', 'client', 'project'])['hours'].sum().reset_index()
            result['Week'] = result['week'].astype(str)
            result = result[['employee', 'Week', 'client', 'project', 'hours']]
            result.columns = ['Employee', 'Week', 'Client', 'Project', 'Hours']
        else:
            # Daily breakdown - separate row for each client/project combination  
            result = filtered_data.groupby(['employee', 'date', 'client', 'project'])['hours'].sum().reset_index()
            result['Date'] = result['date'].dt.strftime('%Y-%m-%d')
            result = result[['employee', 'Date', 'client', 'project', 'hours']]
            result.columns = ['Employee', 'Date', 'Client', 'Project', 'Hours']
        
        return result.round(2)
    
    def get_all_projects_summary(self) -> pd.DataFrame:
        """
        Function 4: Complete Project Summary
        
        Returns comprehensive project summary as requested in the README.
        
        Returns:
            pd.DataFrame: Columns - Project, Start, End, ListUsers
        """
        project_summary = self.data.groupby('project').agg({
            'date': ['min', 'max'],
            'employee': lambda x: list(sorted(set(x))),
            'hours': 'sum'
        })
        
        # Flatten column names
        project_summary.columns = ['Start', 'End', 'ListUsers', 'Total_Hours']
        
        project_summary = project_summary.reset_index()
        
        # Reorder columns as requested: Project, Start, End, ListUsers
        result = project_summary[['project', 'Start', 'End', 'ListUsers']]
        result.columns = ['Project', 'Start', 'End', 'ListUsers']
        
        return result
    
    def get_project_health_metrics(self) -> pd.DataFrame:
        """
        Calculate project health metrics for predictive analytics
        """
        project_metrics = []
        
        for project in self.data['project'].unique():
            proj_data = self.data[self.data['project'] == project]
            
            # Basic metrics
            total_hours = proj_data['hours'].sum()
            total_days = (proj_data['date'].max() - proj_data['date'].min()).days + 1
            active_days = proj_data['date'].nunique()
            team_size = proj_data['employee'].nunique()
            
            # Velocity metrics
            weekly_hours = proj_data.groupby('week')['hours'].sum()
            avg_weekly_hours = weekly_hours.mean()
            hours_variance = weekly_hours.var()
            
            # Team metrics
            employee_hours = proj_data.groupby('employee')['hours'].sum()
            workload_balance = employee_hours.std() / employee_hours.mean() if employee_hours.mean() > 0 else 0
            
            # Health score (0-100)
            consistency_score = max(0, 100 - (hours_variance / avg_weekly_hours * 10)) if avg_weekly_hours > 0 else 0
            balance_score = max(0, 100 - (workload_balance * 50))
            activity_score = (active_days / total_days) * 100 if total_days > 0 else 0
            
            health_score = (consistency_score + balance_score + activity_score) / 3
            
            project_metrics.append({
                'Project': project,
                'Total_Hours': total_hours,
                'Team_Size': team_size,
                'Active_Days': active_days,
                'Avg_Weekly_Hours': round(avg_weekly_hours, 2),
                'Workload_Balance': round(workload_balance, 2),
                'Health_Score': round(health_score, 2),
                'Status': 'Healthy' if health_score > 70 else 'At Risk' if health_score > 40 else 'Critical'
            })
        
        return pd.DataFrame(project_metrics)
    
    def get_employee_performance_metrics(self) -> pd.DataFrame:
        """
        Calculate employee performance metrics
        """
        employee_metrics = []
        
        for employee in self.data['employee'].unique():
            emp_data = self.data[self.data['employee'] == employee]
            
            # Basic metrics
            total_hours = emp_data['hours'].sum()
            total_projects = emp_data['project'].nunique()
            total_clients = emp_data['client'].nunique()
            working_days = emp_data['date'].nunique()
            
            # Performance metrics
            daily_avg = total_hours / working_days if working_days > 0 else 0
            weekly_hours = emp_data.groupby('week')['hours'].sum()
            consistency = 100 - (weekly_hours.std() / weekly_hours.mean() * 10) if weekly_hours.mean() > 0 else 0
            
            # Utilization (assuming 8 hours per day target)
            utilization = (daily_avg / 8) * 100 if daily_avg > 0 else 0
            
            employee_metrics.append({
                'Employee': employee,
                'Total_Hours': total_hours,
                'Projects_Count': total_projects,
                'Clients_Count': total_clients,
                'Working_Days': working_days,
                'Daily_Average': round(daily_avg, 2),
                'Utilization_%': round(min(utilization, 100), 1),
                'Consistency_Score': round(max(0, consistency), 1)
            })
        
        return pd.DataFrame(employee_metrics)
    
    def calculate_project_health(self) -> dict:
        """
        Calculate health scores for all projects.
        
        Returns:
            dict: Project name -> health score (0.0 to 1.0)
        """
        health_scores = {}
        
        for project in self.data['project'].unique():
            project_data = self.data[self.data['project'] == project]
            
            # Calculate various health metrics
            total_hours = project_data['hours'].sum()
            days_active = project_data['date'].nunique()
            employees_involved = project_data['employee'].nunique()
            
            # Health factors
            consistency = 1.0 - (project_data.groupby('date')['hours'].sum().std() / 
                               project_data.groupby('date')['hours'].sum().mean()) if total_hours > 0 else 0
            consistency = max(0, min(1, consistency))
            
            activity_level = min(total_hours / 100, 1.0)  # Normalize to 0-1
            team_engagement = min(employees_involved / 3, 1.0)  # Normalize to 0-1
            
            # Overall health score
            health_score = (consistency * 0.4 + activity_level * 0.3 + team_engagement * 0.3)
            health_scores[project] = round(health_score, 2)
        
        return health_scores
    
    def calculate_employee_performance(self) -> dict:
        """
        Calculate performance scores for all employees.
        
        Returns:
            dict: Employee name -> performance score (0.0 to 1.0)
        """
        performance_scores = {}
        
        for employee in self.data['employee'].unique():
            emp_data = self.data[self.data['employee'] == employee]
            
            # Calculate performance metrics
            total_hours = emp_data['hours'].sum()
            working_days = emp_data['date'].nunique()
            daily_avg = total_hours / working_days if working_days > 0 else 0
            
            # Performance factors
            utilization = min(daily_avg / 8, 1.0)  # Normalize to 8 hours per day
            consistency = 1.0 - (emp_data.groupby('date')['hours'].sum().std() / 
                                emp_data.groupby('date')['hours'].sum().mean()) if total_hours > 0 else 0
            consistency = max(0, min(1, consistency))
            
            project_diversity = min(emp_data['project'].nunique() / 5, 1.0)  # Normalize to 5 projects
            
            # Overall performance score
            performance_score = (utilization * 0.5 + consistency * 0.3 + project_diversity * 0.2)
            performance_scores[employee] = round(performance_score, 2)
        
        return performance_scores

# Convenience functions for easy import and usage
def analyze_clients(data: pd.DataFrame) -> pd.DataFrame:
    """Quick function to get client summary."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_client_summary()

def analyze_projects_for_client(data: pd.DataFrame, client_name: str) -> pd.DataFrame:
    """Quick function to get project summary for a specific client."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_project_summary(client_name)

def analyze_employees_overview(data: pd.DataFrame) -> pd.DataFrame:
    """Quick function to get employee overview with proper daily averages."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_employee_overview()

def analyze_employee_detailed(data: pd.DataFrame, employee_name: str = None, frequency: str = 'daily') -> pd.DataFrame:
    """Quick function to get detailed employee work breakdown."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_employee_detailed_report(employee_name, frequency)

def analyze_all_projects(data: pd.DataFrame) -> pd.DataFrame:
    """Quick function to get all projects summary."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_all_projects_summary()

def get_project_health_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Quick function to get project health metrics."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_project_health_metrics()

def get_employee_performance_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Quick function to get employee performance metrics."""
    analyzer = TimeTrackingAnalyzer(data)
    return analyzer.get_employee_performance_metrics()

def generate_sample_timesheet_data(num_employees: int = 5, num_days: int = 60) -> pd.DataFrame:
    """
    Generate sample timesheet data for testing the time tracking analyzer.
    """
    import random
    
    # Sample data
    employees = ['Naveen Kumar', 'Ritvik Singh', 'Sarah Chen', 'Mike Johnson', 'Lisa Wang'][:num_employees]
    clients = ['Shlegel Construction', 'TechCorp Solutions', 'BuildCo Inc', 'DataSys Analytics', 'WebFlow Digital']
    
    # Projects mapped to clients
    client_projects = {
        'Shlegel Construction': ['Electrical Wiring', 'Plumbing Systems', 'HVAC Installation'],
        'TechCorp Solutions': ['Database Migration', 'API Development', 'Frontend Redesign'],
        'BuildCo Inc': ['Foundation Work', 'Roofing Project', 'Interior Design'],
        'DataSys Analytics': ['Data Analytics Platform', 'Report Migration', 'Dashboard Development'],
        'WebFlow Digital': ['Website Design', 'E-commerce Development', 'Mobile App Testing']
    }
    
    # Generate date range (excluding some weekends randomly to simulate real work)
    start_date = datetime.now() - timedelta(days=num_days)
    date_range = []
    
    current_date = start_date
    while current_date <= datetime.now():
        # Skip some weekends randomly (simulate real work patterns)
        if current_date.weekday() < 5 or random.random() < 0.2:  # Weekdays + some weekend work
            date_range.append(current_date)
        current_date += timedelta(days=1)
    
    data = []
    
    for employee in employees:
        # Each employee works on random selection of clients/projects
        employee_clients = random.sample(clients, k=random.randint(2, 4))
        
        # Generate work entries for this employee
        working_days = random.sample(date_range, k=random.randint(len(date_range)//3, int(len(date_range) * 0.8)))
        
        for date in working_days:
            # Employee might work on 1-3 different projects in a day
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
    
    df = pd.DataFrame(data)
    
    # Sort by employee and date for better readability
    df = df.sort_values(['employee', 'date']).reset_index(drop=True)
    
    return df
