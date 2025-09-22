import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import requests
import json

# Import dual data source utilities
from utils import (
    # Original functions
    analyze_all_projects,
    analyze_projects_for_client,
    get_project_health_metrics,
    TimeTrackingAnalyzer,
    
    # API functions
    get_api_handler,
    analyze_projects_for_client_api,
    analyze_project_details_api,
    
    # Estimates functions
    get_estimates_handler,
    get_progress_comparison,
    get_budget_alerts
)

# Set page configuration
st.set_page_config(
    page_title="Project Analytics - DDMac",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS for project analytics with dual data sources
st.markdown("""
<style>
    .project-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .project-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
        margin: 0.5rem 0;
    }
    
    .risk-high { 
        border-left-color: #dc3545;
        background: #f8d7da;
    }
    
    .risk-medium { 
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    
    .risk-low { 
        border-left-color: #28a745;
        background: #d4edda;
    }
    
    .progress-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .budget-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .timeline-card {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 10px;
        color: #333;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def fetch_client_time_summary_direct(page=1, limit=1000):
    """Make direct API call to fetch client time summary data"""
    try:
        api_url = "http://16.171.230.164/api/v1/client-time-summary"
        params = {
            "page": page,
            "limit": limit
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Add pagination info if not present
        if 'total_pages' not in data:
            total = data.get('total', 0)
            data['total_pages'] = (total + limit - 1) // limit if total > 0 else 0
        
        return data
        
    except requests.exceptions.RequestException as e:
        st.error(f"API request error: {str(e)}")
        return {"total": 0, "data": [], "page": page-1, "limit": limit, "total_pages": 0}
    except Exception as e:
        st.error(f"Error fetching API data: {str(e)}")
        return {"total": 0, "data": [], "page": page-1, "limit": limit, "total_pages": 0}

def safe_format_date(date_value):
    """Safely format date values, handling empty strings, None values, and invalid dates"""
    # Handle None, empty string, or non-string types
    if pd.isna(date_value) or date_value == '' or date_value is None:
        return ''
    
    # Handle non-string types (like lists, dicts, etc.)
    if not isinstance(date_value, str):
        return ''
    
    try:
        # Convert to datetime
        dt = pd.to_datetime(date_value, errors='coerce')
        if pd.isna(dt):
            return ''
        return dt.strftime('%Y-%m-%d')
    except:
        return ''

def fetch_client_user_data_direct(jobcode_id, user_id=None, page=1, limit=50):
    """Make direct API call to fetch client user data"""
    try:
        api_url = f"http://16.171.230.164/api/v1/client-user-data/{jobcode_id}"
        params = {
            "page": page,
            "limit": limit
        }
        
        if user_id:
            params["user_id"] = user_id
        
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Add pagination info if not present
        if 'total_pages' not in data:
            total = data.get('total', 0)
            data['total_pages'] = (total + limit - 1) // limit if total > 0 else 0
        
        return data
        
    except requests.exceptions.RequestException as e:
        st.error(f"API request error: {str(e)}")
        return {"total": 0, "data": [], "page": page, "limit": limit, "total_pages": 0}
    except Exception as e:
        st.error(f"Error fetching client user data: {str(e)}")
        return {"total": 0, "data": [], "page": page, "limit": limit, "total_pages": 0}

def analyze_team_allocation_direct(client_data):
    """Analyze team allocation from client time summary data directly"""
    if not client_data or not client_data.get('data'):
        return pd.DataFrame(columns=['Client', 'Total_Hours', 'Days_Worked', 'Avg_Hours_Per_Day', 'Efficiency_Score', 'Status', 'Jobcode_ID', 'User_ID'])
    
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

def get_project_data():
    """Fetch project data from both API and estimates sources"""
    api_data = None
    estimates_data = None
    progress_data = None
    alerts_data = None
    
    try:
        # Make direct API call to fetch client time summary data
        client_time_summary = fetch_client_time_summary_direct(page=1, limit=50)
        
        # Analyze team allocation data directly
        team_allocation = analyze_team_allocation_direct(client_time_summary)
        
        # Create comprehensive API data structure
        api_data = {
            'client_time_summary': client_time_summary,
            'team_allocation': team_allocation,
            'active_projects': client_time_summary.get('total', 0),
            'total_hours': sum(item.get('total_duration', 0) for item in client_time_summary.get('data', []) if item.get('total_duration')),
            'total_clients': len(client_time_summary.get('data', [])),
            'efficiency': team_allocation['Efficiency_Score'].mean() if not team_allocation.empty else 0
        }
        
        # Get estimates data
        estimates_handler = get_estimates_handler()
        estimates_data = estimates_handler.get_sample_data()
        
        # Generate progress comparison (skip if estimates data has issues)
        try:
            if api_data and estimates_data:
                progress_data = get_progress_comparison(api_data, estimates_data)
                alerts_data = get_budget_alerts(progress_data)
        except Exception as e:
            # Don't show warning for estimates data issues, just skip silently
            progress_data = None
            alerts_data = None
    
    except Exception as e:
        # Don't show error message, just return minimal data structure
        api_data = {
            'client_time_summary': {"total": 0, "data": []},
            'team_allocation': pd.DataFrame(),
            'active_projects': 0,
            'total_hours': 0,
            'total_clients': 0,
            'efficiency': 0
        }
    
    return api_data, estimates_data, progress_data, alerts_data

def create_project_progress_timeline(progress_data):
    """Create project progress timeline chart"""
    if not progress_data:
        return None
    
    timeline_data = []
    for p in progress_data:
        # Calculate progress percentage
        progress_pct = (p['actual_hours'] / p['estimated_hours'] * 100) if p['estimated_hours'] > 0 else 0
        
        timeline_data.append({
            'Project': p['project_name'],
            'Progress %': min(progress_pct, 100),
            'Status': p.get('status', 'Unknown'),
            'Estimated Hours': p['estimated_hours'],
            'Actual Hours': p['actual_hours']
        })
    
    df = pd.DataFrame(timeline_data)
    
    # Create horizontal bar chart
    fig = px.bar(
        df,
        x='Progress %',
        y='Project',
        color='Status',
        orientation='h',
        title='Project Progress Overview',
        color_discrete_map={
            'On Track': '#28a745',
            'At Risk': '#ffc107',
            'Delayed': '#dc3545',
            'Completed': '#17a2b8'
        }
    )
    
    # Add 100% reference line
    fig.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="Target")
    
    fig.update_layout(height=400, xaxis_title="Progress Percentage")
    return fig

def create_project_budget_analysis(progress_data):
    """Create project budget analysis chart"""
    if not progress_data:
        return None
    
    budget_data = []
    for p in progress_data:
        if p.get('budget', 0) > 0:
            utilization = (p.get('actual_cost', 0) / p['budget']) * 100
            budget_data.append({
                'Project': p['project_name'],
                'Budget': p['budget'],
                'Spent': p.get('actual_cost', 0),
                'Remaining': max(0, p['budget'] - p.get('actual_cost', 0)),
                'Utilization %': utilization,
                'Status': 'Over Budget' if utilization > 100 else 'On Track' if utilization <= 90 else 'Caution'
            })
    
    if not budget_data:
        return None
    
    df = pd.DataFrame(budget_data)
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Spent',
        x=df['Project'],
        y=df['Spent'],
        marker_color='#dc3545'
    ))
    
    fig.add_trace(go.Bar(
        name='Remaining',
        x=df['Project'],
        y=df['Remaining'],
        marker_color='#28a745'
    ))
    
    fig.update_layout(
        title='Project Budget Utilization',
        xaxis_title='Projects',
        yaxis_title='Budget ($)',
        barmode='stack',
        height=400
    )
    
    return fig, df

def create_project_risk_matrix(progress_data):
    """Create project risk assessment matrix"""
    if not progress_data:
        return None
    
    risk_data = []
    for p in progress_data:
        # Calculate risk factors
        budget_risk = (p.get('actual_cost', 0) / p.get('budget', 1)) if p.get('budget', 0) > 0 else 0
        schedule_risk = (p['actual_hours'] / p['estimated_hours']) if p['estimated_hours'] > 0 else 0
        
        # Risk scoring (0-10 scale)
        budget_score = min(10, budget_risk * 10)
        schedule_score = min(10, schedule_risk * 10)
        
        risk_data.append({
            'Project': p['project_name'],
            'Budget Risk': budget_score,
            'Schedule Risk': schedule_score,
            'Overall Risk': (budget_score + schedule_score) / 2,
            'Status': p.get('status', 'Unknown')
        })
    
    df = pd.DataFrame(risk_data)
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='Budget Risk',
        y='Schedule Risk',
        size='Overall Risk',
        color='Status',
        hover_data=['Project'],
        title='Project Risk Matrix',
        labels={
            'Budget Risk': 'Budget Risk (0-10)',
            'Schedule Risk': 'Schedule Risk (0-10)'
        }
    )
    
    # Add risk zones
    fig.add_shape(type="rect", x0=0, y0=0, x1=5, y1=5, 
                  fillcolor="green", opacity=0.2, line_width=0)
    fig.add_shape(type="rect", x0=5, y0=5, x1=10, y1=10, 
                  fillcolor="red", opacity=0.2, line_width=0)
    
    fig.update_layout(height=400)
    return fig, df

def create_project_team_allocation(team_allocation_data):
    """Create project team allocation chart using real API data"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None, None
    
    # Create efficiency vs hours scatter plot
    fig = px.scatter(
        team_allocation_data,
        x='Total_Hours',
        y='Efficiency_Score',
        size='Days_Worked',
        color='Status',
        hover_data=['Client', 'Avg_Hours_Per_Day', 'Days_Worked'],
        title='Team Allocation: Efficiency vs Total Hours Analysis',
        labels={
            'Total_Hours': 'Total Hours',
            'Efficiency_Score': 'Efficiency Score (%)',
            'Days_Worked': 'Days Worked'
        },
        color_discrete_map={
            'High Performance': '#28a745',
            'Good Performance': '#17a2b8',
            'Average Performance': '#ffc107',
            'Low Performance': '#dc3545'
        }
    )
    
    # Add efficiency reference lines
    fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="High Performance (80%)")
    fig.add_hline(y=60, line_dash="dash", line_color="blue", annotation_text="Good Performance (60%)")
    fig.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text="Average Performance (40%)")
    
    # Improve layout
    fig.update_layout(
        height=600,
        xaxis_title="Total Hours (Log Scale)",
        yaxis_title="Efficiency Score (%)",
        xaxis=dict(type="log"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig, team_allocation_data

def create_team_allocation_summary_chart(team_allocation_data):
    """Create team allocation summary bar chart"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    # Group by status and calculate metrics
    status_summary = team_allocation_data.groupby('Status').agg({
        'Total_Hours': 'sum',
        'Client': 'count',
        'Efficiency_Score': 'mean'
    }).reset_index()
    
    status_summary.columns = ['Status', 'Total_Hours', 'Client_Count', 'Avg_Efficiency']
    
    # Create horizontal bar chart
    fig = px.bar(
        status_summary,
        x='Total_Hours',
        y='Status',
        color='Status',
        orientation='h',
        title='Team Allocation Summary by Performance Status',
        labels={
            'Total_Hours': 'Total Hours',
            'Status': 'Performance Status'
        },
        color_discrete_map={
            'High Performance': '#28a745',
            'Good Performance': '#17a2b8',
            'Average Performance': '#ffc107',
            'Low Performance': '#dc3545'
        }
    )
    
    # Add client count and efficiency as text annotations
    for i, row in status_summary.iterrows():
        fig.add_annotation(
            x=row['Total_Hours'] + max(status_summary['Total_Hours']) * 0.01,
            y=row['Status'],
            text=f"{int(row['Client_Count'])} clients<br>Avg: {row['Avg_Efficiency']:.1f}%",
            showarrow=False,
            font=dict(size=10),
            align="left"
        )
    
    # Add percentage annotations
    total_hours = status_summary['Total_Hours'].sum()
    for i, row in status_summary.iterrows():
        pct = (row['Total_Hours'] / total_hours) * 100
        fig.add_annotation(
            x=row['Total_Hours'] / 2,
            y=row['Status'],
            text=f"{pct:.1f}%",
            showarrow=False,
            font=dict(size=12, color="white", family="Arial Black"),
            align="center"
        )
    
    fig.update_layout(
        height=400,
        xaxis_title="Total Hours",
        yaxis_title="Performance Status",
        showlegend=False
    )
    return fig

def create_client_hours_distribution(team_allocation_data):
    """Create client hours distribution pie chart"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    # Get top 10 clients by hours
    top_clients = team_allocation_data.nlargest(10, 'Total_Hours')
    
    fig = px.pie(
        top_clients,
        values='Total_Hours',
        names='Client',
        title='Top 10 Clients by Total Hours',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    return fig

def create_efficiency_distribution_chart(team_allocation_data):
    """Create efficiency distribution histogram"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    fig = px.histogram(
        team_allocation_data,
        x='Efficiency_Score',
        nbins=20,
        title='Efficiency Score Distribution',
        labels={'Efficiency_Score': 'Efficiency Score (%)', 'count': 'Number of Clients'},
        color_discrete_sequence=['#17a2b8']
    )
    
    # Add efficiency reference lines
    fig.add_vline(x=80, line_dash="dash", line_color="green", annotation_text="High (80%)")
    fig.add_vline(x=60, line_dash="dash", line_color="blue", annotation_text="Good (60%)")
    fig.add_vline(x=40, line_dash="dash", line_color="orange", annotation_text="Avg (40%)")
    
    fig.update_layout(height=400)
    return fig

def create_hours_vs_days_chart(team_allocation_data):
    """Create hours vs days worked scatter plot"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    fig = px.scatter(
        team_allocation_data,
        x='Days_Worked',
        y='Total_Hours',
        size='Efficiency_Score',
        color='Status',
        hover_data=['Client', 'Avg_Hours_Per_Day'],
        title='Hours vs Days Worked Analysis',
        labels={
            'Days_Worked': 'Days Worked',
            'Total_Hours': 'Total Hours',
            'Efficiency_Score': 'Efficiency Score'
        },
        color_discrete_map={
            'High Performance': '#28a745',
            'Good Performance': '#17a2b8',
            'Average Performance': '#ffc107',
            'Low Performance': '#dc3545'
        }
    )
    
    fig.update_layout(height=400)
    return fig

def display_project_kpis(api_data, estimates_data, progress_data):
    """Display project-level KPIs using client time summary data"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Get client time summary data
    client_data = api_data.get('client_time_summary', {}) if api_data else {}
    client_records = client_data.get('data', []) if client_data else []
    
    with col1:
        # Count unique jobcode_ids as active projects
        if client_records:
            active_projects = len(set([record.get('jobcode_id') for record in client_records if record.get('jobcode_id')]))
            st.metric("Active Projects", active_projects)
        else:
            st.metric("Active Projects", 0)
    
    with col2:
        # For now, we don't have completion status in the API, so show N/A
        st.metric("Completed Projects", "N/A")
    
    with col3:
        # Calculate total duration as a proxy for budget/work
        if client_records:
            total_duration = sum([record.get('total_duration', 0) for record in client_records])
            st.metric("Total Hours", f"{total_duration:,.1f}")
        else:
            st.metric("Total Hours", "N/A")
    
    with col4:
        # Calculate average duration per project
        if client_records:
            project_durations = {}
            for record in client_records:
                jobcode_id = record.get('jobcode_id')
                duration = record.get('total_duration', 0)
                if jobcode_id in project_durations:
                    project_durations[jobcode_id] += duration
                else:
                    project_durations[jobcode_id] = duration
            
            if project_durations:
                avg_duration = sum(project_durations.values()) / len(project_durations)
                st.metric("Avg Hours/Project", f"{avg_duration:.1f}")
            else:
                st.metric("Avg Hours/Project", "N/A")
        else:
            st.metric("Avg Hours/Project", "N/A")
    
    with col5:
        # Count unique users as team size
        if client_records:
            unique_users = len(set([record.get('user_id') for record in client_records if record.get('user_id')]))
            st.metric("Active Users", unique_users)
        else:
            st.metric("Active Users", 0)

def main():
    """Main Project Analytics Dashboard"""
    
    # Header
    st.markdown("""
    <div class="project-header">
        <h1>🚀 Project Analytics Dashboard</h1>
        <p>Comprehensive Project Performance, Budget Tracking & Risk Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch project data
    with st.spinner("Loading project analytics..."):
        api_data, estimates_data, progress_data, alerts_data = get_project_data()
    
    # Display KPIs
    st.subheader("📊 Project Performance KPIs")
    display_project_kpis(api_data, estimates_data, progress_data)
    
    # Main Analytics Tabs
    tab5, tab6 = st.tabs([
     
        "📊 API Data View",
        "🔍 Project & Client Explorer"
    ])
    
    
    with tab6:
        st.subheader("🔍 Project & Client Explorer")
        
        # Always load fresh data for Project & Client Explorer
        available_projects = []
        available_clients = []
        
        try:
            with st.spinner("Loading project data..."):
                client_data = fetch_client_time_summary_direct(page=1, limit=100)
                
                
                if client_data and client_data.get('data'):
                    for item in client_data['data']:
                        if item.get('name'):
                            available_clients.append(item['name'])
                        if item.get('jobcode_id'):
                            available_projects.append({
                                'name': item.get('name', 'Unknown'),
                                'jobcode_id': item.get('jobcode_id'),
                                'total_duration': item.get('total_duration', 0)
                            })
                else:
                    st.warning("No data received from API or data array is empty")
        except Exception as e:
            st.error(f"Could not load project data: {str(e)}")
        
        # Add refresh button
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write("**Select Project/Client:**")
        
        with col2:
            if st.button("🔄 Refresh Data", type="secondary"):
                st.rerun()
        
        with col3:
            st.write(f"**{len(available_projects)} projects available**")
        
    
        
        # Create dropdown
        if available_projects:
            # Create a list of project names for the dropdown
            project_names = [f"{p['name']} (ID: {p['jobcode_id']})" for p in available_projects]
            selected_project = st.selectbox(
                "Choose a project/client:",
                options=[""] + project_names,
                index=0,
                help="Select a project/client to view detailed information"
            )
        else:
            st.warning("No projects available. Please refresh the data or check your connection.")
            selected_project = None
        
        # View options section
        st.write("**View Options:**")
        view_type = st.radio(
            "What would you like to see?",
            ["📊 Summary Data", "👥 User Details", "📅 Timesheet Data"],
            horizontal=True
        )
        
        # Process selection and display data
        if selected_project and selected_project != "":
            # Extract jobcode_id from selection
            try:
                jobcode_id = int(selected_project.split("(ID: ")[1].split(")")[0])
                project_name = selected_project.split(" (ID:")[0]
                
                st.markdown("---")
                st.subheader(f"📋 Data for: {project_name}")
                
                # Display based on view type
                if view_type == "📊 Summary Data":
                    # Show project summary
                    project_info = next((p for p in available_projects if p['jobcode_id'] == jobcode_id), None)
                    client_time_summary_client_data = fetch_client_time_summary_direct(page=1, limit=1000)
                    if project_info:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Project Name", project_name)
                        
                        with col2:
                            st.metric("Job Code ID", jobcode_id)
                        
                        with col3:
                            total_duration = project_info.get('total_duration', 0)
                            if total_duration is None:
                                total_duration = 0
                            st.metric("Total Duration", f"{total_duration:.1f} hours")
                        
                        with col4:
                            # Calculate efficiency if we have days worked
                            total_duration = project_info.get('total_duration', 0)
                            if total_duration is None:
                                total_duration = 0
                            days_worked = next((item.get('days_worked', 0) for item in client_time_summary_client_data['data'] if item.get('jobcode_id') == jobcode_id), 0)
                            avg_hours = total_duration / days_worked if days_worked > 0 else 0
                            st.metric("Avg Hours/Day", f"{avg_hours:.1f}")
                        
                        # Show project timeline
                        st.subheader("📈 Project Timeline")
                        timeline_data = {
                            'Metric': ['Total Duration', 'Days Worked', 'Average Hours/Day', 'Efficiency Score'],
                            'Value': [
                                f"{total_duration:.1f} hours",
                                f"{days_worked:.0f} days",
                                f"{avg_hours:.1f} hours",
                                f"{(avg_hours/8*100):.1f}%" if avg_hours > 0 else "0%"
                            ]
                        }
                        
                        timeline_df = pd.DataFrame(timeline_data)
                        st.dataframe(timeline_df, use_container_width=True, hide_index=True)
                
                elif view_type == "👥 User Details":
                    # Show user details for this project
                    st.subheader("👥 Users Working on This Project")
                    
                    with st.spinner("Fetching user data..."):
                        user_data = fetch_client_user_data_direct(
                            jobcode_id=jobcode_id,
                            page=1,
                            limit=100
                        )
                    
                    if user_data and user_data.get('data'):
                        # Get unique users
                        users_df = pd.DataFrame(user_data['data'])
                        unique_users = users_df.groupby('username').agg({
                            'user_id': 'first',
                            'total_duration': 'sum',
                            'days_worked': 'first'
                        }).reset_index()
                        
                        unique_users.columns = ['Username', 'User ID', 'Total Hours', 'Work Days']
                        unique_users['Avg Hours/Day'] = unique_users['Total Hours'] / unique_users['Work Days']
                        unique_users['Efficiency %'] = (unique_users['Avg Hours/Day'] / 8 * 100).clip(0, 100)
                        
                        # Round numeric columns
                        numeric_cols = ['Total Hours', 'Avg Hours/Day', 'Efficiency %']
                        for col in numeric_cols:
                            unique_users[col] = unique_users[col].round(2)
                        
                        # Add performance status
                        def get_user_status(efficiency):
                            if efficiency >= 80:
                                return "High Performance"
                            elif efficiency >= 60:
                                return "Good Performance"
                            elif efficiency >= 40:
                                return "Average Performance"
                            else:
                                return "Low Performance"
                        
                        unique_users['Status'] = unique_users['Efficiency %'].apply(get_user_status)
                        
                        # Display user summary
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Users", len(unique_users))
                        
                        with col2:
                            total_hours = unique_users['Total Hours'].sum()
                            st.metric("Total Hours", f"{total_hours:.1f}")
                        
                        with col3:
                            avg_efficiency = unique_users['Efficiency %'].mean()
                            st.metric("Avg Efficiency", f"{avg_efficiency:.1f}%")
                        
                        # Display users table with selection capability
                        st.subheader("👥 Select a User for Detailed Analysis")
                        selected_indices = st.dataframe(
                            unique_users,
                            use_container_width=True,
                            height=300,
                            on_select="rerun",
                            selection_mode="single-row"
                        )
                        
                        # Handle user selection for detailed data
                        if selected_indices.selection.rows:
                            selected_row_idx = selected_indices.selection.rows[0]
                            selected_user_row = unique_users.iloc[selected_row_idx]
                            selected_user_id = selected_user_row['User ID']
                            selected_username = selected_user_row['Username']
                            
                            st.markdown("---")
                            st.subheader(f"🔍 Detailed Analysis for {selected_username}")
                            
                            # Fetch detailed data for the selected user
                            with st.spinner(f"Fetching detailed data for {selected_username}..."):
                                detailed_user_data = fetch_client_user_data_direct(
                                    jobcode_id=jobcode_id,
                                    user_id=selected_user_id,
                                    page=1,
                                    limit=100
                                )
                            
                            # Add API logging
                            st.subheader("📡 API Call Information")
                            api_url = f"http://16.171.230.164/api/v1/client-user-data/{jobcode_id}?page=1&limit=100&user_id={selected_user_id}"
                            
                            if detailed_user_data and detailed_user_data.get('data'):
                                # Display detailed metrics
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Total Entries", detailed_user_data.get('total', 0))
                                
                                with col2:
                                    total_duration = sum(entry.get('total_duration', 0) for entry in detailed_user_data['data'])
                                    st.metric("Total Duration", f"{total_duration:.1f} hours")
                                
                                with col3:
                                    avg_duration = total_duration / len(detailed_user_data['data']) if detailed_user_data['data'] else 0
                                    st.metric("Avg Duration/Entry", f"{avg_duration:.1f} hours")
                                
                                with col4:
                                    unique_dates = len(set(entry.get('start_date', '') for entry in detailed_user_data['data']))
                                    st.metric("Work Days", f"{unique_dates:.0f} days")
                                
                                # Display detailed timesheet data
                                st.subheader("📅 Detailed Timesheet Entries")
                                
                                # Add view options
                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    st.write("**View Options:**")
                                with col2:
                                    view_mode = st.radio(
                                        "Data View:",
                                        ["📅 Daily", "📊 Weekly", "📋 All Data"],
                                        horizontal=True,
                                        key=f"view_mode_{selected_user_id}"
                                    )
                                with col3:
                                    if st.button("🔄 Refresh Data", key=f"refresh_user_detail_{selected_user_id}"):
                                        # Clear all cached data and force refresh
                                        keys_to_clear = [key for key in st.session_state.keys() if f"user_detail_data_{selected_user_id}" in key or f"timesheet_data_{jobcode_id}" in key or f"user_detail_table_{selected_user_id}" in key]
                                        for key in keys_to_clear:
                                            del st.session_state[key]
                                        # Force a complete page refresh
                                        st.cache_data.clear()
                                        st.rerun()
                                
                                # Convert to DataFrame for better display
                                detailed_df = pd.DataFrame(detailed_user_data['data'])
                                
                                # Format the data for better readability
                                if not detailed_df.empty:
                                    # Clean and format date columns - ensure they contain only strings
                                    for col in ['work_date', 'start_date', 'end_date']:
                                        if col in detailed_df.columns:
                                            # Convert non-string values to empty string
                                            detailed_df[col] = detailed_df[col].astype(str).replace('nan', '').replace('None', '')
                                    
                                    # Use work_date as the primary date column if available, otherwise use start_date
                                    if 'work_date' in detailed_df.columns:
                                        detailed_df['work_date'] = detailed_df['work_date'].apply(safe_format_date)
                                        date_col = 'work_date'
                                    else:
                                        # Use start_date as the primary date column
                                        detailed_df['start_date'] = detailed_df['start_date'].apply(safe_format_date)
                                        date_col = 'start_date'
                                        # Create work_date from start_date for consistency
                                        detailed_df['work_date'] = detailed_df['start_date']
                                    
                                    # Format other dates
                                    if 'start_date' in detailed_df.columns:
                                        detailed_df['start_date'] = detailed_df['start_date'].apply(safe_format_date)
                                    if 'end_date' in detailed_df.columns:
                                        detailed_df['end_date'] = detailed_df['end_date'].apply(safe_format_date)
                                    
                                    # Round duration and handle any remaining None values
                                    detailed_df['total_duration'] = detailed_df['total_duration'].fillna(0)
                                    detailed_df['total_duration'] = detailed_df['total_duration'].round(2)
                                    
                                    # Apply view mode processing
                                    if view_mode == "📊 Weekly":
                                        # Group by week and aggregate
                                        detailed_df['date_dt'] = pd.to_datetime(detailed_df[date_col], errors='coerce')
                                        if not detailed_df['date_dt'].isna().all():
                                            # Group by week
                                            detailed_df['week_start'] = detailed_df['date_dt'].dt.to_period('W').dt.start_time
                                            weekly_data = detailed_df.groupby('week_start').agg({
                                                'total_duration': 'sum'
                                            }).reset_index()
                                            
                                            # Format for display
                                            weekly_data['work_date'] = weekly_data['week_start'].dt.strftime('%Y-%m-%d')
                                            weekly_data['end_date'] = (weekly_data['week_start'] + pd.Timedelta(days=6)).dt.strftime('%Y-%m-%d')
                                            detailed_df = weekly_data[['work_date', 'end_date', 'total_duration']].copy()
                                    
                                    # For Daily and All Data views, show individual records
                                    if view_mode in ["📅 Daily", "📋 All Data"]:
                                        # Sort by work_date for better display
                                        if 'work_date' in detailed_df.columns:
                                            detailed_df = detailed_df.sort_values('work_date', ascending=False)
                                        
                                        # Create display dataframe with individual records
                                        if 'work_date' in detailed_df.columns:
                                            display_columns = ['work_date', 'total_duration']
                                            if 'end_date' in detailed_df.columns:
                                                display_columns.insert(1, 'end_date')
                                            user_display = detailed_df[display_columns].copy()
                                            user_display.columns = ['Work Date', 'End Date', 'Duration (hrs)'] if 'end_date' in detailed_df.columns else ['Work Date', 'Duration (hrs)']
                                        else:
                                            # Fallback to start_date/end_date
                                            display_columns = ['start_date', 'total_duration']
                                            if 'end_date' in detailed_df.columns:
                                                display_columns.insert(1, 'end_date')
                                            user_display = detailed_df[display_columns].copy()
                                            user_display.columns = ['Start Date', 'End Date', 'Duration (hrs)'] if 'end_date' in detailed_df.columns else ['Start Date', 'Duration (hrs)']
                                    else:
                                        # For Weekly view, use the aggregated data
                                        if 'work_date' in detailed_df.columns:
                                            display_columns = ['work_date', 'total_duration']
                                            if 'end_date' in detailed_df.columns:
                                                display_columns.insert(1, 'end_date')
                                            user_display = detailed_df[display_columns].copy()
                                            user_display.columns = ['Work Date', 'End Date', 'Duration (hrs)'] if 'end_date' in detailed_df.columns else ['Work Date', 'Duration (hrs)']
                                        else:
                                            # Fallback to start_date/end_date
                                            display_columns = ['start_date', 'total_duration']
                                            if 'end_date' in detailed_df.columns:
                                                display_columns.insert(1, 'end_date')
                                            user_display = detailed_df[display_columns].copy()
                                            user_display.columns = ['Start Date', 'End Date', 'Duration (hrs)'] if 'end_date' in detailed_df.columns else ['Start Date', 'Duration (hrs)']
                                    
                                    # Add work status
                                    if 'Duration (hrs)' in user_display.columns:
                                        def get_work_status(duration):
                                            if view_mode == "📊 Weekly":
                                                # For weekly view, adjust thresholds
                                                if duration >= 40:  # 5 days * 8 hours
                                                    return "Full Week"
                                                elif duration >= 30:  # 5 days * 6 hours
                                                    return "Good Week"
                                                elif duration >= 20:  # 5 days * 4 hours
                                                    return "Partial Week"
                                                else:
                                                    return "Light Week"
                                            else:
                                                # For daily view
                                                if duration >= 8:
                                                    return "Full Day"
                                                elif duration >= 6:
                                                    return "Good Day"
                                                elif duration >= 4:
                                                    return "Partial Day"
                                                else:
                                                    return "Short Day"
                                        
                                        user_display['Status'] = user_display['Duration (hrs)'].apply(get_work_status)
                                        
                                        # Add color coding for duration status
                                        def highlight_work_status(row):
                                            colors = {
                                                # Daily statuses
                                                'Full Day': 'background-color: #d4edda; color: #155724;',
                                                'Good Day': 'background-color: #d1ecf1; color: #0c5460;',
                                                'Partial Day': 'background-color: #fff3cd; color: #856404;',
                                                'Short Day': 'background-color: #f8d7da; color: #721c24;',
                                                # Weekly statuses
                                                'Full Week': 'background-color: #d4edda; color: #155724;',
                                                'Good Week': 'background-color: #d1ecf1; color: #0c5460;',
                                                'Partial Week': 'background-color: #fff3cd; color: #856404;',
                                                'Light Week': 'background-color: #f8d7da; color: #721c24;'
                                            }
                                            return [colors.get(row['Status'], '')] * len(row)
                                        
                                        styled_user = user_display.style.apply(highlight_work_status, axis=1)
                                        styled_user = styled_user.format({'Duration (hrs)': '{:.1f}'})
                                        
                                        # Display view information                                        
                                        # Debug information
                                        if st.checkbox("Show Raw Data Debug", value=False, key=f"debug_user_data_{selected_user_id}"):
                                            st.write("**Raw user_display data:**")
                                            st.write(user_display.head(10))
                                            st.write("**Data types:**")
                                            st.write(user_display.dtypes)
                                            st.write("**Null values:**")
                                            st.write(user_display.isnull().sum())
                                        
                                        # Display the styled dataframe with unique key
                                        import time
                                        table_key = f"user_detail_table_{selected_user_id}_{len(user_display)}_{view_mode}_{int(time.time())}"
                                        st.dataframe(
                                            styled_user,
                                            use_container_width=True,
                                            height=400,
                                            key=table_key
                                        )
                                    else:
                                        import time
                                        table_key = f"user_detail_table_{selected_user_id}_{len(user_display)}_{view_mode}_{int(time.time())}"
                                        st.dataframe(
                                            user_display, 
                                            use_container_width=True, 
                                            height=400,
                                            key=table_key
                                        )
                                    
                                    
                                    # Show pagination info
                                    if detailed_user_data.get('total_pages', 0) > 1:
                                        st.write(f"📄 **Pagination**: Page {detailed_user_data.get('page', 1)} of {detailed_user_data.get('total_pages', 1)} (Total: {detailed_user_data.get('total', 0)} entries)")
                                    
                                    # Additional insights
                                    st.subheader("📈 User Performance Insights")
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write("**Work Pattern Analysis:**")
                                        if 'Duration (hrs)' in user_display.columns:
                                            avg_daily_hours = user_display['Duration (hrs)'].mean()
                                            max_daily_hours = user_display['Duration (hrs)'].max()
                                            min_daily_hours = user_display['Duration (hrs)'].min()
                                            
                                            st.write(f"• Average daily hours: {avg_daily_hours:.1f}")
                                            st.write(f"• Maximum daily hours: {max_daily_hours:.1f}")
                                            st.write(f"• Minimum daily hours: {min_daily_hours:.1f}")
                                    
                                    with col2:
                                        st.write("**Work Status Breakdown:**")
                                        if 'Status' in user_display.columns:
                                            status_counts = user_display['Status'].value_counts()
                                            for status, count in status_counts.items():
                                                pct = (count / len(user_display)) * 100
                                                st.write(f"• {status}: {count} days ({pct:.1f}%)")
                             
                
                elif view_type == "📅 Timesheet Data":
                    # Show detailed timesheet data
                    st.subheader("📅 Detailed Timesheet Data")
                    
                    # Add user selection if multiple users
                    with st.spinner("Fetching timesheet data..."):
                        user_data = fetch_client_user_data_direct(
                            jobcode_id=jobcode_id,
                            page=1,
                            limit=100
                        )
                    
                    if user_data and user_data.get('data'):
                        users_df = pd.DataFrame(user_data['data'])
                        unique_users = users_df['username'].unique().tolist()
                        
                        # Only show user selection if there are multiple users
                        if len(unique_users) > 1:
                            # Create options with both username and user_id for display
                            user_options = ["All Users"]
                            for username in unique_users:
                                user_records = users_df[users_df['username'] == username]
                                if not user_records.empty:
                                    user_id = user_records['user_id'].iloc[0]
                                    user_options.append(f"{username} ({user_id})")
                            
                            selected_user = st.selectbox(
                                "Select a user to view their timesheet:",
                                options=user_options,
                                index=0
                            )
                            
                            if selected_user != "All Users":
                                # Extract username from the selected option
                                selected_username = selected_user.split(" (")[0]
                                users_df = users_df[users_df['username'] == selected_username]

                        else:
                            # If only one user, show all their data
                            selected_user = "All Users"
                        
                        # Add view options for Timesheet Data
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write("**View Options:**")
                        with col2:
                            view_mode = st.radio(
                                "Data View:",
                                ["📅 Daily", "📊 Weekly", "📋 All Data"],
                                horizontal=True,
                                key=f"timesheet_view_mode_{jobcode_id}"
                            )
                        with col3:
                            if st.button("🔄 Refresh Data", key=f"refresh_timesheet_{jobcode_id}"):
                                # Clear all cached data and force refresh
                                keys_to_clear = [key for key in st.session_state.keys() if f"timesheet_data_{jobcode_id}" in key or f"user_detail_data_{jobcode_id}" in key or f"timesheet_table_{jobcode_id}" in key]
                                for key in keys_to_clear:
                                    del st.session_state[key]
                                # Force a complete page refresh
                                st.cache_data.clear()
                                st.rerun()
                        
                        # Add API logging
                        st.subheader("📡 API Call Information")
                        # This URL is used in fetch_client_user_data_direct() function to make API calls
                        # The function is called earlier in this file:
                        # - Line ~1330 with user_id parameter for detailed user data
                        # - Line ~1270 without user_id parameter for all users data
                        api_url = f"http://16.171.230.164/api/v1/client-user-data/{jobcode_id}?page=1&limit=100"
                        if selected_user != "All Users":
                            # Get user_id from the selected user string (format: "username (user_id)")
                            if "(" in selected_user and ")" in selected_user:
                                user_id = selected_user.split("(")[-1].split(")")[0]
                                api_url += f"&user_id={user_id}"
                                if view_mode == "📅 Daily":
                                    api_url += "&period=daily"
                                elif view_mode == "📊 Weekly":
                                    api_url += "&period=weekly"
                        
                     
                        response = requests.get(api_url, timeout=30)
                        user_data = response.json()

                        # Process the fresh API data into a DataFrame
                        if user_data and user_data.get('data'):
                            try:
                                users_df = pd.DataFrame(user_data['data'])
                                if users_df.empty:
                                    st.warning("No data found in API response")
                            except Exception as e:
                                st.error(f"Error processing API data: {str(e)}")
                                users_df = pd.DataFrame()
                        else:
                            st.warning("No data received from API")
                            users_df = pd.DataFrame()

                    
                        
                       
                        
                      
                      
                        
                        # Format the data
                        if not users_df.empty:
                            # Clean and format date columns - ensure they contain only strings
                            for col in ['work_date', 'start_date', 'end_date']:
                                if col in users_df.columns:
                                    # Convert non-string values to empty string
                                    users_df[col] = users_df[col].astype(str).replace('nan', '').replace('None', '')
                            
                            # Use work_date as the primary date column if available, otherwise use start_date
                            if 'work_date' in users_df.columns:
                                users_df['work_date'] = users_df['work_date'].apply(safe_format_date)
                                date_col = 'work_date'
                            else:
                                # Use start_date as the primary date column
                                users_df['start_date'] = users_df['start_date'].apply(safe_format_date)
                                date_col = 'start_date'
                                # Create work_date from start_date for consistency
                                users_df['work_date'] = users_df['start_date']
                            
                            # Format other dates
                            if 'start_date' in users_df.columns:
                                users_df['start_date'] = users_df['start_date'].apply(safe_format_date)
                            if 'end_date' in users_df.columns:
                                users_df['end_date'] = users_df['end_date'].apply(safe_format_date)
                            
                            # Round duration and handle any remaining None values
                            users_df['total_duration'] = users_df['total_duration'].fillna(0)
                            users_df['total_duration'] = users_df['total_duration'].round(2)
                            
                            # Apply view mode processing
                            if view_mode == "📊 Weekly":
                                # Group by week and aggregate
                                users_df['date_dt'] = pd.to_datetime(users_df[date_col], errors='coerce')
                                if not users_df['date_dt'].isna().all():
                                    # Group by week
                                    users_df['week_start'] = users_df['date_dt'].dt.to_period('W').dt.start_time
                                    weekly_data = users_df.groupby('week_start').agg({
                                        'total_duration': 'sum',
                                        'username': 'first'
                                    }).reset_index()
                                    
                                    # Format for display
                                    weekly_data['work_date'] = weekly_data['week_start'].dt.strftime('%Y-%m-%d')
                                    weekly_data['end_date'] = (weekly_data['week_start'] + pd.Timedelta(days=6)).dt.strftime('%Y-%m-%d')
                                    users_df = weekly_data[['work_date', 'username', 'end_date', 'total_duration']].copy()
                            
                            # For Daily and All Data views, show individual records
                            if view_mode in ["📅 Daily", "📋 All Data"]:
                                # Sort by work_date for better display
                                if 'work_date' in users_df.columns:
                                    users_df = users_df.sort_values('work_date', ascending=False)
                                
                                # Create display dataframe with individual records
                                if 'work_date' in users_df.columns:
                                    display_columns = ['work_date', 'username', 'total_duration']
                                    if 'end_date' in users_df.columns:
                                        display_columns.insert(2, 'end_date')
                                    display_df = users_df[display_columns].copy()
                                    display_df.columns = ['Work Date', 'Username', 'End Date', 'Duration (hrs)'] if 'end_date' in users_df.columns else ['Work Date', 'Username', 'Duration (hrs)']
                                else:
                                    # Fallback to start_date/end_date
                                    display_columns = ['start_date', 'username', 'total_duration']
                                    if 'end_date' in users_df.columns:
                                        display_columns.insert(2, 'end_date')
                                    display_df = users_df[display_columns].copy()
                                    display_df.columns = ['Start Date', 'Username', 'End Date', 'Duration (hrs)'] if 'end_date' in users_df.columns else ['Start Date', 'Username', 'Duration (hrs)']
                                
                      
                            else:
                                # For Weekly view, use the aggregated data
                                if 'work_date' in users_df.columns:
                                    display_columns = ['work_date', 'username', 'total_duration']
                                    if 'end_date' in users_df.columns:
                                        display_columns.insert(2, 'end_date')
                                    display_df = users_df[display_columns].copy()
                                    display_df.columns = ['Work Date', 'Username', 'End Date', 'Duration (hrs)'] if 'end_date' in users_df.columns else ['Work Date', 'Username', 'Duration (hrs)']
                                else:
                                    # Fallback to start_date/end_date
                                    display_columns = ['start_date', 'username', 'total_duration']
                                    if 'end_date' in users_df.columns:
                                        display_columns.insert(2, 'end_date')
                                    display_df = users_df[display_columns].copy()
                                    display_df.columns = ['Start Date', 'Username', 'End Date', 'Duration (hrs)'] if 'end_date' in users_df.columns else ['Start Date', 'Username', 'Duration (hrs)']
                                
                        
                            
                            # Add work status
                            def get_work_status(duration):
                                if view_mode == "📊 Weekly":
                                    # For weekly view, adjust thresholds
                                    if duration >= 40:  # 5 days * 8 hours
                                        return "Full Week"
                                    elif duration >= 30:  # 5 days * 6 hours
                                        return "Good Week"
                                    elif duration >= 20:  # 5 days * 4 hours
                                        return "Partial Week"
                                    else:
                                        return "Light Week"
                                else:
                                    # For daily view
                                    if duration >= 8:
                                        return "Full Day"
                                    elif duration >= 6:
                                        return "Good Day"
                                    elif duration >= 4:
                                        return "Partial Day"
                                    else:
                                        return "Short Day"
                            
                            display_df['Status'] = display_df['Duration (hrs)'].apply(get_work_status)
                            
                            # Color coding
                            def highlight_work_status(row):
                                colors = {
                                    # Daily statuses
                                    'Full Day': 'background-color: #d4edda; color: #155724;',
                                    'Good Day': 'background-color: #d1ecf1; color: #0c5460;',
                                    'Partial Day': 'background-color: #fff3cd; color: #856404;',
                                    'Short Day': 'background-color: #f8d7da; color: #721c24;',
                                    # Weekly statuses
                                    'Full Week': 'background-color: #d4edda; color: #155724;',
                                    'Good Week': 'background-color: #d1ecf1; color: #0c5460;',
                                    'Partial Week': 'background-color: #fff3cd; color: #856404;',
                                    'Light Week': 'background-color: #f8d7da; color: #721c24;'
                                }
                                return [colors.get(row['Status'], '')] * len(row)
                            
                            styled_df = display_df.style.apply(highlight_work_status, axis=1)
                            styled_df = styled_df.format({'Duration (hrs)': '{:.1f}'})
                            
                            # Display view information
                            
                            # Add data freshness indicator
                            import datetime
                            current_time = datetime.datetime.now().strftime("%H:%M:%S")
                            

                            
                            # Display the data with a unique key to force refresh
                            import time
                            table_key = f"timesheet_table_{jobcode_id}_{len(display_df)}_{view_mode}_{int(time.time())}"
                            st.dataframe(
                                styled_df, 
                                use_container_width=True, 
                                height=400,
                                key=table_key
                            )
                            
                            # Show summary statistics
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                total_hours = display_df['Duration (hrs)'].sum()
                                st.metric("Total Hours", f"{total_hours:.1f}")
                            
                            with col2:
                                avg_hours = display_df['Duration (hrs)'].mean()
                                st.metric("Avg Hours/Day", f"{avg_hours:.1f}")
                            
                            with col3:
                                work_days = len(display_df)
                                st.metric("Work Days", f"{work_days:.0f}")
                        else:
                            st.warning("No timesheet data available for the selected user.")
                    else:
                        st.warning("No timesheet data available for this project.")
                
                
            except Exception as e:
                st.error(f"Error processing selection: {str(e)}")
        else:
            st.info("👆 Please select a project/client from the dropdown above to view detailed information.")
    
    with tab5:
        st.subheader("📊 Real-Time API Data View")
        
        # Add controls for API calls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write("**API Controls**")
        
        with col2:
            page = st.number_input("Page", min_value=1, max_value=100, value=1, step=1)
        
        with col3:
            limit = st.number_input("Limit", min_value=1, max_value=100, value=10, step=1)
        
        # Refresh button
        if st.button("🔄 Refresh API Data", type="primary"):
            st.rerun()
        
        # Make fresh API call with user parameters
        with st.spinner("Fetching fresh data from API..."):
            fresh_client_data = fetch_client_time_summary_direct(page=page, limit=limit)
        
        if fresh_client_data and fresh_client_data.get('data'):
            client_data = fresh_client_data
            
            # Display API metadata
           
            st.metric("Total Records", len(client_data['data']))
            
           
            
            
            
            # Display the raw API data
            st.subheader("📋 Client Time Summary Data")
            
            # Convert to DataFrame for better display
            df = pd.DataFrame(client_data['data'])
            
            # Format the data for better readability
            if not df.empty:
                # Handle None values in total_duration
                df['total_duration'] = df['total_duration'].fillna(0)
                
                # Format dates - handle empty strings and invalid dates safely
                if 'start_date' in df.columns:
                    df['start_date'] = df['start_date'].apply(safe_format_date)
                
                if 'end_date' in df.columns:
                    df['end_date'] = df['end_date'].apply(safe_format_date)
                
                # Round numeric columns
                numeric_columns = ['total_duration', 'days_worked']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = df[col].round(2)
                
                # Rename columns for better display
                column_mapping = {
                    'name': 'Client Name',
                    'jobcode_id': 'Job Code ID',
                    'total_duration': 'Total Duration (hrs)',
                    'start_date': 'Start Date',
                    'end_date': 'End Date',
                    'days_worked': 'Days Worked'
                }
                df = df.rename(columns=column_mapping)
                
                # Display the data with pagination info
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )
                
                
                
                # Add summary statistics
                st.subheader("📈 Data Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_hours = df['Total Duration (hrs)'].sum()
                    st.metric("Total Hours", f"{total_hours:,.1f}")
                
                with col2:
                    avg_hours = df['Total Duration (hrs)'].mean()
                    st.metric("Average Hours per Client", f"{avg_hours:.1f}")
                
                with col3:
                    total_days = df['Days Worked'].sum()
                    st.metric("Total Days Worked", f"{total_days:,.0f}")
                
                # Top clients by hours
                st.subheader("🏆 Top Clients by Hours")
                top_clients = df.nlargest(10, 'Total Duration (hrs)')
                
                for idx, row in top_clients.iterrows():
                    st.write(f"• **{row['Client Name']}**: {row['Total Duration (hrs)']:.1f} hours ({row['Days Worked']:.0f} days)")
            
            else:
                st.warning("No data available from the API.")
        else:
            st.error("Unable to fetch data from the API. Please check your connection and try again.")
    
    # Alerts section
    if alerts_data:
        st.markdown("---")
        st.subheader("🚨 Project Alerts")
        
        for alert in alerts_data:
            alert_type = alert.get('type', 'info')
            message = alert.get('message', 'No message')
            project = alert.get('project', 'Unknown')
            
            if alert_type == 'danger':
                st.error(f"🚨 **{project}**: {message}")
            elif alert_type == 'warning':
                st.warning(f"⚠️ **{project}**: {message}")
            else:
                st.info(f"ℹ️ **{project}**: {message}")

if __name__ == "__main__":
    main()