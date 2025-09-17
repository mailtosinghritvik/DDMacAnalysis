import streamlit as st
import time
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Import our custom utilities
from utils.time_analysis import (
    generate_sample_timesheet_data,
    analyze_clients,
    analyze_employees_overview,
    get_project_health_metrics,
    get_employee_performance_metrics
)

# Set page configuration
st.set_page_config(
    page_title="DDMac Analytics - Time Tracking & Project Management",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-healthy { color: #28a745; font-weight: bold; }
    .status-risk { color: #ffc107; font-weight: bold; }
    .status-critical { color: #dc3545; font-weight: bold; }
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_health_score_gauge(score, title):
    """Create a gauge chart for health scores"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 70},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "lightgreen"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}))
    
    fig.update_layout(height=300)
    return fig

def create_utilization_chart(performance_data):
    """Create employee utilization chart"""
    fig = px.bar(
        performance_data,
        x='Employee',
        y='Utilization_%',
        color='Utilization_%',
        color_continuous_scale='RdYlGn',
        title='Employee Utilization Rate (%)',
        labels={'Utilization_%': 'Utilization %'}
    )
    
    fig.add_hline(y=80, line_dash="dash", line_color="red", 
                  annotation_text="Target Utilization (80%)")
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=False
    )
    
    return fig

def create_project_timeline(health_data):
    """Create project health timeline"""
    # Create color mapping for status
    color_map = {
        'Healthy': '#28a745',
        'At Risk': '#ffc107', 
        'Critical': '#dc3545'
    }
    
    fig = px.scatter(
        health_data,
        x='Total_Hours',
        y='Health_Score',
        size='Team_Size',
        color='Status',
        color_discrete_map=color_map,
        hover_data=['Project', 'Avg_Weekly_Hours'],
        title='Project Health vs Total Hours Invested'
    )
    
    fig.update_layout(height=400)
    return fig

def main():
    """Main DDMac Analytics Dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">⏱️ DDMac Analytics Dashboard</h1>', 
                unsafe_allow_html=True)
    st.markdown("**Comprehensive Time Tracking, Project Health & Employee Analytics**")
    
    # Sidebar for data upload and navigation
    with st.sidebar:
        st.header("📊 Data Management")
        
        # Data upload section
        uploaded_file = st.file_uploader(
            "Upload Time Tracking Data",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your timesheet data with columns: employee, client, project, date, hours"
        )
        
        # Sample data generator
        st.markdown("---")
        st.subheader("🧪 Demo Mode")
        if st.button("Generate Sample Data", type="secondary"):
            sample_data = generate_sample_timesheet_data(num_employees=6, num_days=90)
            st.session_state['timesheet_data'] = sample_data
            st.session_state['data_source'] = 'sample'
            st.success(f"Generated {len(sample_data)} records for {sample_data['employee'].nunique()} employees")
            st.rerun()
        
        # Data source info
        if 'timesheet_data' in st.session_state:
            data = st.session_state['timesheet_data']
            source = st.session_state.get('data_source', 'uploaded')
            
            st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
            st.markdown("**📈 Current Dataset:**")
            st.metric("Records", f"{len(data):,}")
            st.metric("Employees", data['employee'].nunique())
            st.metric("Projects", data['project'].nunique())
            st.metric("Clients", data['client'].nunique())
            
            # Convert date column to datetime for calculation
            data_dates = pd.to_datetime(data['date'])
            date_range_days = (data_dates.max() - data_dates.min()).days
            st.metric("Date Range", f"{date_range_days} days")
            
            st.markdown(f"**Source:** {'Sample Data' if source == 'sample' else 'Uploaded File'}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("� Quick Navigation")
        st.markdown("• **Dashboard**: Overview & Key Metrics")
        st.markdown("• **Project Analytics**: Project health & performance")
        st.markdown("• **Employee Analytics**: Individual performance")
        st.markdown("• **Client Analytics**: Client profitability")
        st.markdown("• **Predictive Analytics**: Forecasting & insights")
    
    # Handle file upload
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_excel(uploaded_file)
            
            # Validate required columns
            required_cols = ['employee', 'client', 'project', 'date', 'hours']
            if all(col in data.columns for col in required_cols):
                st.session_state['timesheet_data'] = data
                st.session_state['data_source'] = 'uploaded'
                st.success(f"✅ Data uploaded successfully! {len(data)} records loaded.")
            else:
                st.error(f"❌ Missing required columns. Expected: {required_cols}")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.stop()
    
    # Check if data is available
    if 'timesheet_data' not in st.session_state:
        # Welcome screen when no data
        st.markdown("## 👋 Welcome to DDMac Analytics")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🚀 Get Started
            
            **DDMac Analytics** provides comprehensive insights into your team's time tracking data:
            
            - **📊 Project Health Monitoring**: Track project status and identify risks
            - **👥 Employee Performance Analytics**: Monitor utilization and productivity
            - **💼 Client Profitability Analysis**: Understand client relationships
            - **🔮 Predictive Analytics**: Forecast project completion and resource needs
            
            **To begin:**
            1. Upload your timesheet CSV/Excel file using the sidebar
            2. Or generate sample data to explore the features
            
            **Expected Data Format:**
            - `employee`: Employee name
            - `client`: Client name  
            - `project`: Project name
            - `date`: Work date (YYYY-MM-DD)
            - `hours`: Hours worked
            """)
        
        with col2:
            st.info("💡 **Pro Tip**: Use the 'Generate Sample Data' button to explore all features with realistic demo data!")
            
            st.markdown("### 📋 Key Features")
            st.markdown("✅ Real-time dashboards")
            st.markdown("✅ Project health scoring")
            st.markdown("✅ Employee utilization tracking")
            st.markdown("✅ Client profitability analysis")
            st.markdown("✅ Predictive analytics")
            st.markdown("✅ Custom visualizations")
        
        return
    
    # Main dashboard with data
    data = st.session_state['timesheet_data']
    
    # Convert date column to datetime if it's not already
    data['date'] = pd.to_datetime(data['date'])
    
    # Generate analytics
    with st.spinner("Analyzing data..."):
        client_summary = analyze_clients(data)
        employee_overview = analyze_employees_overview(data)
        project_health = get_project_health_metrics(data)
        employee_performance = get_employee_performance_metrics(data)
    
    # Key Metrics Row
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_hours = data['hours'].sum()
        st.metric(
            "Total Hours Tracked",
            f"{total_hours:,.0f}",
            delta=f"+{total_hours/30:.0f}/day avg"
        )
    
    with col2:
        active_projects = data['project'].nunique()
        healthy_projects = len(project_health[project_health['Status'] == 'Healthy'])
        st.metric(
            "Active Projects",
            active_projects,
            delta=f"{healthy_projects} healthy"
        )
    
    with col3:
        avg_utilization = employee_performance['Utilization_%'].mean()
        st.metric(
            "Avg Team Utilization",
            f"{avg_utilization:.1f}%",
            delta=f"Target: 80%"
        )
    
    with col4:
        avg_health_score = project_health['Health_Score'].mean()
        st.metric(
            "Avg Project Health",
            f"{avg_health_score:.0f}/100",
            delta="Health Score"
        )
    
    with col5:
        revenue_per_hour = 150  # Assumed rate
        estimated_revenue = total_hours * revenue_per_hour
        st.metric(
            "Est. Revenue",
            f"${estimated_revenue:,.0f}",
            delta=f"@${revenue_per_hour}/hr"
        )
    
    # Charts Row 1
    st.subheader("📈 Performance Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Employee utilization chart
        util_fig = create_utilization_chart(employee_performance)
        st.plotly_chart(util_fig, use_container_width=True)
    
    with col2:
        # Project health scatter
        health_fig = create_project_timeline(project_health)
        st.plotly_chart(health_fig, use_container_width=True)
    
    # Charts Row 2
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Overall health gauge
        overall_health = project_health['Health_Score'].mean()
        gauge_fig = create_health_score_gauge(overall_health, "Overall Project Health")
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    with col2:
        # Client hours distribution
        client_hours = data.groupby('client')['hours'].sum().reset_index()
        pie_fig = px.pie(
            client_hours, 
            values='hours', 
            names='client',
            title='Hours Distribution by Client'
        )
        pie_fig.update_layout(height=300)
        st.plotly_chart(pie_fig, use_container_width=True)
    
    with col3:
        # Weekly trend
        data['week'] = data['date'].dt.to_period('W').astype(str)
        weekly_hours = data.groupby('week')['hours'].sum().reset_index()
        
        trend_fig = px.line(
            weekly_hours,
            x='week',
            y='hours',
            title='Weekly Hours Trend',
            markers=True
        )
        trend_fig.update_layout(height=300, xaxis_tickangle=-45)
        st.plotly_chart(trend_fig, use_container_width=True)
    
    # Data Tables Section
    st.subheader("📋 Detailed Analytics")
    
    tab1, tab2, tab3 = st.tabs(["🏢 Project Health", "👥 Employee Performance", "💼 Client Summary"])
    
    with tab1:
        st.markdown("### Project Health Dashboard")
        
        # Color-code the status
        def color_status(val):
            if val == 'Healthy':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'At Risk':
                return 'background-color: #fff3cd; color: #856404'
            else:
                return 'background-color: #f8d7da; color: #721c24'
        
        styled_health = project_health.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_health, use_container_width=True)
        
        # Project health insights
        critical_projects = project_health[project_health['Status'] == 'Critical']
        if len(critical_projects) > 0:
            st.warning(f"⚠️ {len(critical_projects)} project(s) need immediate attention:")
            for _, proj in critical_projects.iterrows():
                st.error(f"• **{proj['Project']}**: Health Score {proj['Health_Score']:.0f}/100")
    
    with tab2:
        st.markdown("### Employee Performance Metrics")
        st.dataframe(employee_performance, use_container_width=True)
        
        # Performance insights
        low_util = employee_performance[employee_performance['Utilization_%'] < 60]
        if len(low_util) > 0:
            st.info("📊 Employees with low utilization (< 60%):")
            for _, emp in low_util.iterrows():
                st.write(f"• **{emp['Employee']}**: {emp['Utilization_%']:.1f}% utilization")
    
    with tab3:
        st.markdown("### Client Analysis")
        st.dataframe(client_summary, use_container_width=True)
        
        # Client insights
        top_client = client_summary.loc[client_summary['Total_Hours'].idxmax()]
        st.success(f"🏆 **Top Client**: {top_client['Client']} ({top_client['Total_Hours']:.0f} hours)")

if __name__ == "__main__":
    main()
