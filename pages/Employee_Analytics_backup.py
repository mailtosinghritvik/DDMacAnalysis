import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
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
    """Create employee utilization comparison chart"""
    if not employee_data:
        return None
    
    # Mock employee utilization data
    utilization_data = [
        {'Employee': 'Alice Johnson', 'Planned Hours': 160, 'Actual Hours': 165, 'Utilization %': 103.1},
        {'Employee': 'Bob Smith', 'Planned Hours': 160, 'Actual Hours': 142, 'Utilization %': 88.8},
        {'Employee': 'Carol Davis', 'Planned Hours': 160, 'Actual Hours': 158, 'Utilization %': 98.8},
        {'Employee': 'David Wilson', 'Planned Hours': 160, 'Actual Hours': 170, 'Utilization %': 106.3},
        {'Employee': 'Emma Brown', 'Planned Hours': 160, 'Actual Hours': 155, 'Utilization %': 96.9}
    ]
    
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
        title='Employee Hours: Planned vs Actual',
        xaxis_title='Employees',
        yaxis_title='Hours',
        barmode='group',
        height=400
    )
    
    return fig, df

def create_employee_progress_timeline(api_data):
    """Create employee progress timeline"""
    if not api_data or 'daily_hours' not in api_data:
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

def create_employee_project_allocation(api_data, estimates_data):
    """Create employee project allocation analysis"""
    if not api_data:
        return None
    
    # Mock project allocation data
    allocation_data = [
        {'Employee': 'Alice Johnson', 'Project': 'TechCorp Mobile App', 'Hours': 45, 'Estimated': 40},
        {'Employee': 'Alice Johnson', 'Project': 'GlobalSoft Dashboard', 'Hours': 35, 'Estimated': 38},
        {'Employee': 'Bob Smith', 'Project': 'StartupX Website', 'Hours': 50, 'Estimated': 45},
        {'Employee': 'Bob Smith', 'Project': 'TechCorp Mobile App', 'Hours': 30, 'Estimated': 35},
        {'Employee': 'Carol Davis', 'Project': 'GlobalSoft Dashboard', 'Hours': 60, 'Estimated': 55},
        {'Employee': 'David Wilson', 'Project': 'StartupX Website', 'Hours': 40, 'Estimated': 42},
        {'Employee': 'Emma Brown', 'Project': 'TechCorp Mobile App', 'Hours': 55, 'Estimated': 50}
    ]
    
    df = pd.DataFrame(allocation_data)
    
    # Create sunburst chart
    fig = px.sunburst(
        df,
        path=['Employee', 'Project'],
        values='Hours',
        title='Employee Project Allocation'
    )
    
    fig.update_layout(height=500)
    return fig, df

def display_employee_kpis(api_data, estimates_data):
    """Display employee-level KPIs"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if api_data:
            active_employees = api_data.get('active_employees', 0)
            st.metric("Active Employees", active_employees)
        else:
            st.metric("Active Employees", "N/A")
    
    with col2:
        # Mock average utilization
        avg_utilization = 94.2
        st.metric("Avg Utilization", f"{avg_utilization:.1f}%", delta="2.3%")
    
    with col3:
        if api_data:
            total_hours = api_data.get('total_hours', 0)
            avg_hours_per_employee = total_hours / max(1, api_data.get('active_employees', 1))
            st.metric("Avg Hours/Employee", f"{avg_hours_per_employee:.1f}h")
        else:
            st.metric("Avg Hours/Employee", "N/A")
    
    with col4:
        # Mock productivity score
        team_productivity = 87.5
        st.metric("Team Productivity", f"{team_productivity:.1f}/100", delta="3.2")
    
    with col5:
        # Mock overtime percentage
        overtime_pct = 12.8
        st.metric("Overtime %", f"{overtime_pct:.1f}%", delta="-1.5%")

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
    
    # Display KPIs
    st.subheader("📊 Employee Performance KPIs")
    display_employee_kpis(api_data, estimates_data)
    
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
            util_chart, util_df = create_employee_utilization_chart(api_data)
            if util_chart:
                st.plotly_chart(util_chart, use_container_width=True)
        
        with col2:
            # Project allocation
            allocation_chart, allocation_df = create_employee_project_allocation(api_data, estimates_data)
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
        
        # Employee selector
        selected_employee = st.selectbox(
            "Select Employee",
            ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown']
        )
        
        # Individual employee detailed view
        col1, col2 = st.columns(2)
        
        with col1:
            # Individual productivity gauge
            emp_index = ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown'].index(selected_employee)
            emp_score = [92, 88, 95, 78, 91][emp_index]
            
            individual_gauge = create_employee_productivity_gauge(emp_score, selected_employee)
            st.plotly_chart(individual_gauge, use_container_width=True)
        
        with col2:
            # Individual metrics
            st.subheader(f"📊 {selected_employee} Metrics")
            
            # Mock individual data
            individual_data = {
                'Alice Johnson': {'hours': 165, 'projects': 3, 'utilization': 103.1, 'overtime': 5},
                'Bob Smith': {'hours': 142, 'projects': 2, 'utilization': 88.8, 'overtime': 2},
                'Carol Davis': {'hours': 158, 'projects': 1, 'utilization': 98.8, 'overtime': 0},
                'David Wilson': {'hours': 170, 'projects': 2, 'utilization': 106.3, 'overtime': 10},
                'Emma Brown': {'hours': 155, 'projects': 2, 'utilization': 96.9, 'overtime': 3}
            }
            
            emp_data = individual_data[selected_employee]
            
            st.metric("Total Hours This Month", f"{emp_data['hours']}h")
            st.metric("Active Projects", emp_data['projects'])
            st.metric("Utilization Rate", f"{emp_data['utilization']:.1f}%")
            st.metric("Overtime Hours", f"{emp_data['overtime']}h")
        
        # Individual project breakdown
        st.subheader(f"Project Breakdown - {selected_employee}")
        
        # Mock project data for selected employee
        project_data = {
            'Alice Johnson': [
                {'Project': 'TechCorp Mobile App', 'Hours': 45, 'Status': 'On Track'},
                {'Project': 'GlobalSoft Dashboard', 'Hours': 35, 'Status': 'Ahead'},
                {'Project': 'Internal Tools', 'Hours': 85, 'Status': 'On Track'}
            ],
            'Bob Smith': [
                {'Project': 'StartupX Website', 'Hours': 50, 'Status': 'Behind'},
                {'Project': 'TechCorp Mobile App', 'Hours': 30, 'Status': 'On Track'},
                {'Project': 'Documentation', 'Hours': 62, 'Status': 'Completed'}
            ]
        }
        
        if selected_employee in project_data:
            emp_projects_df = pd.DataFrame(project_data[selected_employee])
            st.dataframe(emp_projects_df, use_container_width=True)
        else:
            st.info("No detailed project data available for this employee")

if __name__ == "__main__":
    main()
</style>
""", unsafe_allow_html=True)

def create_utilization_radar_chart(employee_data):
    """Create radar chart for employee utilization metrics"""
    if employee_data.empty:
        return None
    
    categories = ['Utilization_%', 'Consistency_Score', 'Projects_Count', 'Clients_Count']
    
    # Normalize values to 0-100 scale
    normalized_data = employee_data.copy()
    normalized_data['Projects_Count'] = (normalized_data['Projects_Count'] / normalized_data['Projects_Count'].max() * 100).fillna(0)
    normalized_data['Clients_Count'] = (normalized_data['Clients_Count'] / normalized_data['Clients_Count'].max() * 100).fillna(0)
    
    fig = go.Figure()
    
    for _, employee in normalized_data.iterrows():
        values = [
            employee['Utilization_%'],
            employee['Consistency_Score'],
            employee['Projects_Count'],
            employee['Clients_Count']
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=['Utilization', 'Consistency', 'Project Diversity', 'Client Diversity'],
            fill='toself',
            name=employee['Employee']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Employee Performance Radar Chart",
        height=500
    )
    
    return fig

def create_workload_distribution_chart(data):
    """Create workload distribution chart across employees"""
    employee_workload = data.groupby(['employee', 'date'])['hours'].sum().reset_index()
    
    fig = px.box(
        employee_workload,
        x='employee',
        y='hours',
        title='Daily Workload Distribution by Employee',
        labels={'hours': 'Daily Hours', 'employee': 'Employee'}
    )
    
    # Add target line at 8 hours
    fig.add_hline(y=8, line_dash="dash", line_color="red", 
                  annotation_text="Target (8 hours/day)")
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )
    
    return fig

def create_employee_timeline_chart(data, employee_name):
    """Create timeline chart for specific employee"""
    emp_data = data[data['employee'] == employee_name].copy()
    
    if emp_data.empty:
        return None
    
    # Group by date and project
    daily_breakdown = emp_data.groupby(['date', 'project'])['hours'].sum().reset_index()
    
    fig = px.bar(
        daily_breakdown,
        x='date',
        y='hours',
        color='project',
        title=f'Daily Work Breakdown: {employee_name}',
        labels={'hours': 'Hours Worked', 'date': 'Date'}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        barmode='stack'
    )
    
    return fig

def create_productivity_trend_chart(data, employee_name):
    """Create productivity trend chart for employee"""
    emp_data = data[data['employee'] == employee_name].copy()
    
    if emp_data.empty:
        return None
    
    # Calculate weekly productivity
    emp_data['week'] = emp_data['date'].dt.to_period('W')
    weekly_hours = emp_data.groupby('week')['hours'].sum().reset_index()
    weekly_hours['week_str'] = weekly_hours['week'].astype(str)
    
    # Calculate moving average
    weekly_hours['moving_avg'] = weekly_hours['hours'].rolling(window=3, center=True).mean()
    
    fig = go.Figure()
    
    # Actual hours
    fig.add_trace(go.Scatter(
        x=weekly_hours['week_str'],
        y=weekly_hours['hours'],
        mode='lines+markers',
        name='Weekly Hours',
        line=dict(color='#1f77b4', width=3)
    ))
    
    # Moving average
    fig.add_trace(go.Scatter(
        x=weekly_hours['week_str'],
        y=weekly_hours['moving_avg'],
        mode='lines',
        name='Trend (3-week avg)',
        line=dict(color='#ff7f0e', width=2, dash='dash')
    ))
    
    # Target line
    fig.add_hline(y=40, line_dash="dot", line_color="red", 
                  annotation_text="Target (40 hrs/week)")
    
    fig.update_layout(
        title=f'Productivity Trend: {employee_name}',
        xaxis_title='Week',
        yaxis_title='Hours',
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig

def calculate_employee_insights(data, employee_name):
    """Calculate insights and recommendations for an employee"""
    emp_data = data[data['employee'] == employee_name]
    
    if emp_data.empty:
        return {}
    
    # Basic stats
    total_hours = emp_data['hours'].sum()
    working_days = emp_data['date'].nunique()
    avg_daily_hours = total_hours / working_days if working_days > 0 else 0
    
    # Projects and clients
    projects = emp_data['project'].nunique()
    clients = emp_data['client'].nunique()
    
    # Calculate streaks and patterns
    daily_hours = emp_data.groupby('date')['hours'].sum()
    
    # Find longest streak of consecutive work days
    work_dates = sorted(daily_hours.index)
    max_streak = 0
    current_streak = 1
    
    for i in range(1, len(work_dates)):
        if (work_dates[i] - work_dates[i-1]).days == 1:
            current_streak += 1
        else:
            max_streak = max(max_streak, current_streak)
            current_streak = 1
    max_streak = max(max_streak, current_streak)
    
    # Productivity insights
    high_productivity_days = len(daily_hours[daily_hours >= 8])
    low_productivity_days = len(daily_hours[daily_hours < 4])
    
    # Weekly pattern
    emp_data['day_of_week'] = emp_data['date'].dt.day_name()
    day_patterns = emp_data.groupby('day_of_week')['hours'].mean().round(2)
    best_day = day_patterns.idxmax()
    
    insights = {
        'total_hours': total_hours,
        'working_days': working_days,
        'avg_daily_hours': round(avg_daily_hours, 2),
        'projects_count': projects,
        'clients_count': clients,
        'max_streak': max_streak,
        'high_productivity_days': high_productivity_days,
        'low_productivity_days': low_productivity_days,
        'best_day': best_day,
        'best_day_hours': day_patterns[best_day],
        'day_patterns': day_patterns.to_dict()
    }
    
    return insights

def get_performance_category(utilization, consistency):
    """Categorize employee performance"""
    if utilization >= 80 and consistency >= 70:
        return "Excellent"
    elif utilization >= 60 and consistency >= 50:
        return "Good"
    else:
        return "Needs Improvement"

def main():
    """Main Employee Analytics Dashboard"""
    
    st.title("👥 Employee Analytics Dashboard")
    st.markdown("**Comprehensive employee performance monitoring, productivity analysis, and insights**")
    
    # Check if data is available
    if 'timesheet_data' not in st.session_state:
        st.warning("⚠️ No data uploaded yet. Please upload data on the Home page first.")
        
        if st.button("🏠 Go to Home Page"):
            st.switch_page("Home.py")
        return
    
    data = st.session_state['timesheet_data']
    data['date'] = pd.to_datetime(data['date'])
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔧 Employee Filters")
        
        # Employee selection
        all_employees = sorted(data['employee'].unique())
        selected_employees = st.multiselect(
            "Select Employees",
            all_employees,
            default=all_employees
        )
        
        # Date range filter
        min_date = data['date'].min().date()
        max_date = data['date'].max().date()
        
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Performance filter
        performance_filter = st.selectbox(
            "Filter by Performance",
            ["All", "Excellent", "Good", "Needs Improvement"]
        )
        
        # Apply filters
        if len(date_range) == 2:
            filtered_data = data[
                (data['employee'].isin(selected_employees)) &
                (data['date'].dt.date >= date_range[0]) &
                (data['date'].dt.date <= date_range[1])
            ]
        else:
            filtered_data = data[data['employee'].isin(selected_employees)]
    
    if filtered_data.empty:
        st.error("No data matches the selected filters. Please adjust your selection.")
        return
    
    # Generate analytics
    with st.spinner("Analyzing employee data..."):
        employee_overview = analyze_employees_overview(filtered_data)
        employee_performance = get_employee_performance_metrics(filtered_data)
    
    # Add performance categories
    if not employee_performance.empty:
        employee_performance['Performance_Category'] = employee_performance.apply(
            lambda row: get_performance_category(row['Utilization_%'], row['Consistency_Score']),
            axis=1
        )
        
        # Apply performance filter
        if performance_filter != "All":
            employee_performance = employee_performance[
                employee_performance['Performance_Category'] == performance_filter
            ]
    
    # Key Metrics Row
    st.subheader("📊 Team Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_employees = len(selected_employees)
        st.metric("Total Employees", total_employees)
    
    with col2:
        if not employee_performance.empty:
            avg_utilization = employee_performance['Utilization_%'].mean()
            st.metric("Avg Utilization", f"{avg_utilization:.1f}%", 
                     delta=f"Target: 80%")
        else:
            st.metric("Avg Utilization", "N/A")
    
    with col3:
        if not employee_performance.empty:
            high_performers = len(employee_performance[employee_performance['Performance_Category'] == 'Excellent'])
            st.metric("High Performers", high_performers, 
                     delta=f"{high_performers/len(employee_performance)*100:.0f}%")
        else:
            st.metric("High Performers", 0)
    
    with col4:
        total_hours = filtered_data['hours'].sum()
        avg_hours_per_employee = total_hours / len(selected_employees) if len(selected_employees) > 0 else 0
        st.metric("Avg Hours/Employee", f"{avg_hours_per_employee:.0f}")
    
    # Main Analytics Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Team Overview", 
        "📊 Individual Analysis", 
        "⚡ Performance Metrics", 
        "🎯 Productivity Insights"
    ])
    
    with tab1:
        st.subheader("Team Performance Overview")
        
        if not employee_performance.empty:
            # Performance distribution
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance category pie chart
                perf_counts = employee_performance['Performance_Category'].value_counts()
                fig_perf = px.pie(
                    values=perf_counts.values,
                    names=perf_counts.index,
                    title='Team Performance Distribution',
                    color_discrete_map={
                        'Excellent': '#28a745',
                        'Good': '#17a2b8',
                        'Needs Improvement': '#ffc107'
                    }
                )
                st.plotly_chart(fig_perf, use_container_width=True)
            
            with col2:
                # Utilization vs Consistency scatter
                fig_scatter = px.scatter(
                    employee_performance,
                    x='Utilization_%',
                    y='Consistency_Score',
                    size='Total_Hours',
                    color='Performance_Category',
                    hover_data=['Employee'],
                    title='Utilization vs Consistency',
                    color_discrete_map={
                        'Excellent': '#28a745',
                        'Good': '#17a2b8',
                        'Needs Improvement': '#ffc107'
                    }
                )
                fig_scatter.add_vline(x=80, line_dash="dash", line_color="red")
                fig_scatter.add_hline(y=70, line_dash="dash", line_color="red")
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Workload distribution
            workload_fig = create_workload_distribution_chart(filtered_data)
            st.plotly_chart(workload_fig, use_container_width=True)
            
            # Performance radar chart
            if len(employee_performance) <= 10:  # Only show radar for small teams
                radar_fig = create_utilization_radar_chart(employee_performance)
                if radar_fig:
                    st.plotly_chart(radar_fig, use_container_width=True)
            
            # Employee performance cards
            st.subheader("Individual Performance Cards")
            
            cols = st.columns(3)
            for idx, (_, emp) in enumerate(employee_performance.iterrows()):
                col_idx = idx % 3
                with cols[col_idx]:
                    perf_class = emp['Performance_Category'].lower().replace(' ', '-')
                    
                    st.markdown(f"""
                    <div class="employee-card performance-{perf_class}">
                        <h4>{emp['Employee']}</h4>
                        <p><strong>Utilization:</strong> {emp['Utilization_%']:.1f}%</p>
                        <p><strong>Consistency:</strong> {emp['Consistency_Score']:.1f}/100</p>
                        <p><strong>Total Hours:</strong> {emp['Total_Hours']:.0f}</p>
                        <p><strong>Projects:</strong> {emp['Projects_Count']} | <strong>Clients:</strong> {emp['Clients_Count']}</p>
                        <p><strong>Status:</strong> {emp['Performance_Category']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No employee performance data available for the selected filters.")
    
    with tab2:
        st.subheader("Individual Employee Analysis")
        
        # Employee selector
        analysis_employee = st.selectbox(
            "Select Employee for Detailed Analysis",
            selected_employees
        )
        
        if analysis_employee and analysis_employee in filtered_data['employee'].values:
            # Employee insights
            insights = calculate_employee_insights(filtered_data, analysis_employee)
            
            # Key metrics for selected employee
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Hours", f"{insights['total_hours']:.0f}")
            
            with col2:
                st.metric("Working Days", insights['working_days'])
            
            with col3:
                st.metric("Daily Average", f"{insights['avg_daily_hours']:.1f} hrs")
            
            with col4:
                st.metric("Max Work Streak", f"{insights['max_streak']} days")
            
            # Charts for individual employee
            col1, col2 = st.columns(2)
            
            with col1:
                # Timeline chart
                timeline_fig = create_employee_timeline_chart(filtered_data, analysis_employee)
                if timeline_fig:
                    st.plotly_chart(timeline_fig, use_container_width=True)
            
            with col2:
                # Productivity trend
                trend_fig = create_productivity_trend_chart(filtered_data, analysis_employee)
                if trend_fig:
                    st.plotly_chart(trend_fig, use_container_width=True)
            
            # Daily patterns analysis
            st.subheader("Work Pattern Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Day of week pattern
                day_pattern_df = pd.DataFrame(
                    list(insights['day_patterns'].items()),
                    columns=['Day', 'Avg_Hours']
                )
                
                fig_days = px.bar(
                    day_pattern_df,
                    x='Day',
                    y='Avg_Hours',
                    title=f'Average Hours by Day of Week',
                    color='Avg_Hours',
                    color_continuous_scale='Blues'
                )
                fig_days.update_layout(showlegend=False)
                st.plotly_chart(fig_days, use_container_width=True)
            
            with col2:
                # Project distribution for this employee
                emp_project_hours = filtered_data[
                    filtered_data['employee'] == analysis_employee
                ].groupby('project')['hours'].sum().reset_index()
                
                fig_projects = px.pie(
                    emp_project_hours,
                    values='hours',
                    names='project',
                    title='Time Distribution by Project'
                )
                st.plotly_chart(fig_projects, use_container_width=True)
            
            # Detailed work breakdown
            st.subheader("Detailed Work Breakdown")
            
            frequency = st.radio("View by:", ["Daily", "Weekly"], horizontal=True)
            detailed_data = analyze_employee_detailed(
                filtered_data, 
                analysis_employee, 
                frequency.lower()
            )
            
            if not detailed_data.empty:
                st.dataframe(detailed_data, use_container_width=True)
            
            # Insights and recommendations
            st.subheader("Performance Insights & Recommendations")
            
            # Generate insights based on data
            recommendations = []
            
            if insights['avg_daily_hours'] < 6:
                recommendations.append("🔴 **Low Utilization**: Consider increasing daily hour targets or reviewing workload allocation")
            elif insights['avg_daily_hours'] > 10:
                recommendations.append("⚠️ **High Workload**: Monitor for burnout risk and consider workload redistribution")
            
            if insights['low_productivity_days'] > insights['working_days'] * 0.3:
                recommendations.append("📊 **Consistency**: High number of low-productivity days - investigate potential blockers")
            
            if insights['projects_count'] > 5:
                recommendations.append("🎯 **Focus**: Working on many projects simultaneously - consider prioritization")
            elif insights['projects_count'] == 1:
                recommendations.append("🔄 **Diversity**: Single project focus - consider cross-training opportunities")
            
            # Best performance day insight
            st.info(f"💡 **Peak Performance**: {analysis_employee} is most productive on {insights['best_day']}s "
                   f"(avg {insights['best_day_hours']:.1f} hours)")
            
            if recommendations:
                for rec in recommendations:
                    st.markdown(rec)
            else:
                st.success("✅ Performance metrics are within optimal ranges!")
    
    with tab3:
        st.subheader("Performance Metrics & Benchmarking")
        
        if not employee_performance.empty:
            # Performance metrics table
            st.markdown("#### Detailed Performance Metrics")
            
            # Style the performance table
            def style_utilization(val):
                if val >= 80:
                    return 'background-color: #d4edda'
                elif val >= 60:
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #f8d7da'
            
            def style_consistency(val):
                if val >= 70:
                    return 'background-color: #d4edda'
                elif val >= 50:
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #f8d7da'
            
            styled_performance = employee_performance.style.applymap(
                style_utilization, subset=['Utilization_%']
            ).applymap(
                style_consistency, subset=['Consistency_Score']
            )
            
            st.dataframe(styled_performance, use_container_width=True)
            
            # Performance distribution charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Utilization distribution
                fig_util_dist = px.histogram(
                    employee_performance,
                    x='Utilization_%',
                    nbins=10,
                    title='Utilization Rate Distribution',
                    labels={'count': 'Number of Employees'}
                )
                fig_util_dist.add_vline(x=80, line_dash="dash", line_color="red",
                                       annotation_text="Target (80%)")
                st.plotly_chart(fig_util_dist, use_container_width=True)
            
            with col2:
                # Hours distribution
                fig_hours_dist = px.histogram(
                    employee_performance,
                    x='Total_Hours',
                    nbins=10,
                    title='Total Hours Distribution',
                    labels={'count': 'Number of Employees'}
                )
                st.plotly_chart(fig_hours_dist, use_container_width=True)
            
            # Top performers
            st.subheader("🏆 Top Performers")
            
            top_by_utilization = employee_performance.nlargest(3, 'Utilization_%')
            top_by_hours = employee_performance.nlargest(3, 'Total_Hours')
            top_by_consistency = employee_performance.nlargest(3, 'Consistency_Score')
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Highest Utilization**")
                for _, emp in top_by_utilization.iterrows():
                    st.success(f"{emp['Employee']}: {emp['Utilization_%']:.1f}%")
            
            with col2:
                st.markdown("**Most Hours Worked**")
                for _, emp in top_by_hours.iterrows():
                    st.info(f"{emp['Employee']}: {emp['Total_Hours']:.0f} hrs")
            
            with col3:
                st.markdown("**Most Consistent**")
                for _, emp in top_by_consistency.iterrows():
                    st.success(f"{emp['Employee']}: {emp['Consistency_Score']:.1f}/100")
    
    with tab4:
        st.subheader("🎯 Productivity Insights & Trends")
        
        # Team productivity trends
        st.markdown("#### Team Productivity Trends")
        
        # Weekly team productivity
        filtered_data['week'] = filtered_data['date'].dt.to_period('W')
        weekly_team_hours = filtered_data.groupby('week')['hours'].sum().reset_index()
        weekly_team_hours['week_str'] = weekly_team_hours['week'].astype(str)
        
        fig_team_trend = px.line(
            weekly_team_hours,
            x='week_str',
            y='hours',
            title='Team Weekly Hours Trend',
            markers=True
        )
        fig_team_trend.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig_team_trend, use_container_width=True)
        
        # Project diversity analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Employee project diversity
            project_diversity = filtered_data.groupby('employee')['project'].nunique().reset_index()
            project_diversity.columns = ['Employee', 'Project_Count']
            
            fig_diversity = px.bar(
                project_diversity,
                x='Employee',
                y='Project_Count',
                title='Project Diversity by Employee',
                color='Project_Count',
                color_continuous_scale='Blues'
            )
            fig_diversity.update_layout(xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig_diversity, use_container_width=True)
        
        with col2:
            # Client diversity
            client_diversity = filtered_data.groupby('employee')['client'].nunique().reset_index()
            client_diversity.columns = ['Employee', 'Client_Count']
            
            fig_client_div = px.bar(
                client_diversity,
                x='Employee',
                y='Client_Count',
                title='Client Diversity by Employee',
                color='Client_Count',
                color_continuous_scale='Greens'
            )
            fig_client_div.update_layout(xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig_client_div, use_container_width=True)
        
        # Productivity insights
        st.markdown("#### Key Productivity Insights")
        
        # Calculate insights
        total_employees = len(selected_employees)
        avg_daily_hours = filtered_data.groupby(['employee', 'date'])['hours'].sum().mean()
        peak_day = filtered_data.groupby(filtered_data['date'].dt.day_name())['hours'].sum().idxmax()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-highlight">
                <h4>📊 Team Average</h4>
                <p><strong>{avg_daily_hours:.1f} hours/day</strong></p>
                <p>Average daily hours across all team members</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-highlight">
                <h4>📅 Peak Performance Day</h4>
                <p><strong>{peak_day}</strong></p>
                <p>Day with highest team productivity</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            active_ratio = (filtered_data['date'].nunique() / 
                          ((filtered_data['date'].max() - filtered_data['date'].min()).days + 1)) * 100
            st.markdown(f"""
            <div class="metric-highlight">
                <h4>⚡ Activity Ratio</h4>
                <p><strong>{active_ratio:.1f}%</strong></p>
                <p>Percentage of days with logged work</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
