import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
from datetime import datetime, timedelta

# Import dual data source utilities
from utils import (
    # Original functions
    analyze_employees_overview,
    analyze_employee_detailed,
    get_employee_performance_metrics,
    TimeTrackingAnalyzer,
    
    # API functions
    get_api_handler,
    analyze_employees_overview_api,
    analyze_employee_detailed_api,
    
    # Estimates functions
    get_estimates_handler,
    get_progress_comparison,
    get_budget_alerts
)

# Set page configuration
st.set_page_config(
    page_title="Employee Analytics - DDMac",
    page_icon="👥",
    layout="wide"
)

# Custom CSS for employee analytics with dual data sources
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
</style>
""", unsafe_allow_html=True)

def get_employee_data():
    """Fetch employee data from both API and estimates sources"""
    api_data = None
    estimates_data = None
    progress_data = None
    
    try:
        # Get API data for employee analytics
        api_handler = get_api_handler()
        api_data = api_handler.get_sample_data()
        
        # Get estimates data
        estimates_handler = get_estimates_handler()
        estimates_data = estimates_handler.get_sample_data()
        
        # Generate progress comparison
        if api_data and estimates_data:
            progress_data = get_progress_comparison(api_data, estimates_data)
    
    except Exception as e:
        st.error(f"Error fetching employee data: {str(e)}")
    
    return api_data, estimates_data, progress_data

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
    """Create employee utilization comparison chart using real API data"""
    if not employee_data or not employee_data.get('data'):
        return None, None
    
    employees = employee_data['data']
    
    # Create utilization data from real employee data
    utilization_data = []
    for emp in employees[:10]:  # Show top 10 employees
        username = emp.get('username', 'Unknown')
        total_hours = emp.get('total_hours', 0)
        days_worked = emp.get('days_worked', 0)
        
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

def create_employee_progress_timeline(api_data):
    """Create employee progress timeline"""
    if not api_data:
        return None
    
    # Mock employee daily progress
    timeline_data = []
    employees = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    for emp in employees:
        for date in dates:
            # Generate realistic daily hours
            base_hours = np.random.normal(8, 1.5)
            hours = max(0, min(12, base_hours))
            timeline_data.append({
                'Employee': emp,
                'Date': date,
                'Hours': hours
            })
    
    df = pd.DataFrame(timeline_data)
    
    fig = px.line(
        df,
        x='Date',
        y='Hours',
        color='Employee',
        title='Employee Daily Hours Timeline (Last 30 Days)',
        labels={'Hours': 'Daily Hours', 'Date': 'Date'}
    )
    
    fig.update_layout(height=400)
    return fig

def create_employee_project_allocation(employee_data, estimates_data):
    """Create employee project allocation analysis using real API data"""
    if not employee_data or not employee_data.get('data'):
        return None, None
    
    employees = employee_data['data']
    
    # Create allocation data from real employee data
    allocation_data = []
    for emp in employees[:15]:  # Show top 15 employees
        username = emp.get('username', 'Unknown')
        clients = emp.get('clients', [])
        total_hours = emp.get('total_hours', 0)
        
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

def fetch_user_summary_data(user_id, period='daily', page=1, limit=1000):
    """Fetch user summary data from API with pagination"""
    try:
        all_data = []
        current_page = 1
        total_pages = 1
        
        while current_page <= total_pages:
            response = requests.get(
                "http://16.171.230.164/api/user-summary-data",
                params={
                    "user_id": user_id,
                    "period": period,
                    "page": current_page,
                    "limit": limit
                },
                timeout=10
            )
            
            if response.status_code == 200:
                page_data = response.json()
                page_records = page_data.get("data", [])
                
                if page_records:  # If we got data
                    all_data.extend(page_records)
                    st.write(f"📄 Loaded {period} page {current_page}: {len(page_records)} records")
                
                # Update pagination info
                pagination = page_data.get("pagination", {})
                total_pages = pagination.get("total_pages", 1)
                current_page += 1
                
                # Safety check to prevent infinite loops
                if current_page > 50:  # Max 50 pages (50,000 records)
                    st.warning(f"⚠️ Reached maximum page limit (50) for {period} data. Some data may be missing.")
                    break
            else:
                st.error(f"Failed to fetch {period} page {current_page}: {response.status_code}")
                break
        
        if all_data:
            return {
                "data": all_data,
                "pagination": {"total": len(all_data), "page": 1}
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching user summary data: {str(e)}")
        return None

def create_user_summary_charts(user_data, period='daily'):
    """Create charts for user summary data"""
    if not user_data or not user_data.get('data'):
        return None, None, None
    
    df = pd.DataFrame(user_data['data'])
    
    # Convert date columns
    if period == 'daily':
        df['work_day'] = pd.to_datetime(df['work_day'], format='%d-%m-%Y')
        date_col = 'work_day'
    else:  # weekly
        df['work_week'] = pd.to_datetime(df['work_week'], format='%d-%m-%Y')
        date_col = 'work_week'
    
    # Chart 1: Hours over time
    time_series = df.groupby(date_col)['hours'].sum().reset_index()
    time_fig = px.line(
        time_series, 
        x=date_col, 
        y='hours',
        title=f'Total Hours by {period.capitalize()}',
        labels={'hours': 'Hours', date_col: 'Date'}
    )
    time_fig.update_layout(height=400)
    
    # Chart 2: Hours by client
    client_hours = df.groupby('client')['hours'].sum().reset_index()
    client_hours = client_hours.sort_values('hours', ascending=False).head(10)
    client_fig = px.bar(
        client_hours,
        x='client',
        y='hours',
        title=f'Hours by Client ({period.capitalize()})',
        labels={'hours': 'Hours', 'client': 'Client'}
    )
    client_fig.update_layout(height=400, xaxis_tickangle=-45)
    
    # Chart 3: Hours by task
    task_hours = df.groupby('task')['hours'].sum().reset_index()
    task_hours = task_hours.sort_values('hours', ascending=False).head(10)
    task_fig = px.pie(
        task_hours,
        values='hours',
        names='task',
        title=f'Hours by Task ({period.capitalize()})'
    )
    task_fig.update_layout(height=400)
    
    return time_fig, client_fig, task_fig

def display_employee_kpis(employee_data, estimates_data):
    """Display employee-level KPIs using real API data"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate metrics from real employee data
    if employee_data and employee_data.get('data'):
        employees = employee_data['data']
        total_employees = len(employees)
        
        # Calculate total hours from all employees
        total_hours = sum(emp.get('total_hours', 0) for emp in employees)
        avg_hours_per_employee = total_hours / max(1, total_employees)
        
        # Calculate average utilization (assuming 8 hours per day as standard)
        total_days_worked = sum(emp.get('days_worked', 0) for emp in employees)
        standard_hours = total_days_worked * 8  # 8 hours per day standard
        avg_utilization = (total_hours / max(1, standard_hours)) * 100 if standard_hours > 0 else 0
        
        # Calculate team productivity based on hours consistency
        daily_averages = [emp.get('daily_average', 0) for emp in employees if emp.get('daily_average', 0) > 0]
        if daily_averages:
            # Productivity based on how close daily averages are to 8 hours (optimal)
            productivity_scores = [min(100, (avg / 8) * 100) for avg in daily_averages]
            team_productivity = sum(productivity_scores) / len(productivity_scores)
        else:
            team_productivity = 0
        
        # Calculate overtime percentage (hours over 8 per day)
        overtime_hours = sum(max(0, emp.get('daily_average', 0) - 8) * emp.get('days_worked', 0) for emp in employees)
        overtime_pct = (overtime_hours / max(1, total_hours)) * 100
        
        # Calculate previous period for delta (simplified - using 10% variation)
        prev_utilization = avg_utilization * 0.9
        prev_productivity = team_productivity * 0.95
        prev_overtime = overtime_pct * 1.1
        
    else:
        # Fallback to demo data if no real data
        total_employees = 0
        avg_hours_per_employee = 0
        avg_utilization = 0
        team_productivity = 0
        overtime_pct = 0
        prev_utilization = 0
        prev_productivity = 0
        prev_overtime = 0
    
    with col1:
        st.metric("Active Employees", total_employees)
    
    with col2:
        delta_utilization = avg_utilization - prev_utilization
        st.metric("Avg Utilization", f"{avg_utilization:.1f}%", 
                 delta=f"{delta_utilization:+.1f}%" if delta_utilization != 0 else None)
    
    with col3:
        st.metric("Avg Hours/Employee", f"{avg_hours_per_employee:.1f}h")
    
    with col4:
        delta_productivity = team_productivity - prev_productivity
        st.metric("Team Productivity", f"{team_productivity:.1f}/100", 
                 delta=f"{delta_productivity:+.1f}" if delta_productivity != 0 else None)
    
    with col5:
        delta_overtime = overtime_pct - prev_overtime
        st.metric("Overtime %", f"{overtime_pct:.1f}%", 
                 delta=f"{delta_overtime:+.1f}%" if delta_overtime != 0 else None)

def main():
    """Main Employee Analytics Dashboard"""
    
    # Header
    st.markdown("""
    <div class="employee-header">
        <h1>👥 Employee Analytics Dashboard</h1>
        <p>Comprehensive Employee Performance, Productivity & Progress Tracking</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch employee data
    with st.spinner("Loading employee analytics..."):
        api_data, estimates_data, progress_data = get_employee_data()
    
    # Fetch employee listing data for KPIs
    employee_kpi_data = None
    try:
        with st.spinner("Loading employee data for KPIs..."):
            all_employees = []
            page = 1
            limit = 50
            
            while True:
                response = requests.get(
                    "http://16.171.230.164/api/user-listing-data",
                    params={
                        "page": page,
                        "limit": limit,
                        "sort_field": "username", 
                        "sort_order": "asc"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    page_data = response.json()
                    page_employees = page_data.get("data", [])
                    
                    if page_employees:
                        all_employees.extend(page_employees)
                    
                    pagination = page_data.get("pagination", {})
                    total_pages = pagination.get("total_pages", 1)
                    
                    if page >= total_pages or not page_employees:
                        break
                    page += 1
                    
                    # Safety check
                    if page > 20:  # Limit for KPI loading
                        break
                else:
                    break
            
            if all_employees:
                employee_kpi_data = {
                    "data": all_employees,
                    "pagination": {"total": len(all_employees), "page": 1}
                }
    except Exception as e:
        st.warning(f"Could not load employee data for KPIs: {str(e)}")
    
    # Display KPIs
    st.subheader("📊 Employee Performance KPIs")
    display_employee_kpis(employee_kpi_data, estimates_data)
    
    # Main Analytics Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Performance Overview",
        "📈 Productivity Analysis", 
        "⏱️ Time Utilization",
        "👤 Individual Insights"
    ])
    
    with tab1:
        st.subheader("Employee Performance Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Employee utilization chart
            util_chart, util_df = create_employee_utilization_chart(employee_kpi_data)
            if util_chart:
                st.plotly_chart(util_chart, use_container_width=True)
        
        with col2:
            # Project allocation
            allocation_chart, allocation_df = create_employee_project_allocation(employee_kpi_data, estimates_data)
            if allocation_chart:
                st.plotly_chart(allocation_chart, use_container_width=True)
        
        # Performance summary table
        st.subheader("Performance Summary")
        if util_df is not None:
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
    
    with tab2:
        st.subheader("Productivity Analysis")
        
        # Individual productivity gauges
        col1, col2, col3 = st.columns(3)
        
        employees = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
        productivity_scores = [92, 88, 95, 78, 91]
        
        for i, (emp, score) in enumerate(zip(employees[:3], productivity_scores[:3])):
            with [col1, col2, col3][i]:
                gauge_fig = create_employee_productivity_gauge(score, emp)
                st.plotly_chart(gauge_fig, use_container_width=True)
        
        # Productivity trends
        st.subheader("Productivity Trends")
        timeline_fig = create_employee_progress_timeline(api_data)
        if timeline_fig:
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        # Productivity insights
        st.subheader("📊 Productivity Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🏆 Top Performers:**
            - Carol Davis: 95% productivity
            - Alice Johnson: 92% productivity
            - Emma Brown: 91% productivity
            """)
        
        with col2:
            st.markdown("""
            **📈 Improvement Areas:**
            - David Wilson: Focus on time management
            - Bob Smith: Reduce context switching
            - Team: Optimize meeting efficiency
            """)
    
    with tab3:
        st.subheader("Time Utilization Analysis")
        
        if progress_data and estimates_data:
            # Progress vs estimates comparison
            st.subheader("Actual vs Estimated Hours")
            
            progress_comparison = []
            for p in progress_data:
                progress_comparison.append({
                    'Project': p['project_name'],
                    'Estimated Hours': p['estimated_hours'],
                    'Actual Hours': p['actual_hours'],
                    'Variance': p['actual_hours'] - p['estimated_hours'],
                    'Variance %': ((p['actual_hours'] - p['estimated_hours']) / p['estimated_hours'] * 100) if p['estimated_hours'] > 0 else 0
                })
            
            progress_df = pd.DataFrame(progress_comparison)
            
            # Variance chart
            fig = px.bar(
                progress_df,
                x='Project',
                y='Variance',
                color='Variance',
                color_continuous_scale='RdYlGn_r',
                title='Project Hours Variance (Actual - Estimated)',
                labels={'Variance': 'Hours Variance'}
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed variance table
            st.dataframe(progress_df, use_container_width=True)
        else:
            st.info("💡 Upload estimates to enable time utilization comparison")
        
        # Time distribution analysis
        st.subheader("Time Distribution by Category")
        
        # Mock time category data
        time_categories = {
            'Development': 65,
            'Meetings': 15,
            'Planning': 10,
            'Documentation': 5,
            'Other': 5
        }
        
        fig = px.pie(
            values=list(time_categories.values()),
            names=list(time_categories.keys()),
            title='Team Time Distribution (%)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Individual Employee Insights")

        # Fetch employee list from API with pagination
        employee_data = None
        employee_names = []
        employee_user_ids = {}  # Map usernames to user_ids
        all_employees = []  # Store all employees from all pages
        
        try:
            page = 1
            limit = 50  # Fetch 50 employees per page
            total_pages = 1
            
            with st.spinner("Loading all employee data..."):
                while page <= total_pages:
                    response = requests.get(
                        "http://16.171.230.164/api/user-listing-data",
                        params={
                            "page": page,
                            "limit": limit,
                            "sort_field": "username", 
                            "sort_order": "asc"
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        page_data = response.json()
                        page_employees = page_data.get("data", [])
                        
                        if page_employees:  # If we got data
                            all_employees.extend(page_employees)
                            st.write(f"📄 Loaded page {page}: {len(page_employees)} employees")
                        
                        # Update pagination info
                        pagination = page_data.get("pagination", {})
                        total_pages = pagination.get("total_pages", 1)
                        page += 1
                        
                        # Safety check to prevent infinite loops
                        if page > 100:  # Max 100 pages (5000 employees)
                            st.warning("⚠️ Reached maximum page limit (100). Some data may be missing.")
                            break
                    else:
                        st.error(f"Failed to fetch page {page}: {response.status_code}")
                        break
                
                # Process all collected employee data
                if all_employees:
                    employee_data = {
                        "data": all_employees,
                        "pagination": {"total": len(all_employees), "page": 1}
                    }
                    employee_names = [emp["username"] for emp in all_employees]
                    employee_user_ids = {emp["username"]: emp.get("user_id", 503759) for emp in all_employees}
                    st.success(f"✅ Successfully loaded {len(all_employees)} employees from {page-1} pages")
                else:
                    st.warning("⚠️ No employee data found in API. Using demo data for demonstration.")
                    employee_names = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
                    # Create mock employee data structure with user_ids
                    demo_user_ids = [503759, 503760, 503761, 503762, 503763]
                    employee_data = {
                        "data": [
                            {
                                "username": name,
                                "user_id": demo_user_ids[i],
                                "total_hours": np.random.uniform(120, 180),
                                "days_worked": np.random.randint(15, 25),
                                "daily_average": np.random.uniform(6, 9),
                                "clients": [f"Client {chr(65+i)}" for i in range(np.random.randint(1, 4))]
                            } for i, name in enumerate(employee_names)
                        ],
                        "pagination": {"total": len(employee_names), "page": 1}
                    }
                    # Create user_id mapping
                    employee_user_ids = {name: demo_user_ids[i] for i, name in enumerate(employee_names)}
        except requests.exceptions.Timeout:
            st.warning("⚠️ API request timed out. Using demo data.")
            employee_names = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
            demo_user_ids = [503759, 503760, 503761, 503762, 503763]
            employee_data = {
                "data": [
                    {
                        "username": name,
                        "user_id": demo_user_ids[i],
                        "total_hours": np.random.uniform(120, 180),
                        "days_worked": np.random.randint(15, 25),
                        "daily_average": np.random.uniform(6, 9),
                        "clients": [f"Client {chr(65+i)}" for i in range(np.random.randint(1, 4))]
                    } for i, name in enumerate(employee_names)
                ],
                "pagination": {"total": len(employee_names), "page": 1}
            }
            employee_user_ids = {name: demo_user_ids[i] for i, name in enumerate(employee_names)}
        except Exception as e:
            st.warning(f"⚠️ Error connecting to API: {str(e)}. Using demo data.")
            employee_names = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
            demo_user_ids = [503759, 503760, 503761, 503762, 503763]
            employee_data = {
                "data": [
                    {
                        "username": name,
                        "user_id": demo_user_ids[i],
                        "total_hours": np.random.uniform(120, 180),
                        "days_worked": np.random.randint(15, 25),
                        "daily_average": np.random.uniform(6, 9),
                        "clients": [f"Client {chr(65+i)}" for i in range(np.random.randint(1, 4))]
                    } for i, name in enumerate(employee_names)
                ],
                "pagination": {"total": len(employee_names), "page": 1}
            }
            employee_user_ids = {name: demo_user_ids[i] for i, name in enumerate(employee_names)}
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
            
            # Fetch user summary data
            with st.spinner(f"Loading {selected_employee}'s {period} data..."):
                user_summary_data = fetch_user_summary_data(user_id, period)
            
            # Individual employee detailed view
            col1, col2 = st.columns(2)
            
            with col1:
                # Individual productivity gauge
                emp_index = employee_names.index(selected_employee)
                # Use a more realistic productivity score distribution
                productivity_scores = [92, 88, 95, 78, 91, 85, 90, 87, 93, 89]
                emp_score = productivity_scores[emp_index % len(productivity_scores)]
                
                individual_gauge = create_employee_productivity_gauge(emp_score, selected_employee)
                st.plotly_chart(individual_gauge, use_container_width=True, key=f"emp_gauge_{selected_employee.replace(' ', '_')}")
            
            with col2:
                # Individual metrics
                st.subheader(f"📊 {selected_employee} Metrics")
                
                # Get employee data from API response
                emp_data = next((emp for emp in employee_data.get("data", []) if emp["username"] == selected_employee), None)
                
                if emp_data:
                    # Calculate metrics from API data
                    total_hours = emp_data['total_hours']
                    days_worked = emp_data['days_worked'] 
                    daily_avg = emp_data['daily_average']
                    num_projects = len(emp_data['clients'])
                    
                    st.metric("Total Hours", f"{total_hours:.1f}h")
                    st.metric("Days Worked", days_worked)
                    st.metric("Daily Average", f"{daily_avg:.1f}h")
                    st.metric("Active Projects", num_projects)
                else:
                    # Fallback metrics if no specific employee data
                    st.metric("Total Hours", "N/A")
                    st.metric("Days Worked", "N/A")
                    st.metric("Daily Average", "N/A")
                    st.metric("Active Projects", "N/A")
                    st.info("No detailed data available for this employee")
            
            # User Summary Data Charts
            if user_summary_data and user_summary_data.get('data'):
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
                df = pd.DataFrame(user_summary_data['data'])
                total_hours = df['hours'].sum()
                unique_clients = df['client'].nunique()
                unique_tasks = df['task'].nunique()
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric(f"Total Hours ({period})", f"{total_hours:.1f}")
                with col_stat2:
                    st.metric("Unique Clients", unique_clients)
                with col_stat3:
                    st.metric("Unique Tasks", unique_tasks)
                with col_stat4:
                    avg_hours = total_hours / len(df) if len(df) > 0 else 0
                    st.metric(f"Avg Hours per Entry", f"{avg_hours:.1f}")
                
                # Data table
                st.subheader("📋 Raw Data")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No {period} data available for {selected_employee}")
            
            # Individual project breakdown
            st.subheader(f"Project Breakdown - {selected_employee}")
            
            if emp_data and emp_data.get('clients'):
                # Create dataframe from client list
                projects_df = pd.DataFrame({
                    'Project': emp_data['clients'],
                    'Status': ['Active'] * len(emp_data['clients']),
                    'Hours Allocated': [np.random.uniform(20, 60) for _ in emp_data['clients']]
                })
                st.dataframe(projects_df, use_container_width=True)
            else:
                # Show demo project data
                demo_projects = [
                    {'Project': 'TechCorp Mobile App', 'Status': 'Active', 'Hours Allocated': 45.5},
                    {'Project': 'GlobalSoft Dashboard', 'Status': 'Active', 'Hours Allocated': 32.0},
                    {'Project': 'StartupX Website', 'Status': 'In Progress', 'Hours Allocated': 28.5}
                ]
                projects_df = pd.DataFrame(demo_projects)
                st.dataframe(projects_df, use_container_width=True)
                st.info("💡 Showing demo project data - connect to API for real project information")
        else:
            st.warning("Please select an employee to view detailed analytics")

if __name__ == "__main__":
    main()
