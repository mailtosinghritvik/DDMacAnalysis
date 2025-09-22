import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import numpy as np
from datetime import datetime, timedelta

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Supabase configuration (replace with your actual values)
SUPABASE_URL = "https://tgendmgdrljuxxxyynpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"

# Initialize Supabase client
if SUPABASE_AVAILABLE and SUPABASE_URL != "YOUR_SUPABASE_URL_HERE":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_CONFIGURED = True
    except Exception as e:
        SUPABASE_CONFIGURED = False
else:
    SUPABASE_CONFIGURED = False


def get_sample_accubid_data():
    """Get sample AccuBid data for testing"""
    sample_data = [
        {"duration_hours": None, "task_name": " || CCTV - PATHWAYS", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - SHARED SPACE", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || LIGHTING - SITE", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - MAIN SERVICE WEST (2000A)", "time_estimate": "61.91", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || SITE - EV CHARGING", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || GENERAL EXPENSES", "time_estimate": "8000", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || AREA - EAST SUITES", "time_estimate": "25600", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - EAST SUITES", "time_estimate": "25600", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || GENERATOR", "time_estimate": "97", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || GENERAL EXPENSES", "time_estimate": "8000", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - LS EAST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || EQUIPMENT - EAST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || COMMUNICATIONS - PATHWAYS", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || EQUIPMENT - WEST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || COMMUNICATIONS - PATHWAYS", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - NORMAL EAST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || ENGINEERING", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || MECHANICAL - WEST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || PRIMARY DUCT BANK", "time_estimate": "359.3", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - NORMAL WEST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || SITE - EV CHARGING", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || SECURITY - PATHWAYS", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - LS WEST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || EQUIPMENT - EAST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || PA SYSTEM", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || MECHANICAL - EAST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || CCTV - PATHWAYS", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || AREA - SHARED SPACE", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - WEST SUITES", "time_estimate": "25600.01", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - MAIN SERVICE EAST (2000A)", "time_estimate": "61.91", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - MAIN SERVICE EAST (2000A)", "time_estimate": "61.91", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || FIRE ALARM SYSTEM", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - WEST GENERAL", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - LS EAST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": "EVERYTHING", "time_estimate": "102631.99", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - EAST GENERAL", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || PRIMARY DUCT BANK", "time_estimate": "359.3", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - WEST GENERAL", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - NORMAL EAST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || NURSE CALL SYSTEM (CONDUIT RI)", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - MAIN SERVICE WEST (2000A)", "time_estimate": "61.91", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || FIRE ALARM SYSTEM", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || LIGHTING - SITE", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || AREA - EAST GENERAL", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || PA SYSTEM", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || NURSE CALL SYSTEM (CONDUIT RI)", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - NLS WEST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || SECONDARY DUCT BANK", "time_estimate": "585.79", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || ATS", "time_estimate": "64", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - NLS WEST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || MECHANICAL - WEST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || EQUIPMENT - WEST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - NLS EAST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - LS WEST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": "EVERYTHING", "time_estimate": "102631.99", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || AREA - WEST SUITES", "time_estimate": "25600.01", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || GENERATOR", "time_estimate": "97", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || MECHANICAL - EAST", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || SECONDARY DUCT BANK", "time_estimate": "585.79", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || SECURITY - PATHWAYS", "time_estimate": "0", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": None, "task_name": " || DIST - NORMAL WEST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || DIST - NLS EAST", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || ENGINEERING", "time_estimate": "0", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || COMMUNICATION DUCT BANK", "time_estimate": "105.36", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || ATS", "time_estimate": "64", "job_name": "Schelgel"},
        {"duration_hours": None, "task_name": " || COMMUNICATION DUCT BANK", "time_estimate": "105.36", "job_name": "LEESWOOD - East Penn"},
        {"duration_hours": "16.8833333333333333", "task_name": "Fire Alarm", "time_estimate": "36000", "job_name": "LEESWOOD - East Penn"}
    ]
    
    # Convert to DataFrame and process data types
    df = pd.DataFrame(sample_data)
    df['time_estimate'] = pd.to_numeric(df['time_estimate'], errors='coerce')
    df['duration_hours'] = pd.to_numeric(df['duration_hours'], errors='coerce')
    
    return df

def fetch_task_hours_data(limit=100, offset=0, jobcode_id=None, job_name=None):
    """Fetch task hours data from API"""
    try:
        # For demo purposes, return sample data
        if not SUPABASE_CONFIGURED:
            df = get_sample_accubid_data()
            # Filter by job name if specified
            if job_name and job_name != "All Projects":
                df = df[df['job_name'] == job_name]
            return df
            
        # Fetch task estimate list data
        if SUPABASE_CONFIGURED:
            # Use Supabase RPC function to fetch task summary
            # Convert jobcode_id to integer if it's a string, otherwise use None
            try:
                if jobcode_id and isinstance(jobcode_id, str):
                    # If it's a string, try to convert to int, otherwise use None
                    jobcode_id_int = int(jobcode_id) if jobcode_id.isdigit() else None
                else:
                    jobcode_id_int = jobcode_id
            except (ValueError, AttributeError):
                jobcode_id_int = None
                
            params = {
                   "p_limit": limit,
                   "p_offset": offset,
                   "p_job_name": job_name if job_name != "All Projects" else None,
                   "p_user_id": None,
                   "p_jobcode_id": jobcode_id_int
            }
            try:
                response = supabase.rpc("get_accubid_task_summary", params).execute()
                if response and response.data:
                    df = pd.DataFrame(response.data)
                    return df
                else:
                    df = get_sample_accubid_data()
                    # Filter by job name if specified
                    if job_name and job_name != "All Projects":
                        df = df[df['job_name'] == job_name]
                    return df
            except Exception as e:
                df = get_sample_accubid_data()
                # Filter by job name if specified
                if job_name and job_name != "All Projects":
                    df = df[df['job_name'] == job_name]
                return df
        else:
            df = get_sample_accubid_data()
            # Filter by job name if specified
            if job_name and job_name != "All Projects":
                df = df[df['job_name'] == job_name]
            return df

            
    except requests.exceptions.ConnectionError:
        df = get_sample_accubid_data()
        # Filter by job name if specified
        if job_name and job_name != "All Projects":
            df = df[df['job_name'] == job_name]
        return df
    except Exception as e:
        df = get_sample_accubid_data()
        # Filter by job name if specified
        if job_name and job_name != "All Projects":
            df = df[df['job_name'] == job_name]
        return df

def fetch_available_jobcodes():
    """Fetch available job codes with names for dropdown"""
    try:
        if SUPABASE_CONFIGURED:
            # Query distinct client names from Supabase table
            try:
                response = supabase.table("accubid_breakdowns").select("job_name").neq("job_name", None).execute()
                if response and response.data:
                    # Get unique client names
                    client_names = pd.DataFrame(response.data)['job_name'].dropna().unique().tolist()
                    # Return as list of tuples (client_name, client_name)
                    return [(name, name) for name in client_names]
                else:
                    return []
            except Exception as e:
                return []
       
         
        return []
    except Exception:
        return []



def create_planned_vs_actual_chart(df):
    """Create planned vs actual hours chart"""
    if df.empty:
        return None, pd.DataFrame()
    
    # Check if required columns exist - updated for AccuBid data structure
    required_cols = ['task_name', 'time_estimate']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return None, pd.DataFrame()
    
    # Group by task name and calculate totals
    agg_dict = {
        'time_estimate': 'sum'
    }
    
    # Add duration_hours if available
    if 'duration_hours' in df.columns:
        agg_dict['duration_hours'] = 'sum'
    
    task_data = df.groupby('task_name').agg(agg_dict).reset_index()
    
    # Rename columns for clarity
    new_columns = ['Task_Name', 'Estimated_Hours']
    if len(task_data.columns) > 2:
        new_columns.append('Actual_Hours')
    task_data.columns = new_columns
    
    # Convert time estimates from hours to hours (already in hours for AccuBid data)
    #task_data['Planned_Hours'] = task_data['Estimated_Hours'].fillna(0)
    
    # Handle actual hours
    if 'Actual_Hours' in task_data.columns:
        task_data['Actual_Hours'] = task_data['Actual_Hours'].fillna(0)
    else:
        task_data['Actual_Hours'] = 0
    
    # Calculate variance
    task_data['Variance'] = task_data['Actual_Hours'] - task_data['Estimated_Hours']
    task_data['Variance_Percent'] = np.where(
        task_data['Estimated_Hours'] > 0,
        (task_data['Variance'] / task_data['Estimated_Hours'] * 100).round(2),
        0
    )
    
    # Create the chart
    fig = go.Figure()
    
    # Add planned hours bar
    fig.add_trace(go.Bar(
        name='Estimated Hours',
        x=task_data['Task_Name'],
        y=task_data['Estimated_Hours'],
        marker_color='lightblue',
        text=task_data['Estimated_Hours'].round(1),
        textposition='auto',
    ))
    
    # Add actual hours bar
    fig.add_trace(go.Bar(
        name='Actual Hours',
        x=task_data['Task_Name'],
        y=task_data['Actual_Hours'],
        marker_color='darkblue',
        text=task_data['Actual_Hours'].round(1),
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Estimated vs Actual Task Hours by Task Name',
        xaxis_title='Task Name',
        yaxis_title='Hours',
        barmode='group',
        height=500,
        showlegend=True
    )
    
    return fig, task_data

def create_variance_chart(task_data):
    """Create variance analysis chart"""
    if task_data.empty or 'Variance' not in task_data.columns:
        return None
    
    # Create variance chart
    fig = go.Figure()
    
    # Add variance bars
    colors = ['red' if x < 0 else 'green' for x in task_data['Variance']]
    
    # Use the correct column name based on data structure
    x_column = 'Task_Name' if 'Task_Name' in task_data.columns else 'Task_Type'
    
    fig.add_trace(go.Bar(
        x=task_data[x_column],
        y=task_data['Variance'],
        marker_color=colors,
        text=task_data['Variance'].round(1),
        textposition='auto',
        name='Variance (Actual - Planned)'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title='Hours Variance by Task Name (Negative = Under Budget, Positive = Over Budget)',
        xaxis_title='Task Name',
        yaxis_title='Hours Variance',
        height=400,
        showlegend=False
    )
    
    return fig

def create_efficiency_chart(task_data):
    """Create efficiency chart showing variance percentage"""
    if task_data.empty or 'Variance_Percent' not in task_data.columns:
        return None
    
    # Create efficiency chart
    fig = go.Figure()
    
    # Add efficiency bars
    colors = ['red' if x < 0 else 'green' for x in task_data['Variance_Percent']]
    
    # Use the correct column name based on data structure
    x_column = 'Task_Name' if 'Task_Name' in task_data.columns else 'Task_Type'
    
    fig.add_trace(go.Bar(
        x=task_data[x_column],
        y=task_data['Variance_Percent'],
        marker_color=colors,
        text=task_data['Variance_Percent'].round(1).astype(str) + '%',
        textposition='auto',
        name='Efficiency %'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title='Task Name Efficiency (Negative = Under Budget, Positive = Over Budget)',
        xaxis_title='Task Name',
        yaxis_title='Efficiency %',
        height=400,
        showlegend=False
    )
    
    return fig

def create_user_efficiency_chart(df):
    """Create task efficiency chart"""
    if df.empty:
        return None, pd.DataFrame()
    
    # Check if required columns exist
    if 'duration_hours' not in df.columns or 'task_name' not in df.columns:
        return None, pd.DataFrame()
    
    # Group by task name and calculate efficiency
    task_data = df.groupby('task_name').agg({
        'duration_hours': 'sum',
        'time_estimate': 'sum'
    }).reset_index()
    
    # Calculate planned hours from time estimates (already in hours for AccuBid data)
    task_data['Actual_Hours'] = task_data['duration_hours'].fillna(0)
    task_data['Planned_Hours'] = task_data['time_estimate'].fillna(0)
    
    # Calculate efficiency
    task_data['Efficiency'] = np.where(
        task_data['Planned_Hours'] > 0,
        (task_data['Actual_Hours'] / task_data['Planned_Hours'] * 100).round(2),
        0
    )
    
    # Create the chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=task_data['task_name'],
        y=task_data['Efficiency'],
        marker_color='lightgreen',
        text=task_data['Efficiency'].round(1).astype(str) + '%',
        textposition='auto',
        name='Efficiency %'
    ))
    
    # Add 100% line
    fig.add_hline(y=100, line_dash="dash", line_color="red", opacity=0.7, 
                  annotation_text="100% Target Line")
    
    fig.update_layout(
        title='Task Name Efficiency (Actual Hours / Estimated Hours)',
        xaxis_title='Task Name',
        yaxis_title='Efficiency %',
        height=400,
        showlegend=False
    )
    
    return fig, task_data

def fetch_est_vs_act_hrs(df):
    pass

def create_job_analysis_chart(df):
    """Create job-based analysis chart"""
    if df.empty:
        return None
    
    # Check if required columns exist
    if 'job_name' not in df.columns or 'time_estimate' not in df.columns:
        return None
    
    # Group by job name and calculate totals
    job_data = df.groupby('job_name').agg({
        'time_estimate': 'sum'
    }).reset_index()
    
    # Get actual hours from timesheet table for each job
    actual_hours_dict = {}
    unique_job_names = df['job_name'].dropna().unique().tolist()
    
    for job_name in unique_job_names:
        # Get jobid from jobcodes table
        jobid_response = supabase.table("jobcodes").select("id").eq("name", job_name).execute()
        jobid = None
        if jobid_response and jobid_response.data and len(jobid_response.data) > 0:
            jobid = jobid_response.data[0].get("id")
        
        # If jobid found, get sum of times from timesheets table
        if jobid:
            times_response = supabase.table("timesheets").select("duration").eq("jobcode_id", jobid).execute()
            total_times = 0
            if times_response and times_response.data:
                # Sum the 'duration' field for all records and convert to hours
                total_times = sum([row.get("duration", 0) or 0 for row in times_response.data]) / 3600
            actual_hours_dict[job_name] = total_times
        else:
            actual_hours_dict[job_name] = 0
    
    # Convert time estimates to hours (already in hours for AccuBid data)
    job_data['Estimated_Hours'] = job_data['time_estimate'].fillna(0)
    
    # Map actual hours to each job
    job_data['Actual_Hours'] = job_data['job_name'].map(actual_hours_dict).fillna(0)
    
    # Create the chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=job_data['job_name'],
        y=job_data['Estimated_Hours'],
        name='Estimated Hours',
        marker_color='lightgreen',
        text=job_data['Estimated_Hours'].round(1),
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=job_data['job_name'],
        y=job_data['Actual_Hours'],
        name='Actual Hours',
        marker_color='darkgreen',
        text=job_data['Actual_Hours'].round(1),
        textposition='auto'
    ))
    
    fig.update_layout(
        title='Estimated vs Actual Hours by Job',
        xaxis_title='Job Name',
        yaxis_title='Hours',
        barmode='group',
        height=400,
        showlegend=True
    )
    
    return fig, job_data

def create_task_category_chart(df):
    """Create task category breakdown chart"""
    if df.empty:
        return None
    
    # Check if required columns exist
    if 'task_name' not in df.columns or 'time_estimate' not in df.columns:
        return None
    
    # Extract task categories from task names (before the " || " separator)
    df['task_category'] = df['task_name'].str.split(' || ').str[0]
    df['task_category'] = df['task_category'].fillna('Other')
    
    # Group by task category and calculate totals
    category_data = df.groupby('task_category').agg({
        'time_estimate': 'sum',
        'duration_hours': 'sum' if 'duration_hours' in df.columns else lambda x: 0
    }).reset_index()
    
    # Convert time estimates to hours
    category_data['Estimated_Hours'] = category_data['time_estimate'].fillna(0)
    category_data['Actual_Hours'] = category_data['duration_hours'].fillna(0)
    
    # Create pie chart for estimated hours
    fig = go.Figure(data=[go.Pie(
        labels=category_data['task_category'],
        values=category_data['Estimated_Hours'],
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f} hrs<br>(%{percent})',
        hovertemplate='<b>%{label}</b><br>Estimated Hours: %{value:.1f}<br>Percentage: %{percent}<extra></extra>'
    )])
    
  
    
    return fig, category_data

def create_timeline_chart(df):
    """Create timeline chart showing hours over time"""
    if df.empty:
        return None
    
    # Check if required columns exist
    if 'duration_hours' not in df.columns:
        return None
    
    # Since we don't have time data, create a simple task type comparison
    if 'value' not in df.columns:
        return None
    
    # Group by task type and calculate totals
    task_data = df.groupby('value').agg({
        'duration_hours': 'sum',
        'time_estimate': 'sum'
    }).reset_index()
    
    # Convert time estimates from seconds to hours
    task_data['Actual_Hours'] = task_data['duration_hours']
    task_data['Planned_Hours'] = task_data['time_estimate'].fillna(0) / 3600
    
    # Create the chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=task_data['value'],
        y=task_data['Planned_Hours'],
        name='Planned Hours',
        marker_color='lightblue',
        text=task_data['Planned_Hours'].round(1),
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=task_data['value'],
        y=task_data['Actual_Hours'],
        name='Actual Hours',
        marker_color='darkblue',
        text=task_data['Actual_Hours'].round(1),
        textposition='auto'
    ))
    
    fig.update_layout(
        title='Planned vs Actual Hours by Task Type',
        xaxis_title='Task Type',
        yaxis_title='Hours',
        barmode='group',
        height=400,
        showlegend=True
    )
    
    return fig

def main():
    """Main Task Hours Analytics Dashboard"""
    
    # Page configuration
    st.set_page_config(
        page_title="Task Hours Analytics",
        page_icon="⏱️",
        layout="wide"
    )
    
    # Header
    st.title("⏱️ Task Hours Analytics")
    st.markdown("Analyze planned vs actual task hours across projects and task types")
    
    # Controls Section
    st.subheader("🔧 Controls & Filters")
    
    # Create columns for controls
    col3, col4 = st.columns(2)
    
 
    
    with col3:
        # Create job name dropdown from sample data
        job_names = ["All Projects", "Schelgel", "LEESWOOD - East Penn"]
        selected_job_name = st.selectbox("Select Job/Client", job_names)
        
        # For now, we'll use job name filtering instead of job code ID
        jobcode_id = None
    
    with col4:
        st.write("")  # Empty space for alignment
        if st.button("🔄 Refresh Data", key="refresh_task_hours"):
            st.rerun()
    
    # API Status - removed info message
    
    # Fetch data
    with st.spinner("Loading task hours data..."):
        df = fetch_task_hours_data(limit=1000, offset=0, jobcode_id=jobcode_id, job_name=selected_job_name)
    if df.empty:
        return
    
    
    # Main charts
  
    
    # Job Analysis Chart
    st.subheader("🏗️ Job Analysis - Estimated vs Actual Hours")
    job_fig, job_data = create_job_analysis_chart(df)
    if job_fig:
        st.plotly_chart(job_fig, use_container_width=True)
        
        # Display job data table
        st.subheader("📋 Job Details")
        st.dataframe(job_data, use_container_width=True)
    
   
  
    
    # Planned vs Actual Hours Chart
    st.markdown("---")
    st.subheader("📈 Estimated vs Actual Hours by Task Name")
    planned_actual_fig, task_data = create_planned_vs_actual_chart(df)
    if planned_actual_fig:
        st.plotly_chart(planned_actual_fig, use_container_width=True)
        
        # Display task data table
        st.subheader("📋 Task Details")
        st.dataframe(task_data, use_container_width=True)
    
    # Variance Analysis
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Hours Variance")
        variance_fig = create_variance_chart(task_data)
        if variance_fig:
            st.plotly_chart(variance_fig, use_container_width=True)
        else:
            st.write("No variance data available")
    
    with col2:
        st.subheader("📊 Efficiency Analysis")
        efficiency_fig = create_efficiency_chart(task_data)
        if efficiency_fig:
            st.plotly_chart(efficiency_fig, use_container_width=True)
        else:
            st.write("No efficiency data available")
    
    # Raw Data Display
    st.markdown("---")
    st.subheader("📄 Raw AccuBid Data")
    st.dataframe(df, use_container_width=True)
    
    # Summary Statistics
    st.markdown("---")
    st.subheader("📈 Summary Statistics")
    
    if not task_data.empty and 'Variance' in task_data.columns:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_variance = task_data['Variance'].mean()
            st.metric("Average Variance", f"{avg_variance:.1f} hours")
        
        with col2:
            over_budget_tasks = len(task_data[task_data['Variance'] > 0])
            st.metric("Over Budget Tasks", over_budget_tasks)
        
        with col3:
            under_budget_tasks = len(task_data[task_data['Variance'] < 0])
            st.metric("Under Budget Tasks", under_budget_tasks)
    
    # Additional AccuBid-specific statistics
    if not df.empty:
        st.subheader("📊 AccuBid Project Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_estimated = df['time_estimate'].sum() if 'time_estimate' in df.columns else 0
            st.metric("Total Estimated Hours", f"{total_estimated:.1f}")
        
        with col2:
            total_actual = df['duration_hours'].sum() if 'duration_hours' in df.columns else 0
            st.metric("Total Actual Hours", f"{total_actual:.1f}")
        
        with col3:
            if 'job_name' in df.columns:
                unique_jobs = df['job_name'].nunique()
                st.metric("Number of Jobs", unique_jobs)
            else:
                st.metric("Number of Jobs", "N/A")
        
        with col4:
            if 'task_name' in df.columns:
                unique_tasks = df['task_name'].nunique()
                st.metric("Number of Tasks", unique_tasks)
            else:
                st.metric("Number of Tasks", "N/A")

if __name__ == "__main__":
    main()
