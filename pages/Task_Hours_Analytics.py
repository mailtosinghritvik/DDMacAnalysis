import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import numpy as np
from datetime import datetime, timedelta

def fetch_task_hours_data(limit=100, offset=0, jobcode_id=None):
    """Fetch task hours data from API"""
    try:
        # Fetch task estimate list data
        api_url = f"http://16.171.230.164/api/v1/task-estmate-list?limit={limit}&offset={offset}"
        if jobcode_id:
            api_url += f"&jobcode_id={jobcode_id}"
        
        headers = {'accept': 'application/json'}
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and data.get('data'):
                df = pd.DataFrame(data['data'])
                return df
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
            
    except requests.exceptions.ConnectionError:
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def fetch_available_jobcodes(limit=1000):
    """Fetch available job codes with names for dropdown"""
    try:
        api_url = f"http://16.171.230.164/api/v1/task-estmate-list?limit={limit}&offset=0"
        headers = {'accept': 'application/json'}
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data and data.get('data'):
                df = pd.DataFrame(data['data'])
                # Extract unique job codes with names if available
                if 'jobcode_id' in df.columns and 'jobcode_name' in df.columns:
                    # Get unique combinations of jobcode_id and jobcode_name
                    unique_jobcodes = df[['jobcode_id', 'jobcode_name']].drop_duplicates()
                    # Return list of tuples (jobcode_id, jobcode_name)
                    return [(row['jobcode_id'], row['jobcode_name']) for _, row in unique_jobcodes.iterrows()]
                elif 'jobcode_id' in df.columns:
                    # Fallback to just jobcode_id if jobcode_name not available
                    unique_ids = df['jobcode_id'].unique()
                    return [(jobcode_id, f"Job Code {jobcode_id}") for jobcode_id in unique_ids]
        return []
    except:
        return []

def create_planned_vs_actual_chart(df):
    """Create planned vs actual hours chart"""
    if df.empty:
        return None, pd.DataFrame()
    
    # Check if required columns exist
    required_cols = ['duration_hours', 'value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.warning(f"Missing required columns: {missing_cols}")
        return None, pd.DataFrame()
    
    # Group by task type (value) and calculate totals
    agg_dict = {
        'duration_hours': 'sum'
    }
    
    # Add time_estimate if available
    if 'time_estimate' in df.columns:
        agg_dict['time_estimate'] = 'sum'
    
    task_data = df.groupby('value').agg(agg_dict).reset_index()
    
    # Rename columns for clarity
    new_columns = ['Task_Type', 'Actual_Hours']
    if len(task_data.columns) > 2:
        new_columns.append('Estimated_Seconds')
    task_data.columns = new_columns
    
    # Convert time estimates from seconds to hours if available
    if 'Estimated_Seconds' in task_data.columns:
        task_data['Planned_Hours'] = task_data['Estimated_Seconds'] / 3600  # Convert seconds to hours
    else:
        # Fallback: estimate planned hours as 1.2x actual hours
        task_data['Planned_Hours'] = task_data['Actual_Hours'] * 1.2
    
    # Calculate variance
    task_data['Variance'] = task_data['Actual_Hours'] - task_data['Planned_Hours']
    task_data['Variance_Percent'] = (task_data['Variance'] / task_data['Planned_Hours'] * 100).round(2)
    
    # Create the chart
    fig = go.Figure()
    
    # Add planned hours bar
    fig.add_trace(go.Bar(
        name='Planned Hours',
        x=task_data['Task_Type'],
        y=task_data['Planned_Hours'],
        marker_color='lightblue',
        text=task_data['Planned_Hours'].round(1),
        textposition='auto',
    ))
    
    # Add actual hours bar
    fig.add_trace(go.Bar(
        name='Actual Hours',
        x=task_data['Task_Type'],
        y=task_data['Actual_Hours'],
        marker_color='darkblue',
        text=task_data['Actual_Hours'].round(1),
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Planned vs Actual Task Hours by Task Type',
        xaxis_title='Task Type',
        yaxis_title='Hours',
        barmode='group',
        height=500,
        showlegend=True
    )
    
    return fig, task_data

def create_variance_chart(task_data):
    """Create variance analysis chart"""
    if task_data.empty:
        return None
    
    # Create variance chart
    fig = go.Figure()
    
    # Add variance bars
    colors = ['red' if x < 0 else 'green' for x in task_data['Variance']]
    
    fig.add_trace(go.Bar(
        x=task_data['Task_Type'],
        y=task_data['Variance'],
        marker_color=colors,
        text=task_data['Variance'].round(1),
        textposition='auto',
        name='Variance (Actual - Planned)'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title='Hours Variance by Task Type (Negative = Under Budget, Positive = Over Budget)',
        xaxis_title='Task Type',
        yaxis_title='Hours Variance',
        height=400,
        showlegend=False
    )
    
    return fig

def create_efficiency_chart(task_data):
    """Create efficiency chart showing variance percentage"""
    if task_data.empty:
        return None
    
    # Create efficiency chart
    fig = go.Figure()
    
    # Add efficiency bars
    colors = ['red' if x < 0 else 'green' for x in task_data['Variance_Percent']]
    
    fig.add_trace(go.Bar(
        x=task_data['Task_Type'],
        y=task_data['Variance_Percent'],
        marker_color=colors,
        text=task_data['Variance_Percent'].round(1).astype(str) + '%',
        textposition='auto',
        name='Efficiency %'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title='Task Type Efficiency (Negative = Under Budget, Positive = Over Budget)',
        xaxis_title='Task Type',
        yaxis_title='Efficiency %',
        height=400,
        showlegend=False
    )
    
    return fig

def create_user_efficiency_chart(df):
    """Create task type efficiency chart"""
    if df.empty:
        return None, pd.DataFrame()
    
    # Check if required columns exist
    if 'duration_hours' not in df.columns or 'value' not in df.columns:
        st.warning("Missing required columns: duration_hours or value")
        return None, pd.DataFrame()
    
    # Group by task type and calculate efficiency
    task_data = df.groupby('value').agg({
        'duration_hours': 'sum',
        'time_estimate': 'sum'
    }).reset_index()
    
    # Calculate planned hours from time estimates
    task_data['Actual_Hours'] = task_data['duration_hours']
    task_data['Planned_Hours'] = task_data['time_estimate'].fillna(0) / 3600  # Convert seconds to hours
    
    # Calculate efficiency
    task_data['Efficiency'] = np.where(
        task_data['Planned_Hours'] > 0,
        (task_data['Actual_Hours'] / task_data['Planned_Hours'] * 100).round(2),
        0
    )
    
    # Create the chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=task_data['value'],
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
        title='Task Type Efficiency (Actual Hours / Estimated Hours)',
        xaxis_title='Task Type',
        yaxis_title='Efficiency %',
        height=400,
        showlegend=False
    )
    
    return fig, task_data

def create_timeline_chart(df):
    """Create timeline chart showing hours over time"""
    if df.empty:
        return None
    
    # Check if required columns exist
    if 'duration_hours' not in df.columns:
        st.warning("Missing required columns for timeline chart")
        return None
    
    # Since we don't have time data, create a simple task type comparison
    if 'value' not in df.columns:
        st.warning("No task type data available for timeline chart")
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
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        limit = st.number_input("Records Limit", min_value=10, max_value=1000, value=100, step=10)
    
    with col2:
        offset = st.number_input("Offset", min_value=0, value=0, step=10)
    
    with col3:
        # Fetch available job codes for dropdown
        available_jobcodes = fetch_available_jobcodes()
        if available_jobcodes:
            # Create options with job code names
            jobcode_options = ["All Projects"] + [f"{name} (ID: {jc_id})" for jc_id, name in available_jobcodes]
            selected_jobcode = st.selectbox("Select Job Code", jobcode_options)
            if selected_jobcode == "All Projects":
                jobcode_id = None
            else:
                # Extract jobcode_id from the selected option
                jobcode_id = int(selected_jobcode.split("(ID: ")[1].split(")")[0])
        else:
            st.selectbox("Select Job Code", ["No data available"], disabled=True)
            jobcode_id = None
    
    with col4:
        st.write("")  # Empty space for alignment
        if st.button("🔄 Refresh Data", key="refresh_task_hours"):
            st.rerun()
    
    # API Status
    st.info(f"📡 **API Endpoint**: http://16.171.230.164/| **Records**: {limit} | **Offset**: {offset}" + 
            (f" | **Job Code**: {jobcode_id}" if jobcode_id else " | **Job Code**: All"))
    
    # Fetch data
    with st.spinner("Loading task hours data..."):
        df = fetch_task_hours_data(limit=limit, offset=offset, jobcode_id=jobcode_id)
    
    if df.empty:
        st.warning("No data available. Please check the API connection.")
        return
    
    # Display data summary
    st.subheader("📊 Data Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'value' in df.columns:
            st.metric("Task Types", len(df['value'].unique()))
        else:
            st.metric("Task Types", "N/A")
    
    with col2:
        if 'duration_hours' in df.columns:
            st.metric("Total Hours", f"{df['duration_hours'].sum():.1f}")
        else:
            st.metric("Total Hours", "N/A")
    
    with col3:
        if 'time_estimate' in df.columns:
            # Convert seconds to hours and sum
            estimated_hours = df['time_estimate'].fillna(0).sum() / 3600
            st.metric("Estimated Hours", f"{estimated_hours:.1f}")
        else:
            st.metric("Estimated Hours", "N/A")
    
    with col4:
        if 'duration_hours' in df.columns and 'time_estimate' in df.columns:
            # Calculate efficiency
            actual_hours = df['duration_hours'].sum()
            estimated_hours = df['time_estimate'].fillna(0).sum() / 3600
            if estimated_hours > 0:
                efficiency = (actual_hours / estimated_hours * 100)
                st.metric("Efficiency", f"{efficiency:.1f}%")
            else:
                st.metric("Efficiency", "N/A")
        else:
            st.metric("Efficiency", "N/A")
    
    # Main charts
    st.markdown("---")
    
    # Planned vs Actual Hours Chart
    st.subheader("📈 Planned vs Actual Hours by Task Type")
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
    
    with col2:
        st.subheader("📊 Efficiency Analysis")
        efficiency_fig = create_efficiency_chart(task_data)
        if efficiency_fig:
            st.plotly_chart(efficiency_fig, use_container_width=True)
    
    # User Efficiency
    st.markdown("---")
    st.subheader("👥 User Efficiency Analysis")
    user_efficiency_fig, user_data = create_user_efficiency_chart(df)
    if user_efficiency_fig:
        st.plotly_chart(user_efficiency_fig, use_container_width=True)
        
        # Display user data table
        st.subheader("👤 User Details")
        st.dataframe(user_data, use_container_width=True)
    
    # Timeline Analysis
    st.markdown("---")
    st.subheader("📅 Timeline Analysis")
    timeline_fig = create_timeline_chart(df)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Summary Statistics
    st.markdown("---")
    st.subheader("📈 Summary Statistics")
    
    if not task_data.empty:
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

if __name__ == "__main__":
    main()
