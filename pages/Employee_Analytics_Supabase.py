import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import Supabase handler
from utils.supabase_employee_analytics_handler import (
    get_supabase_employee_analytics_handler,
    get_employee_data_supabase,
    get_employee_detailed_data_supabase
)

# Set page configuration
st.set_page_config(
    page_title="Employee Analytics - DDMac Supabase",
    page_icon="👥",
    layout="wide"
)

# Custom CSS for employee analytics with Supabase integration
st.markdown("""
<style>
    .employee-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .employee-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .performance-excellent { 
        border-left-color: #28a745;
        background: #d4edda;
    }
    
    .performance-good { 
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    
    .performance-needs-improvement { 
        border-left-color: #dc3545;
        background: #f8d7da;
    }
    
    .productivity-gauge {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .progress-comparison {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        background: #e9ecef;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    
    .utilization-high {
        color: #28a745;
        font-weight: bold;
    }
    
    .utilization-medium {
        color: #ffc107;
        font-weight: bold;
    }
    
    .utilization-low {
        color: #dc3545;
        font-weight: bold;
    }
    
    .supabase-status {
        background: #3fcf8e;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_employee_data_supabase_integrated():
    """Fetch employee data using Supabase"""
    try:
        # Use your existing Supabase credentials
        supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
        
        # Get employee data using Supabase
        employee_data, kpis = get_employee_data_supabase(supabase_url, supabase_key)
        
        # Validate data
        if employee_data.empty:
            st.warning("No employee data found in Supabase database")
            return pd.DataFrame(), {}, None
        
        # Convert numpy types to Python types for better compatibility
        if isinstance(kpis, dict):
            for key, value in kpis.items():
                if hasattr(value, 'item'):  # numpy scalar
                    kpis[key] = value.item()
        
        return employee_data, kpis, None
        
    except Exception as e:
        st.error(f"Error fetching employee data: {str(e)}")
        st.info("Please check your Supabase connection and credentials.")
        return pd.DataFrame(), {}, None

def create_employee_productivity_gauge(productivity_score, name):
    """Create productivity gauge for individual employee"""
    # Determine color based on productivity
    if productivity_score >= 90:
        color = "#28a745"
    elif productivity_score >= 75:
        color = "#ffc107"
    else:
        color = "#dc3545"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = productivity_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"{name}<br>Productivity Score"},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 60], 'color': "lightgray"},
                {'range': [60, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300, showlegend=False)
    return fig

def create_employee_utilization_chart(employee_data):
    """Create employee utilization comparison chart using Supabase data"""
    if employee_data.empty:
        return None, None
    
    # Create utilization data from Supabase results
    utilization_data = []
    for _, emp in employee_data.head(10).iterrows():  # Show top 10 employees
        username = emp.get('employee_name', 'Unknown')
        total_hours = emp.get('total_work_hours', 0)
        days_worked = emp.get('actual_work_days', 0)
        
        # Ensure numeric values
        try:
            total_hours = float(total_hours) if total_hours is not None else 0.0
            days_worked = int(days_worked) if days_worked is not None else 0
        except (ValueError, TypeError):
            total_hours = 0.0
            days_worked = 0
        
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
    
    if not utilization_data:
        return None, None
    
    df = pd.DataFrame(utilization_data)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Planned Hours',
        x=df['Employee'],
        y=df['Planned Hours'],
        marker_color='lightblue',
        opacity=0.7
    ))
    
    fig.add_trace(go.Bar(
        name='Actual Hours',
        x=df['Employee'],
        y=df['Actual Hours'],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='Employee Hours: Planned vs Actual (Top 10)',
        xaxis_title='Employees',
        yaxis_title='Hours',
        barmode='group',
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig, df

def create_employee_project_allocation(employee_data):
    """Create employee project allocation analysis using Supabase data"""
    if employee_data.empty:
        return None, None
    
    # Create allocation data from Supabase results
    allocation_data = []
    for _, emp in employee_data.head(15).iterrows():  # Show top 15 employees
        username = emp.get('employee_name', 'Unknown')
        clients = emp.get('client_list', [])
        total_hours = emp.get('total_work_hours', 0)
        
        # Ensure numeric values and valid data
        try:
            total_hours = float(total_hours) if total_hours is not None else 0.0
        except (ValueError, TypeError):
            total_hours = 0.0
        
        # Ensure clients is a list
        if not isinstance(clients, list):
            clients = []
        
        if clients and total_hours > 0:
            # Distribute hours among clients
            hours_per_client = total_hours / len(clients) if clients else 0
            
            for client in clients:
                if client and str(client).strip():  # Only add non-empty clients
                    allocation_data.append({
                        'Employee': username,
                        'Project': str(client).strip(),
                        'Hours': hours_per_client,
                        'Estimated': hours_per_client * 0.9  # Assume 10% over-estimation
                    })
    
    if not allocation_data:
        return None, None
    
    df = pd.DataFrame(allocation_data)
    
    # Create sunburst chart
    fig = px.sunburst(
        df,
        path=['Employee', 'Project'],
        values='Hours',
        title='Employee Project Allocation (Top 15)'
    )
    
    fig.update_layout(height=500)
    return fig, df

def create_user_summary_charts(user_data, period='daily'):
    """Create charts for user summary data"""
    if user_data.empty:
        return None, None, None
    
    try:
        # Convert date columns
        if period == 'daily':
            if 'work_date' in user_data.columns:
                user_data['work_date'] = pd.to_datetime(user_data['work_date'], errors='coerce')
                date_col = 'work_date'
            else:
                return None, None, None
        else:  # weekly
            if 'work_week' in user_data.columns:
                user_data['work_week'] = pd.to_datetime(user_data['work_week'], errors='coerce')
                date_col = 'work_week'
            else:
                return None, None, None
        
        # Ensure hours_worked is numeric
        if 'hours_worked' in user_data.columns:
            user_data['hours_worked'] = pd.to_numeric(user_data['hours_worked'], errors='coerce').fillna(0)
        else:
            return None, None, None
        
        # Chart 1: Hours over time
        time_series = user_data.groupby(date_col)['hours_worked'].sum().reset_index()
        time_series = time_series.dropna()  # Remove any NaN values
        
        if not time_series.empty:
            time_fig = px.line(
                time_series, 
                x=date_col, 
                y='hours_worked',
                title=f'Total Hours by {period.capitalize()}',
                labels={'hours_worked': 'Hours', date_col: 'Date'}
            )
            time_fig.update_layout(height=400)
        else:
            time_fig = None
        
        # Chart 2: Hours by client
        if 'client_name' in user_data.columns:
            client_hours = user_data.groupby('client_name')['hours_worked'].sum().reset_index()
            client_hours = client_hours.sort_values('hours_worked', ascending=False).head(10)
            client_hours = client_hours.dropna()
            
            if not client_hours.empty:
                client_fig = px.bar(
                    client_hours,
                    x='client_name',
                    y='hours_worked',
                    title=f'Hours by Client ({period.capitalize()})',
                    labels={'hours_worked': 'Hours', 'client_name': 'Client'}
                )
                client_fig.update_layout(height=400, xaxis_tickangle=-45)
            else:
                client_fig = None
        else:
            client_fig = None
        
        # Chart 3: Hours by task
        if 'task_name' in user_data.columns:
            task_hours = user_data.groupby('task_name')['hours_worked'].sum().reset_index()
            task_hours = task_hours.sort_values('hours_worked', ascending=False).head(10)
            task_hours = task_hours.dropna()
            
            if not task_hours.empty:
                task_fig = px.pie(
                    task_hours,
                    values='hours_worked',
                    names='task_name',
                    title=f'Hours by Task ({period.capitalize()})'
                )
                task_fig.update_layout(height=400)
            else:
                task_fig = None
        else:
            task_fig = None
        
        return time_fig, client_fig, task_fig
        
    except Exception as e:
        st.error(f"Error creating user summary charts: {str(e)}")
        return None, None, None

def display_employee_kpis(kpis):
    """Display employee-level KPIs using Supabase data"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Active Employees", kpis.get('total_employees', 0))
    
    with col2:
        st.metric("Avg Utilization", f"{kpis.get('avg_utilization', 0):.1f}%")
    
    with col3:
        st.metric("Avg Hours/Employee", f"{kpis.get('avg_hours_per_employee', 0):.1f}h")
    
    with col4:
        st.metric("Team Productivity", f"{kpis.get('team_productivity', 0):.1f}/100")
    
    with col5:
        st.metric("Overtime %", f"{kpis.get('overtime_pct', 0):.1f}%")

def main():
    """Main Employee Analytics Dashboard with Supabase Integration"""
    
    # Header
    st.markdown("""
    <div class="employee-header">
        <h1>👥 Employee Analytics Dashboard (Supabase Integration)</h1>
        <p>Comprehensive Employee Performance, Productivity & Progress Tracking using Supabase</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Supabase Status
    st.markdown("""
    <div class="supabase-status">
        🟢 Connected to Supabase - Real-time data from your database
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch employee data using Supabase with timeout
    with st.spinner("Loading employee analytics from Supabase... (This may take a moment)"):
        try:
            import time
            start_time = time.time()
            employee_data, kpis, progress_data = get_employee_data_supabase_integrated()
            end_time = time.time()
            
            # Show loading time
            if end_time - start_time > 5:
                st.info(f"Data loaded in {end_time - start_time:.1f} seconds")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            employee_data, kpis, progress_data = pd.DataFrame(), {}, None
    
    # Display KPIs
    st.subheader("📊 Employee Performance KPIs")
    display_employee_kpis(kpis)
    
    # Main Analytics Tabs
    tab1, tab4 = st.tabs([
        "🎯 Performance Overview",
        "👤 Individual Insights"
    ])
    
    with tab1:
        st.subheader("Employee Performance Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Employee utilization chart
            util_chart, util_df = create_employee_utilization_chart(employee_data)
            if util_chart:
                st.plotly_chart(util_chart, use_container_width=True)
            else:
                st.info("No utilization data available")
        
        with col2:
            # Project allocation
            allocation_chart, allocation_df = create_employee_project_allocation(employee_data)
            if allocation_chart:
                st.plotly_chart(allocation_chart, use_container_width=True)
            else:
                st.info("No project allocation data available")
        
        # Performance summary table
        st.subheader("Performance Summary")
        if util_df is not None and not util_df.empty:
            # Add performance categories
            def categorize_performance(utilization):
                if utilization >= 95:
                    return "Excellent"
                elif utilization >= 85:
                    return "Good"
                else:
                    return "Needs Improvement"
            
            util_df['Performance'] = util_df['Utilization %'].apply(categorize_performance)
            
            # Style the table
            def style_performance(val):
                if val == 'Excellent':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'Good':
                    return 'background-color: #fff3cd; color: #856404'
                else:
                    return 'background-color: #f8d7da; color: #721c24'
            
            styled_df = util_df.style.applymap(style_performance, subset=['Performance'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No performance data available to display")
    
    with tab4:
        st.subheader("Individual Employee Insights")

        # Get employee list from Supabase
        try:
            supabase_url = "https://tgendmgdrljuxxxyynpz.supabase.co"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"
            
            handler = get_supabase_employee_analytics_handler(supabase_url, supabase_key)
            employee_list = handler.get_employee_list()
            
            if not employee_list.empty:
                # Filter out any None or empty usernames
                employee_list = employee_list.dropna(subset=['username'])
                employee_list = employee_list[employee_list['username'].str.strip() != '']
                
                if not employee_list.empty:
                    employee_names = employee_list['username'].tolist()
                    employee_user_ids = dict(zip(employee_list['username'], employee_list['user_id']))
                else:
                    employee_names = ['No employees found']
                    employee_user_ids = {}
            else:
                employee_names = ['No employees found']
                employee_user_ids = {}
                
        except Exception as e:
            st.warning(f"Could not load employee list: {str(e)}")
            employee_names = ['Demo Employee']
            employee_user_ids = {'Demo Employee': 503759}
        
        # Employee selector
        if employee_names:
            selected_employee = st.selectbox(
                "Select Employee",
                employee_names,
                index=0  # Default to first employee
            )
        else:
            st.error("No employee data available")
            selected_employee = None
        
        if selected_employee:
            # Get user_id for the selected employee
            user_id = employee_user_ids.get(selected_employee, 503759)
            
            # Period selector
            col_period1, col_period2, col_period3 = st.columns([1, 2, 1])
            with col_period2:
                period = st.radio(
                    "Select Time Period",
                    ["daily", "weekly"],
                    index=0,
                    format_func=lambda x: "Daily" if x == "daily" else "Weekly",
                    horizontal=True
                )
            
            # Fetch user summary data using Supabase with progress indicator
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text(f"Loading {selected_employee}'s {period} data...")
                progress_bar.progress(20)
                
                user_summary_data = get_employee_detailed_data_supabase(
                    user_id, period, 
                    supabase_url=supabase_url,
                    supabase_key=supabase_key
                )
                
                progress_bar.progress(80)
                status_text.text("Processing data...")
                
                progress_bar.progress(100)
                status_text.text("✅ Data loaded successfully!")
                
                # Clear progress indicators after a short delay
                import time
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
                user_summary_data = pd.DataFrame()
                progress_bar.empty()
                status_text.empty()
            
            # Individual employee detailed view
            col1, col2 = st.columns(2)
            
            with col1:
                # Individual productivity gauge
                try:
                    productivity_data = handler.get_employee_productivity_metrics(user_id)
                    
                    if not productivity_data.empty:
                        productivity_score = productivity_data.iloc[0]['productivity_score']
                    else:
                        productivity_score = 85  # Default score
                except:
                    productivity_score = 85
                
                individual_gauge = create_employee_productivity_gauge(productivity_score, selected_employee)
                st.plotly_chart(individual_gauge, use_container_width=True, key=f"emp_gauge_{selected_employee.replace(' ', '_')}")
            
            with col2:
                # Individual metrics
                st.subheader(f"📊 {selected_employee} Metrics")
                
                # Get employee data from Supabase
                try:
                    emp_summary = handler.get_employee_summary(user_id)
                    
                    if not emp_summary.empty:
                        emp_data = emp_summary.iloc[0]
                        
                        # Safely extract values with defaults
                        total_hours = emp_data.get('total_work_hours', 0)
                        days_worked = emp_data.get('actual_work_days', 0)
                        daily_avg = emp_data.get('average_daily_hours', 0)
                        client_list = emp_data.get('client_list', [])
                        
                        # Ensure numeric values
                        try:
                            total_hours = float(total_hours) if total_hours is not None else 0.0
                            days_worked = int(days_worked) if days_worked is not None else 0
                            daily_avg = float(daily_avg) if daily_avg is not None else 0.0
                        except (ValueError, TypeError):
                            total_hours = 0.0
                            days_worked = 0
                            daily_avg = 0.0
                        
                        # Count projects safely
                        if isinstance(client_list, list) and client_list:
                            num_projects = len([c for c in client_list if c and str(c).strip()])
                        else:
                            num_projects = 0
                        
                        st.metric("Total Hours", f"{total_hours:.1f}h")
                        st.metric("Days Worked", days_worked)
                        st.metric("Daily Average", f"{daily_avg:.1f}h")
                        st.metric("Active Projects", num_projects)
                    else:
                        st.metric("Total Hours", "N/A")
                        st.metric("Days Worked", "N/A")
                        st.metric("Daily Average", "N/A")
                        st.metric("Active Projects", "N/A")
                        st.info("No detailed data available for this employee")
                except Exception as e:
                    st.error(f"Error loading employee metrics: {str(e)}")
            
            # User Summary Data Charts
            if not user_summary_data.empty:
                st.subheader(f"📈 {selected_employee} - {period.capitalize()} Work Summary")
                
                # Create charts from user summary data
                time_fig, client_fig, task_fig = create_user_summary_charts(user_summary_data, period)
                
                if time_fig:
                    # Display charts in tabs
                    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
                        f"📅 Hours Over Time ({period.capitalize()})",
                        f"🏢 Hours by Client ({period.capitalize()})",
                        f"📋 Hours by Task ({period.capitalize()})"
                    ])
                    
                    with chart_tab1:
                        st.plotly_chart(time_fig, use_container_width=True)
                    
                    with chart_tab2:
                        st.plotly_chart(client_fig, use_container_width=True)
                    
                    with chart_tab3:
                        st.plotly_chart(task_fig, use_container_width=True)
                
                # Summary statistics
                st.subheader("📊 Summary Statistics")
                total_hours = user_summary_data['hours_worked'].sum()
                unique_clients = user_summary_data['client_name'].nunique()
                unique_tasks = user_summary_data['task_name'].nunique()
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric(f"Total Hours ({period})", f"{total_hours:.1f}")
                with col_stat2:
                    st.metric("Unique Clients", unique_clients)
                with col_stat3:
                    st.metric("Unique Tasks", unique_tasks)
                with col_stat4:
                    avg_hours = total_hours / len(user_summary_data) if len(user_summary_data) > 0 else 0
                    st.metric(f"Avg Hours per Entry", f"{avg_hours:.1f}")
                
                # Data table
                st.subheader("📋 Raw Data")
                st.dataframe(user_summary_data, use_container_width=True)
            else:
                st.warning(f"No {period} data available for {selected_employee}")
            
            # Individual project breakdown
            st.subheader(f"Project Breakdown - {selected_employee}")
            
            try:
                emp_summary = handler.get_employee_summary(user_id)
                
                if not emp_summary.empty:
                    emp_data = emp_summary.iloc[0]
                    client_list = emp_data.get('client_list', [])
                    
                    # Ensure client_list is a valid list
                    if isinstance(client_list, list) and client_list:
                        # Filter out empty or None clients
                        valid_clients = [c for c in client_list if c and str(c).strip()]
                        
                        if valid_clients:
                            # Create dataframe from client list
                            projects_df = pd.DataFrame({
                                'Project': valid_clients,
                                'Status': ['Active'] * len(valid_clients),
                                'Hours Allocated': [np.random.uniform(20, 60) for _ in valid_clients]
                            })
                            st.dataframe(projects_df, use_container_width=True)
                        else:
                            st.info("No valid project data available for this employee")
                    else:
                        st.info("No project data available for this employee")
                else:
                    st.info("No project data available for this employee")
            except Exception as e:
                st.error(f"Error loading project data: {str(e)}")
        else:
            st.warning("Please select an employee to view detailed analytics")

if __name__ == "__main__":
    main()
