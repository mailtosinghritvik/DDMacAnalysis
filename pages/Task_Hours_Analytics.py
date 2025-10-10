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

# Supabase configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
if SUPABASE_AVAILABLE and SUPABASE_URL != "YOUR_SUPABASE_URL_HERE":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_CONFIGURED = True
    except Exception as e:
        SUPABASE_CONFIGURED = False
else:
    SUPABASE_CONFIGURED = False


def get_empty_dataframe():
    """Return empty DataFrame with expected columns"""
    return pd.DataFrame(columns=['task_name', 'time_estimate', 'duration_hours', 'job_name'])

def fetch_task_hours_data(limit=100, offset=0, jobcode_id=None, job_name=None):
    """Fetch task hours data from API"""
    try:
        # Return empty data if Supabase not configured
        if not SUPABASE_CONFIGURED:
            return get_empty_dataframe()
            
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
                    return get_empty_dataframe()
            except Exception as e:
                return get_empty_dataframe()
        else:
            return get_empty_dataframe()

            
    except requests.exceptions.ConnectionError:
        return get_empty_dataframe()
    except Exception as e:
        return get_empty_dataframe()

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



def create_planned_vs_actual_chart(df, selected_job_name=None):
    """Create planned vs actual hours chart with foreman progress"""
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
    
    # Get foreman progress for tasks
    foreman_progress = get_foreman_progress_for_tasks(task_data, selected_job_name)
    task_data['Foreman_Progress_%'] = task_data['Task_Name'].map(foreman_progress).fillna(0)
    
    # Calculate actual completion percentage based on actual vs estimated hours
    task_data['Actual_Completion_%'] = np.where(
        task_data['Estimated_Hours'] > 0,
        (task_data['Actual_Hours'] / task_data['Estimated_Hours'] * 100).round(2),
        0
    )
    
    # Calculate if foreman is faster or slower than actual progress
    # If foreman reports higher % than actual completion, they are SLOWER (behind actual work)
    # If foreman reports lower % than actual completion, they are FASTER (ahead of actual work)
    task_data['Faster_or_Slower'] = np.where(
        task_data['Foreman_Progress_%'] > task_data['Actual_Completion_%'],
        'Slower',
        np.where(
            task_data['Foreman_Progress_%'] < task_data['Actual_Completion_%'],
            'Faster',
            'On Track'
        )
    )
    
    # Calculate the difference between foreman progress and actual completion
    task_data['Progress_Difference'] = (task_data['Foreman_Progress_%'] - task_data['Actual_Completion_%']).round(2)
    
    # Calculate statistical variance between Actual_Hours and Estimated_Hours
    # Treating each as a single observation from two samples, so variance = ((x1 - mean)^2 + (x2 - mean)^2) / (n-1) where n=2
    def calc_stat_variance(row):
        x1 = row['Actual_Hours']
        x2 = row['Estimated_Hours']
        mean = (x1 + x2) / 2
        # For n=2, denominator is 1
        return (((x1 - mean) ** 2 + (x2 - mean) ** 2) / 1)**0.5

    task_data['Variance'] = task_data.apply(calc_stat_variance, axis=1)
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
    
    # Add foreman progress line (scaled to fit the chart)
    if 'Foreman_Progress_%' in task_data.columns:
        # Scale foreman progress to fit within the chart range
        max_hours = max(task_data['Estimated_Hours'].max(), task_data['Actual_Hours'].max())
        if max_hours > 0:
            scaled_progress = (task_data['Foreman_Progress_%'] / 100) * max_hours
            
            # Create color coding based on faster/slower status
            colors = []
            for status in task_data['Faster_or_Slower']:
                if status == 'Faster':
                    colors.append('green')
                elif status == 'Slower':
                    colors.append('red')
                else:  # On Track
                    colors.append('orange')
            
            fig.add_trace(go.Scatter(
                name='Foreman Progress %',
                x=task_data['Task_Name'],
                y=scaled_progress,
                mode='lines+markers',
                line=dict(color='orange', width=3),
                marker=dict(size=8, color=colors),
                text=task_data['Foreman_Progress_%'].round(1).astype(str) + '%<br>' + 
                     task_data['Faster_or_Slower'] + '<br>' +
                     'Diff: ' + task_data['Progress_Difference'].astype(str) + '%',
                textposition='top center',
                yaxis='y'
            ))
    
    fig.update_layout(
        title='Estimated vs Actual Task Hours by Task Name (with Foreman Progress)',
        xaxis_title='Task Name',
        yaxis_title='Hours',
        barmode='group',
        height=500,
        showlegend=True
    )
    
    return fig, task_data

def get_foreman_progress_for_tasks(task_data: pd.DataFrame, selected_job_name: str) -> dict:
    """Get foreman progress for tasks from task_progress table.
    
    Returns a dictionary mapping task_name to latest progress percentage.
    """
    progress_map = {}
    if not SUPABASE_CONFIGURED or task_data is None or task_data.empty:
        return progress_map
    
    try:
        # Get task IDs from accubid_breakdowns for the selected job
        abd_res = (
            supabase.table("accubid_breakdowns")
            .select("id, Task_name, job_name")
            .eq("job_name", selected_job_name)
            .execute()
        )
        
        if not abd_res or not abd_res.data:
            return progress_map
            
        # Create mapping from task_name to task_id
        task_name_to_id = {}
        for row in abd_res.data:
            task_name = row.get("Task_name")
            task_id = row.get("id")
            if task_name and task_id is not None:
                task_name_to_id[task_name] = task_id
        
        # Debug: Print task mapping for troubleshooting
        # st.write("Debug - Task name to ID mapping:", task_name_to_id)
        
        # Get latest progress for each task
        for task_name, task_id in task_name_to_id.items():
            try:
                progress_res = (
                    supabase.table("task_progress")
                    .select("progress, created_at")
                    .eq("task_id", task_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                
                if progress_res and progress_res.data:
                    progress_value = progress_res.data[0].get("progress", 0)
                    progress_map[task_name] = progress_value
                    # Debug: Print progress found
                    # st.write(f"Debug - Found progress for {task_name}: {progress_value}%")
                else:
                    progress_map[task_name] = 0
                    # Debug: Print no progress found
                    # st.write(f"Debug - No progress found for {task_name}")
            except Exception as e:
                progress_map[task_name] = 0
                # Debug: Print error
                # st.write(f"Debug - Error getting progress for {task_name}: {str(e)}")
                
    except Exception as e:
        # Debug: Print general error
        # st.write(f"Debug - General error in get_foreman_progress_for_tasks: {str(e)}")
        pass
    
    return progress_map

def save_task_progress_rows(task_data: pd.DataFrame, selected_job_name: str) -> dict:
    """Persist task progress rows into public.task_progress.

    Only runs when Supabase is configured and a specific job (not All Projects) is selected.
    Returns summary dict with counts.
    """
    summary = {"inserted": 0, "skipped": 0, "errors": 0}
    if not SUPABASE_CONFIGURED:
        return summary
    if not selected_job_name or selected_job_name == "All Projects":
        return summary
    if task_data is None or task_data.empty:
        return summary

    # Ensure required columns
    required = {"Task_Name", "Estimated_Hours", "Actual_Hours"}
    if not required.issubset(set(task_data.columns)):
        return summary

    try:
        # Map task_name -> accubid_breakdowns.id within the selected job
        abd_res = (
            supabase.table("accubid_breakdowns")
            .select("id, Task_name, job_name")
            .eq("job_name", selected_job_name)
            .execute()
        )
        mapping = {}
        if abd_res and abd_res.data:
            for row in abd_res.data:
                tname = row.get("Task_name")
                tid = row.get("id")
                if tname and tid is not None:
                    # If duplicates, keep first
                    mapping.setdefault(tname, tid)

        # Insert each task row
        for _, row in task_data.iterrows():
            task_name = row.get("Task_Name")
            est = float(row.get("Estimated_Hours") or 0)
            act = float(row.get("Actual_Hours") or 0)
            if not task_name:
                summary["skipped"] += 1
                continue
            task_id = mapping.get(task_name)
            if task_id is None:
                # No matching task id in accubid_breakdowns for this job
                summary["skipped"] += 1
                continue
            progress_val = 0.0 if est <= 0 else (act / est) * 100.0

            # Write row
            try:
                supabase.table("task_progress").insert({
                    "task_id": task_id,
                    "progress": progress_val,
                }).execute()
                summary["inserted"] += 1
            except Exception:
                summary["errors"] += 1
        return summary
    except Exception:
        return summary

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


def build_task_progress_table(selected_job_name=None):
    """Build task progress table using estimates from accubid_breakdowns and actuals from timesheets.

    Progress % = (Actual_Hours / Estimated_Hours) * 100
    """
    if not SUPABASE_CONFIGURED:
        # Return empty DataFrame when Supabase not configured
        return pd.DataFrame(columns=["job_name", "Estimated_Hours", "Actual_Hours", "Completion_%"])

    # Supabase path
    try:
        # Filter accubid_breakdowns by job if provided
        abd_query = supabase.table("accubid_breakdowns").select("job_name,task_name,time_estimate")
        if selected_job_name and selected_job_name != "All Projects":
            abd_query = abd_query.eq("job_name", selected_job_name)
        abd_res = abd_query.execute()
        abd_rows = abd_res.data if abd_res and abd_res.data else []

        if not abd_rows:
            return pd.DataFrame(columns=["job_name", "Estimated_Hours", "Actual_Hours", "Completion_%"])  # empty

        abd_df = pd.DataFrame(abd_rows)
        if "time_estimate" in abd_df.columns:
            abd_df["time_estimate"] = pd.to_numeric(abd_df["time_estimate"], errors="coerce").fillna(0.0)

        # Compute estimate per job: prefer EVERYTHING rows per job; else sum all
        def compute_estimate(group: pd.DataFrame) -> float:
            everything = group[group["task_name"].str.contains("EVERYTHING", case=False, na=False)]
            if not everything.empty:
                return float(everything["time_estimate"].sum())
            return float(group["time_estimate"].sum())

        est_df = (
            abd_df.groupby("job_name")
            .apply(compute_estimate)
            .reset_index(name="Estimated_Hours")
        )

        # For actuals, map job_name -> jobcodes.id then sum timesheets.duration
        job_names = est_df["job_name"].dropna().unique().tolist()

        actual_hours_map = {}
        for job_name in job_names:
            try:
                jc_res = supabase.table("jobcodes").select("id").eq("name", job_name).execute()
                jobcode_id = None
                if jc_res and jc_res.data:
                    jobcode_id = jc_res.data[0].get("id")
                if jobcode_id:
                    ts_res = (
                        supabase.table("timesheets").select("duration").eq("jobcode_id", jobcode_id).execute()
                    )
                    total_seconds = 0
                    if ts_res and ts_res.data:
                        total_seconds = sum([(row.get("duration") or 0) for row in ts_res.data])
                    actual_hours_map[job_name] = float(total_seconds) / 3600.0
                else:
                    actual_hours_map[job_name] = 0.0
            except Exception:
                actual_hours_map[job_name] = 0.0

        est_df["Actual_Hours"] = est_df["job_name"].map(actual_hours_map).fillna(0.0)
        est_df["Completion_%"] = np.where(
            est_df["Estimated_Hours"] > 0,
            (est_df["Actual_Hours"] / est_df["Estimated_Hours"]) * 100.0,
            0.0,
        )

        # Sort for easier readability
        est_df = est_df.sort_values(by=["Completion_%"], ascending=False).reset_index(drop=True)
        return est_df
    except Exception:
        return pd.DataFrame(columns=["job_name", "Estimated_Hours", "Actual_Hours", "Completion_%"])  # empty

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
    st.markdown("Analyze planned vs actual task hours - EVERYTHING tasks overview and detailed task breakdown")
    
    # Controls Section
    st.subheader("🔧 Controls & Filters")
    
    # Create columns for controls
    col3, col4 = st.columns(2)
    
 
    
    with col3:
    # Create job name dropdown from available data
        job_names = ["All Projects"]
        if SUPABASE_CONFIGURED:
            try:
                available_jobs = fetch_available_jobcodes()
                if available_jobs:
                    job_names.extend([job[0] for job in available_jobs])
            except Exception:
                pass
        
        selected_job_name = st.selectbox("Select Job/Client", job_names)
            
            # For now, we'll use job name filtering instead of job code ID
        jobcode_id = None
    
    with col4:
        st.write("")  # Empty space for alignment
        if st.button("🔄 Refresh Data", key="refresh_task_hours"):
            st.rerun()
    
    # API Status - removed info message
    
    # Task Progress Table (Completion %)
    st.markdown("---")
    st.subheader("✅ Task Progress (Completion %)")
    with st.spinner("Building progress table..."):
        progress_df = build_task_progress_table(selected_job_name)
    if progress_df is not None and not progress_df.empty:
        st.dataframe(progress_df, use_container_width=True)
    else:
        st.info("📈 No progress data available yet.")
        if not SUPABASE_CONFIGURED:
            st.info("💡 Configure Supabase to enable progress tracking features.")
        else:
            st.info("💡 Progress data will appear once tasks are created and time tracking begins.")

    # Fetch data
    with st.spinner("Loading task hours data..."):
        df = fetch_task_hours_data(limit=1000, offset=0, jobcode_id=jobcode_id, job_name=selected_job_name)
    
    if df.empty:
        st.info("📊 No task data available for the selected project.")
        if not SUPABASE_CONFIGURED:
            st.info("💡 To view data, please configure Supabase connection in your environment settings.")
        else:
            st.info("💡 Data may not be available yet. Check if AccuBid data has been imported to the database.")
        return
    
    
    # Main charts
  
    
    # Job Analysis Chart - Show only EVERYTHING tasks
    st.subheader("🏗️ Job Analysis - EVERYTHING Tasks Only")
    
    # Filter to show only EVERYTHING tasks for this chart
    everything_df = df[df['task_name'].str.contains('EVERYTHING', case=False, na=False)] if not df.empty and 'task_name' in df.columns else df
    
    if not everything_df.empty:
        job_fig, job_data = create_job_analysis_chart(everything_df)
        if job_fig:
            st.plotly_chart(job_fig, use_container_width=True)
            
            # Display job data table
            st.subheader("📋 Job Details - EVERYTHING Tasks")
            st.dataframe(job_data, use_container_width=True)
    else:
        st.info("📋 No 'EVERYTHING' tasks found for the selected project.")
        st.info("💡 EVERYTHING tasks represent the total project estimates. They will appear once AccuBid data is imported.") 
    
   
  
    
    # Planned vs Actual Hours Chart - Show actual tasks (excluding EVERYTHING)
    st.markdown("---")
    st.subheader("📈 Actual Tasks - Estimated vs Actual Hours")
    
    # Filter out EVERYTHING tasks for this chart
    actual_tasks_df = df[~df['task_name'].str.contains('EVERYTHING', case=False, na=False)] if not df.empty and 'task_name' in df.columns else df
    
    if not actual_tasks_df.empty:
        planned_actual_fig, task_data = create_planned_vs_actual_chart(actual_tasks_df, selected_job_name)
        if planned_actual_fig:
            st.plotly_chart(planned_actual_fig, use_container_width=True)
            
            # Display task data table
            st.subheader("📋 Task Details - Actual Tasks")
            st.dataframe(task_data, use_container_width=True)
            
            # Foreman Progress Input Section
            if SUPABASE_CONFIGURED and selected_job_name != "All Projects":
                st.markdown("---")
                st.subheader("👷 Foreman Progress Update")
                
                # Get task options for the selected job
                try:
                    abd_res = (
                        supabase.table("accubid_breakdowns")
                        .select("id, Task_name")
                        .eq("job_name", selected_job_name)
                        .execute()
                    )
                    
                    if abd_res and abd_res.data:
                        # Create task selection dropdown
                        task_options = {}
                        for row in abd_res.data:
                            task_name = row.get("Task_name")
                            task_id = row.get("id")
                            if task_name and task_id is not None:
                                task_options[f"{task_name} (ID: {task_id})"] = task_id
                        
                        if task_options:
                            selected_task_display = st.selectbox(
                                "Select Task to Update Progress:",
                                options=list(task_options.keys()),
                                key="foreman_task_selector"
                            )
                            selected_task_id = task_options[selected_task_display]
                            
                            # Get current progress for the selected task
                            current_progress = 0
                            try:
                                progress_res = (
                                    supabase.table("task_progress")
                                    .select("progress, created_at")
                                    .eq("task_id", selected_task_id)
                                    .order("created_at", desc=True)
                                    .limit(1)
                                    .execute()
                                )
                                if progress_res and progress_res.data:
                                    current_progress = progress_res.data[0].get("progress", 0)
                            except Exception:
                                pass
                            
                            # Progress input
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                new_progress = st.slider(
                                    f"Progress Percentage (Current: {current_progress}%):",
                                    min_value=0,
                                    max_value=100,
                                    value=current_progress,
                                    key="foreman_progress_slider"
                                )
                            
                            with col2:
                                st.write("")  # Empty space for alignment
                                if st.button("💾 Update Foreman Progress", key="update_foreman_progress", type="primary"):
                                    # Insert new progress
                                    try:
                                        data = {
                                            'task_id': selected_task_id,
                                            'progress': new_progress,
                                            'created_at': datetime.now().isoformat()
                                        }
                                        
                                        result = supabase.table('task_progress').insert(data).execute()
                                        
                                        if result.data:
                                            st.success(f"✅ Foreman progress updated successfully!")
                                            st.success(f"Task: {selected_task_display}")
                                            st.success(f"Progress: {new_progress}%")
                                            st.rerun()  # Refresh the page to show updated data
                                        else:
                                            st.info("💾 Progress update was not saved. Please try again.")
                                    except Exception as e:
                                        st.info("💾 Unable to save progress at this time. Please check your connection and try again.")
                        else:
                            st.info("📋 No tasks found for the selected job.")
                            st.info("💡 Tasks will appear once AccuBid data is imported for this project.")
                    else:
                        st.info("📋 No tasks found for the selected job.")
                        st.info("💡 Tasks will appear once AccuBid data is imported for this project.")
                except Exception as e:
                    st.info("📋 Unable to load tasks at this time.")
                    st.info("💡 Please check your database connection and try again.")
            
            # Save progress button (only when a specific job is selected)
            if SUPABASE_CONFIGURED and selected_job_name != "All Projects":
                if st.button("💾 Save Task Progress to Database", key="save_task_progress"):
                    with st.spinner("Saving progress to task_progress..."):
                        result = save_task_progress_rows(task_data, selected_job_name)
                    if result.get('inserted', 0) > 0:
                        st.success(f"✅ Progress saved: {result.get('inserted',0)} tasks updated")
                    if result.get('skipped', 0) > 0:
                        st.info(f"⏭️ Skipped: {result.get('skipped',0)} tasks (no matching data)")
                    if result.get('errors', 0) > 0:
                        st.info(f"⚠️ Issues: {result.get('errors',0)} tasks could not be saved")
            elif not SUPABASE_CONFIGURED:
                st.info("💾 Progress saving requires Supabase configuration.")
            else:
                st.info("💾 Select a specific job to enable progress saving features.")
    else:
        st.info("📊 No individual task data available yet.")
        st.info("💡 Individual task breakdowns will appear once AccuBid data is imported and processed.")
    
    # Progress Analysis Section
    st.markdown("---")
    st.subheader("⚡ Foreman vs Actual Progress Analysis")
    
    if not actual_tasks_df.empty and 'Faster_or_Slower' in task_data.columns:
        # Create a summary table for progress analysis
        progress_summary = task_data[['Task_Name', 'Foreman_Progress_%', 'Actual_Completion_%', 'Faster_or_Slower', 'Progress_Difference']].copy()
        progress_summary = progress_summary.sort_values('Progress_Difference', ascending=False)
        
        # Color code the faster/slower column
        def color_faster_slower(val):
            if val == 'Faster':
                return 'background-color: #d4edda; color: #155724'  # Green
            elif val == 'Slower':
                return 'background-color: #f8d7da; color: #721c24'  # Red
            else:
                return 'background-color: #fff3cd; color: #856404'  # Yellow
        
        styled_summary = progress_summary.style.applymap(color_faster_slower, subset=['Faster_or_Slower'])
        st.dataframe(styled_summary, use_container_width=True)
        
        # Add explanation
        st.info("""
        **Progress Analysis Legend:**
        - 🟢 **Faster**: Foreman reports lower progress than actual completion (ahead of actual work)
        - 🔴 **Slower**: Foreman reports higher progress than actual completion (behind actual work)
        - 🟡 **On Track**: Foreman progress matches actual completion
        - **Progress Difference**: Foreman % - Actual Completion %
        """)
    else:
        st.info("⚡ Progress analysis will be available once both foreman progress and actual completion data are present.")
    
    # Variance Analysis - Use actual tasks data
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Hours Variance - Actual Tasks")
        if not actual_tasks_df.empty:
            variance_fig = create_variance_chart(task_data)
            if variance_fig:
                st.plotly_chart(variance_fig, use_container_width=True)
            else:
                st.info("📊 Variance analysis will be available once task data is loaded.")
        else:
            st.info("📊 Variance analysis requires individual task data to be available.")
    
    with col2:
        st.subheader("📊 Efficiency Analysis - Actual Tasks")
        if not actual_tasks_df.empty:
            efficiency_fig = create_efficiency_chart(task_data)
            if efficiency_fig:
                st.plotly_chart(efficiency_fig, use_container_width=True)
            else:
                st.info("📊 Efficiency analysis will be available once task data is loaded.")
        else:
            st.info("📊 Efficiency analysis requires individual task data to be available.")
    
    # Raw Data Display
    st.markdown("---")
    st.subheader("📄 Raw AccuBid Data")
    st.dataframe(df, use_container_width=True)
    
    # Summary Statistics
    st.markdown("---")
    st.subheader("📈 Summary Statistics")
    
    if not task_data.empty and 'Variance' in task_data.columns:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_variance = task_data['Variance'].mean()
            st.metric("Average Variance", f"{avg_variance:.1f} hours")
        
        with col2:
            over_budget_tasks = len(task_data[task_data['Actual_Hours'] > task_data['Estimated_Hours']]) # count of all task actual > estimate
            st.metric("Over Time Tasks", over_budget_tasks)
        
        with col3:
            under_budget_tasks = len(task_data[task_data['Actual_Hours'] < task_data['Estimated_Hours']]) # count of all task actual < estimate
            st.metric("Under Time Tasks", under_budget_tasks)
        
        with col4:
            if 'Foreman_Progress_%' in task_data.columns:
                avg_foreman_progress = task_data['Foreman_Progress_%'].mean()
                st.metric("Avg Foreman Progress", f"{avg_foreman_progress:.1f}%")
            else:
                st.metric("Avg Foreman Progress", "N/A")
        
        with col5:
            if 'Faster_or_Slower' in task_data.columns:
                faster_tasks = len(task_data[task_data['Faster_or_Slower'] == 'Faster'])
                slower_tasks = len(task_data[task_data['Faster_or_Slower'] == 'Slower'])
                on_track_tasks = len(task_data[task_data['Faster_or_Slower'] == 'On Track'])
                st.metric("Faster Tasks", faster_tasks)
                st.metric("Slower Tasks", slower_tasks)
                st.metric("On Track Tasks", on_track_tasks)
            else:
                st.metric("Progress Analysis", "N/A")
    
    # Additional AccuBid-specific statistics
    if not df.empty:
        st.subheader("📊 AccuBid Project Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Calculate total estimated hours from EVERYTHING tasks only
            everything_tasks = df[df['task_name'].str.contains('EVERYTHING', case=False, na=False)] if 'task_name' in df.columns else df
            total_estimated = everything_tasks['time_estimate'].sum() if 'time_estimate' in everything_tasks.columns and not everything_tasks.empty else 0
            st.metric("Total Estimated Hours (EVERYTHING)", f"{total_estimated:.1f}")
        
        with col2:
            unique_job_names = df['job_name'].dropna().unique().tolist()
            total_actual = 0
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
                    total_actual += total_times
                else:
                    total_actual += 0
            st.metric("Total Actual Hours", f"{total_actual:.1f}")
        
        with col3:
            if 'job_name' in df.columns:
                unique_jobs = df['job_name'].nunique()
                st.metric("Number of Jobs", unique_jobs)
            else:
                st.metric("Number of Jobs", "N/A")
        
        with col4:
            if 'task_name' in df.columns:
                # Count only EVERYTHING tasks
                everything_tasks = df[df['task_name'].str.contains('EVERYTHING', case=False, na=False)]
                unique_tasks = everything_tasks['task_name'].nunique() if not everything_tasks.empty else 0
                st.metric("Number of EVERYTHING Tasks", unique_tasks)
            else:
                st.metric("Number of EVERYTHING Tasks", "N/A")

if __name__ == "__main__":
    main()
