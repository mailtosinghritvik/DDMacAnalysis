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
        return None, None
    
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

def create_employee_project_allocation(api_data, estimates_data):
    """Create employee project allocation analysis"""
    if not api_data:
        return None, None
    
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
            ],
            'Carol Davis': [
                {'Project': 'GlobalSoft Dashboard', 'Hours': 158, 'Status': 'On Track'}
            ],
            'David Wilson': [
                {'Project': 'StartupX Website', 'Hours': 90, 'Status': 'Behind'},
                {'Project': 'Infrastructure', 'Hours': 80, 'Status': 'On Track'}
            ],
            'Emma Brown': [
                {'Project': 'TechCorp Mobile App', 'Hours': 75, 'Status': 'On Track'},
                {'Project': 'Testing Framework', 'Hours': 80, 'Status': 'Ahead'}
            ]
        }
        
        if selected_employee in project_data:
            emp_projects_df = pd.DataFrame(project_data[selected_employee])
            st.dataframe(emp_projects_df, use_container_width=True)
        else:
            st.info("No detailed project data available for this employee")

if __name__ == "__main__":
    main()
