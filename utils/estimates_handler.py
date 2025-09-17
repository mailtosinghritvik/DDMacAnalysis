"""
Excel Estimates Handler
Handles Excel file uploads, processes estimates, and integrates with Supabase
"""

import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
from supabase import create_client, Client

class EstimatesHandler:
    """
    Handles Excel-based project estimates and integrates with Supabase
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize estimates handler with Supabase connection
        
        Args:
            supabase_url (str): Supabase project URL
            supabase_key (str): Supabase API key
        """
        self.supabase_url = supabase_url or "https://your-project.supabase.co"
        self.supabase_key = supabase_key or "your-supabase-anon-key"
        
        # Initialize Supabase client (demo mode for now)
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        except Exception as e:
            print(f"Supabase connection failed (demo mode): {e}")
            self.supabase = None
    
    def process_excel_estimates(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Process uploaded Excel file and extract estimates
        
        Args:
            file_content (bytes): Excel file content
            filename (str): Original filename
            
        Returns:
            pd.DataFrame: Processed estimates data
        """
        try:
            # Read Excel file
            excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            
            # Process different sheets if they exist
            estimates_df = self._extract_estimates_from_excel(excel_data)
            
            # Save to Supabase
            if self.supabase:
                self._save_estimates_to_supabase(estimates_df, filename)
            
            return estimates_df
            
        except Exception as e:
            print(f"Error processing Excel file: {e}")
            return self._generate_mock_estimates_data()
    
    def _extract_estimates_from_excel(self, excel_data: Dict) -> pd.DataFrame:
        """
        Extract estimates from Excel sheets
        
        Expected Excel structure:
        Sheet 1: Project Estimates
        - Client Name
        - Project/Task Name
        - Estimated Hours
        - Estimated Cost
        - Start Date
        - End Date
        - Priority
        """
        estimates = []
        
        # Try to find the main estimates sheet
        main_sheet = None
        for sheet_name, sheet_data in excel_data.items():
            if any(keyword in sheet_name.lower() for keyword in ['estimate', 'project', 'budget']):
                main_sheet = sheet_data
                break
        
        if main_sheet is None:
            # Use first sheet if no specific sheet found
            main_sheet = list(excel_data.values())[0]
        
        # Expected columns (flexible column name matching)
        column_mapping = {
            'client': ['client', 'client name', 'customer', 'company'],
            'project': ['project', 'task', 'project name', 'task name', 'job'],
            'estimated_hours': ['estimated hours', 'hours', 'time estimate', 'planned hours'],
            'estimated_cost': ['estimated cost', 'cost', 'budget', 'price', 'amount'],
            'start_date': ['start date', 'start', 'begin date', 'project start'],
            'end_date': ['end date', 'end', 'finish date', 'project end'],
            'priority': ['priority', 'importance', 'urgency']
        }
        
        # Normalize column names
        main_sheet.columns = main_sheet.columns.str.lower().str.strip()
        
        # Map columns to expected names
        column_map = {}
        for target_col, possible_names in column_mapping.items():
            for col in main_sheet.columns:
                if any(name in col for name in possible_names):
                    column_map[col] = target_col
                    break
        
        # Rename columns
        main_sheet = main_sheet.rename(columns=column_map)
        
        # Fill missing columns with defaults
        required_columns = ['client', 'project', 'estimated_hours', 'estimated_cost', 'start_date', 'end_date']
        for col in required_columns:
            if col not in main_sheet.columns:
                if col == 'estimated_hours':
                    main_sheet[col] = 40  # Default 40 hours
                elif col == 'estimated_cost':
                    main_sheet[col] = main_sheet.get('estimated_hours', 40) * 125  # $125/hour
                elif col in ['start_date', 'end_date']:
                    main_sheet[col] = datetime.now()
                else:
                    main_sheet[col] = 'Unknown'
        
        # Clean and validate data
        main_sheet = main_sheet.dropna(subset=['client', 'project'])
        main_sheet['estimated_hours'] = pd.to_numeric(main_sheet['estimated_hours'], errors='coerce').fillna(0)
        main_sheet['estimated_cost'] = pd.to_numeric(main_sheet['estimated_cost'], errors='coerce').fillna(0)
        
        # Convert dates
        for date_col in ['start_date', 'end_date']:
            main_sheet[date_col] = pd.to_datetime(main_sheet[date_col], errors='coerce').fillna(datetime.now())
        
        # Add metadata
        main_sheet['upload_date'] = datetime.now()
        main_sheet['status'] = 'Active'
        main_sheet['progress_percentage'] = 0.0
        
        return main_sheet
    
    def _save_estimates_to_supabase(self, estimates_df: pd.DataFrame, filename: str):
        """
        Save estimates to Supabase database
        
        Args:
            estimates_df (pd.DataFrame): Estimates data
            filename (str): Original filename
        """
        if not self.supabase:
            print("Supabase not connected - estimates saved locally only")
            return
        
        try:
            # Convert DataFrame to records
            records = estimates_df.to_dict('records')
            
            # Add filename to each record
            for record in records:
                record['source_file'] = filename
                # Convert datetime objects to strings
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.isoformat()
            
            # Insert into Supabase
            result = self.supabase.table('project_estimates').insert(records).execute()
            print(f"Saved {len(records)} estimates to Supabase")
            
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
    
    def get_estimates_for_client(self, client_name: str) -> pd.DataFrame:
        """
        Get all estimates for a specific client
        
        Args:
            client_name (str): Client name
            
        Returns:
            pd.DataFrame: Client estimates
        """
        if self.supabase:
            try:
                result = self.supabase.table('project_estimates').select("*").eq('client', client_name).execute()
                return pd.DataFrame(result.data)
            except Exception as e:
                print(f"Error fetching estimates from Supabase: {e}")
        
        # Return mock data if Supabase unavailable
        return self._generate_mock_estimates_data().query(f"client == '{client_name}'")
    
    def get_estimates_for_project(self, project_name: str) -> pd.DataFrame:
        """
        Get estimates for a specific project
        
        Args:
            project_name (str): Project name
            
        Returns:
            pd.DataFrame: Project estimates
        """
        if self.supabase:
            try:
                result = self.supabase.table('project_estimates').select("*").eq('project', project_name).execute()
                return pd.DataFrame(result.data)
            except Exception as e:
                print(f"Error fetching estimates from Supabase: {e}")
        
        # Return mock data if Supabase unavailable
        return self._generate_mock_estimates_data().query(f"project == '{project_name}'")
    
    def get_all_estimates(self) -> pd.DataFrame:
        """
        Get all estimates from database
        
        Returns:
            pd.DataFrame: All estimates
        """
        if self.supabase:
            try:
                result = self.supabase.table('project_estimates').select("*").execute()
                return pd.DataFrame(result.data)
            except Exception as e:
                print(f"Error fetching estimates from Supabase: {e}")
        
        # Return mock data if Supabase unavailable
        return self._generate_mock_estimates_data()
    
    def calculate_progress_vs_estimates(self, actual_data: pd.DataFrame, estimates_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Calculate progress against estimates for progress bars
        
        Args:
            actual_data (pd.DataFrame): Actual timesheet data
            estimates_data (pd.DataFrame): Estimates data (optional)
            
        Returns:
            pd.DataFrame: Progress vs estimates comparison
        """
        if estimates_data is None:
            estimates_data = self.get_all_estimates()
        
        if estimates_data.empty or actual_data.empty:
            return pd.DataFrame()
        
        # Group actual data by client and project
        actual_summary = actual_data.groupby(['client', 'project']).agg({
            'hours': 'sum',
            'date': ['min', 'max']
        }).round(2)
        
        actual_summary.columns = ['Actual_Hours', 'Actual_Start', 'Actual_End']
        actual_summary = actual_summary.reset_index()
        
        # Merge with estimates
        progress_comparison = estimates_data.merge(
            actual_summary,
            on=['client', 'project'],
            how='left'
        )
        
        # Fill NaN values for projects not started
        progress_comparison['Actual_Hours'] = progress_comparison['Actual_Hours'].fillna(0)
        
        # Calculate progress metrics
        progress_comparison['Hours_Progress_%'] = (
            progress_comparison['Actual_Hours'] / 
            progress_comparison['estimated_hours'].replace(0, 1) * 100
        ).round(1)
        
        progress_comparison['Cost_Progress_%'] = (
            (progress_comparison['Actual_Hours'] * 125) /  # Assume $125/hour
            progress_comparison['estimated_cost'].replace(0, 1) * 100
        ).round(1)
        
        # Calculate variance
        progress_comparison['Hours_Variance'] = (
            progress_comparison['Actual_Hours'] - progress_comparison['estimated_hours']
        ).round(1)
        
        progress_comparison['Cost_Variance'] = (
            (progress_comparison['Actual_Hours'] * 125) - progress_comparison['estimated_cost']
        ).round(2)
        
        # Status based on progress
        def get_status(row):
            hours_progress = row['Hours_Progress_%']
            if hours_progress == 0:
                return 'Not Started'
            elif hours_progress < 50:
                return 'In Progress'
            elif hours_progress < 100:
                return 'Nearing Completion'
            elif hours_progress <= 110:
                return 'Completed'
            else:
                return 'Over Budget'
        
        progress_comparison['Project_Status'] = progress_comparison.apply(get_status, axis=1)
        
        return progress_comparison
    
    def get_budget_alerts(self, progress_data: pd.DataFrame = None) -> List[Dict]:
        """
        Get budget alerts for projects exceeding estimates
        
        Args:
            progress_data (pd.DataFrame): Progress comparison data
            
        Returns:
            List[Dict]: Budget alerts
        """
        if progress_data is None:
            # Get progress data with mock actual data
            mock_actual = self._generate_mock_actual_data()
            progress_data = self.calculate_progress_vs_estimates(mock_actual)
        
        alerts = []
        
        # Over budget alerts (>100% of estimate)
        over_budget = progress_data[progress_data['Hours_Progress_%'] > 100]
        for _, row in over_budget.iterrows():
            alerts.append({
                'type': 'over_budget',
                'severity': 'high' if row['Hours_Progress_%'] > 120 else 'medium',
                'client': row['client'],
                'project': row['project'],
                'estimated_hours': row['estimated_hours'],
                'actual_hours': row['Actual_Hours'],
                'progress_pct': row['Hours_Progress_%'],
                'message': f"{row['project']} is {row['Hours_Progress_%']:.1f}% over budget"
            })
        
        # At risk alerts (80-100% of estimate)
        at_risk = progress_data[
            (progress_data['Hours_Progress_%'] >= 80) & 
            (progress_data['Hours_Progress_%'] <= 100)
        ]
        for _, row in at_risk.iterrows():
            alerts.append({
                'type': 'at_risk',
                'severity': 'medium',
                'client': row['client'],
                'project': row['project'],
                'estimated_hours': row['estimated_hours'],
                'actual_hours': row['Actual_Hours'],
                'progress_pct': row['Hours_Progress_%'],
                'message': f"{row['project']} is approaching budget limit ({row['Hours_Progress_%']:.1f}%)"
            })
        
        return alerts
    
    def get_sample_data(self) -> dict:
        """
        Get comprehensive sample data for demo purposes
        
        Returns:
            dict: Complete sample estimates data structure
        """
        # Generate mock estimates
        estimates_df = self._generate_mock_estimates_data()
        
        # Calculate some summary metrics
        total_estimated_hours = estimates_df['estimated_hours'].sum()
        total_estimated_budget = estimates_df['estimated_budget'].sum()
        avg_hourly_rate = total_estimated_budget / total_estimated_hours if total_estimated_hours > 0 else 85
        
        # Get unique values
        clients = estimates_df['client'].unique().tolist()
        projects = estimates_df['project'].unique().tolist()
        employees = estimates_df['employee'].unique().tolist()
        
        return {
            'estimates_data': estimates_df,
            'clients': clients,
            'projects': projects,
            'employees': employees,
            'total_estimated_hours': total_estimated_hours,
            'total_estimated_budget': total_estimated_budget,
            'avg_hourly_rate': avg_hourly_rate,
            'total_projects': len(projects),
            'total_clients': len(clients)
        }

    def _generate_mock_estimates_data(self) -> pd.DataFrame:
        """
        Generate mock estimates data for testing
        
        Returns:
            pd.DataFrame: Mock estimates
        """
        # Sample data
        estimates_data = [
            {
                'client': 'Shlegel Construction',
                'project': 'Electrical Wiring',
                'estimated_hours': 120,
                'estimated_cost': 15000,
                'start_date': datetime(2024, 1, 15),
                'end_date': datetime(2024, 3, 15),
                'priority': 'High',
                'status': 'Active'
            },
            {
                'client': 'Shlegel Construction', 
                'project': 'Pipe Installation',
                'estimated_hours': 80,
                'estimated_cost': 10000,
                'start_date': datetime(2024, 2, 1),
                'end_date': datetime(2024, 4, 1),
                'priority': 'Medium',
                'status': 'Active'
            },
            {
                'client': 'TechCorp Solutions',
                'project': 'Database Migration',
                'estimated_hours': 200,
                'estimated_cost': 25000,
                'start_date': datetime(2024, 1, 1),
                'end_date': datetime(2024, 5, 1),
                'priority': 'High',
                'status': 'Active'
            },
            {
                'client': 'TechCorp Solutions',
                'project': 'API Development',
                'estimated_hours': 150,
                'estimated_cost': 18750,
                'start_date': datetime(2024, 3, 1),
                'end_date': datetime(2024, 6, 1),
                'priority': 'Medium',
                'status': 'Active'
            },
            {
                'client': 'BuildCo Inc',
                'project': 'Foundation Work',
                'estimated_hours': 300,
                'estimated_cost': 37500,
                'start_date': datetime(2024, 2, 15),
                'end_date': datetime(2024, 8, 15),
                'priority': 'High',
                'status': 'Active'
            },
            {
                'client': 'DataSys Analytics',
                'project': 'Data Analytics',
                'estimated_hours': 100,
                'estimated_cost': 12500,
                'start_date': datetime(2024, 3, 1),
                'end_date': datetime(2024, 5, 1),
                'priority': 'Medium',
                'status': 'Active'
            },
            {
                'client': 'WebFlow Digital',
                'project': 'Website Design',
                'estimated_hours': 75,
                'estimated_cost': 9375,
                'start_date': datetime(2024, 4, 1),
                'end_date': datetime(2024, 6, 1),
                'priority': 'Low',
                'status': 'Active'
            }
        ]
        
        df = pd.DataFrame(estimates_data)
        df['upload_date'] = datetime.now()
        df['progress_percentage'] = 0.0
        
        return df
    
    def _generate_mock_actual_data(self) -> pd.DataFrame:
        """
        Generate mock actual data for testing progress calculations
        
        Returns:
            pd.DataFrame: Mock actual timesheet data
        """
        # This would typically come from the API handler
        # For testing, generate some progress data
        actual_data = [
            {'client': 'Shlegel Construction', 'project': 'Electrical Wiring', 'hours': 95, 'date': datetime(2024, 2, 1)},
            {'client': 'Shlegel Construction', 'project': 'Pipe Installation', 'hours': 60, 'date': datetime(2024, 2, 15)},
            {'client': 'TechCorp Solutions', 'project': 'Database Migration', 'hours': 180, 'date': datetime(2024, 3, 1)},
            {'client': 'TechCorp Solutions', 'project': 'API Development', 'hours': 120, 'date': datetime(2024, 4, 1)},
            {'client': 'BuildCo Inc', 'project': 'Foundation Work', 'hours': 250, 'date': datetime(2024, 5, 1)},
            {'client': 'DataSys Analytics', 'project': 'Data Analytics', 'hours': 85, 'date': datetime(2024, 4, 15)},
            {'client': 'WebFlow Digital', 'project': 'Website Design', 'hours': 45, 'date': datetime(2024, 5, 1)},
        ]
        
        return pd.DataFrame(actual_data)
    
    def generate_mock_excel_file(self) -> bytes:
        """
        Generate a mock Excel file for testing
        
        Returns:
            bytes: Excel file content
        """
        estimates_df = self._generate_mock_estimates_data()
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            estimates_df.to_excel(writer, sheet_name='Project Estimates', index=False)
        
        output.seek(0)
        return output.read()

# Convenience functions
def get_estimates_handler() -> EstimatesHandler:
    """Get configured estimates handler instance"""
    return EstimatesHandler()

def process_excel_upload(file_content: bytes, filename: str) -> pd.DataFrame:
    """Process uploaded Excel file"""
    handler = get_estimates_handler()
    return handler.process_excel_estimates(file_content, filename)

def get_progress_comparison(actual_data: pd.DataFrame) -> pd.DataFrame:
    """Get progress vs estimates comparison"""
    handler = get_estimates_handler()
    return handler.calculate_progress_vs_estimates(actual_data)

def get_budget_alerts(progress_data: pd.DataFrame = None) -> List[Dict]:
    """Get budget alerts"""
    handler = get_estimates_handler()
    return handler.get_budget_alerts(progress_data)
