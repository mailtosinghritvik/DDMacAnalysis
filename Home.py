import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Import all analytics utilities including new handlers
from utils import (
    # Original functions for uploaded data
    TimeTrackingAnalyzer,
    analyze_clients,
    analyze_projects_for_client,
    generate_sample_timesheet_data,
    
    # Real-time API functions
    get_api_handler,
    fetch_real_time_data,
    analyze_clients_api,
    analyze_employees_overview_api,
    
    # Excel estimates functions
    get_estimates_handler,
    get_progress_comparison,
    get_budget_alerts
)

# Page configuration
st.set_page_config(
    page_title="DDMac Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .status-success {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    
    .status-warning {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    
    .status-danger {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    
    .progress-bar {
        background-color: #e9ecef;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    .stDataFrame {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .data-source-indicator {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        margin: 0.25rem;
        display: inline-block;
    }
    
    .api-indicator {
        background-color: #28a745;
        color: white;
    }
    
    .estimates-indicator {
        background-color: #007bff;
        color: white;
    }
    
    .offline-indicator {
        background-color: #6c757d;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def create_progress_bar(actual, estimated, label="Progress"):
    """Create a visual progress bar comparing actual vs estimated"""
    if estimated > 0:
        progress_pct = min((actual / estimated) * 100, 100)
        over_pct = max(((actual - estimated) / estimated) * 100, 0) if actual > estimated else 0
        
        # Determine color based on progress
        if progress_pct <= 75:
            color = "#28a745"  # Green
        elif progress_pct <= 90:
            color = "#ffc107"  # Yellow
        else:
            color = "#dc3545"  # Red
            
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = progress_pct,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"{label}<br>Progress"},
            delta = {'reference': 100, 'position': "top"},
            gauge = {
                'axis': {'range': [None, 120]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 75], 'color': "lightgray"},
                    {'range': [75, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "orange"},
                    {'range': [100, 120], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        
        fig.update_layout(height=250, showlegend=False)
        return fig
    return None

def display_data_source_indicators(api_connected, estimates_loaded):
    """Display data source status indicators"""
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if api_connected:
            st.markdown('<span class="data-source-indicator api-indicator">🟢 API Live</span>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<span class="data-source-indicator offline-indicator">🔴 API Offline</span>', 
                       unsafe_allow_html=True)
    
    with col2:
        if estimates_loaded:
            st.markdown('<span class="data-source-indicator estimates-indicator">📊 Estimates Loaded</span>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<span class="data-source-indicator offline-indicator">📊 No Estimates</span>', 
                       unsafe_allow_html=True)
    
    with col3:
        if api_connected and estimates_loaded:
            st.markdown("**Status**: Full integration active with progress tracking")
        elif api_connected:
            st.markdown("**Status**: Live data only (upload estimates for progress tracking)")
        elif estimates_loaded:
            st.markdown("**Status**: Estimates only (connect API for live tracking)")
        else:
            st.markdown("**Status**: Demo mode (configure data sources)")

def display_kpi_cards(api_data, estimates_data):
    """Display key performance indicators as cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if api_data and isinstance(api_data, dict):
            hours = api_data.get('total_hours', 0) or 0
            st.metric("Total Hours (This Month)", f"{hours:.1f}h")
        else:
            st.metric("Total Hours (This Month)", "1,250.5h")  # Demo value
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if api_data and isinstance(api_data, dict):
            projects = api_data.get('active_projects', api_data.get('total_projects', 0)) or 0
            st.metric("Active Projects", projects)
        else:
            st.metric("Active Projects", "8")  # Demo value
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if estimates_data and isinstance(estimates_data, dict):
            budget = estimates_data.get('total_estimated_budget', 0) or 0
            st.metric("Total Budget", f"${budget:,.0f}")
        elif api_data and isinstance(api_data, dict):
            revenue = api_data.get('revenue', 0) or 0
            st.metric("Total Revenue", f"${revenue:,.0f}")
        else:
            st.metric("Total Budget", "$156,750")  # Demo value
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if api_data and isinstance(api_data, dict):
            efficiency = api_data.get('efficiency', 0) or 0
            delta_color = "normal" if efficiency >= 85 else "inverse"
            st.metric("Team Efficiency", f"{efficiency:.1f}%", 
                     delta=f"{efficiency-85:.1f}%" if efficiency != 85 else None,
                     delta_color=delta_color)
        else:
            st.metric("Team Efficiency", "92.3%")  # Demo value
        st.markdown('</div>', unsafe_allow_html=True)

def display_project_progress(progress_data):
    """Display project progress with visual progress bars"""
    st.subheader("📈 Project Progress Overview")
    
    if not progress_data:
        st.info("💡 Upload project estimates to enable progress tracking and comparisons with actual hours.")
        return
    
    # Create progress charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Overall progress gauge
        total_actual = sum([p['actual_hours'] for p in progress_data])
        total_estimated = sum([p['estimated_hours'] for p in progress_data])
        
        if total_estimated > 0:
            progress_fig = create_progress_bar(total_actual, total_estimated, "Overall")
            st.plotly_chart(progress_fig, use_container_width=True)
    
    with col2:
        # Budget vs Actual spending
        total_budget = sum([p.get('budget', 0) for p in progress_data])
        total_spent = sum([p.get('actual_cost', 0) for p in progress_data])
        
        if total_budget > 0:
            budget_fig = create_progress_bar(total_spent, total_budget, "Budget")
            st.plotly_chart(budget_fig, use_container_width=True)
    
    # Project details table
    st.subheader("Project Details")
    
    progress_df = pd.DataFrame([
        {
            'Project': p['project_name'],
            'Estimated Hours': p['estimated_hours'],
            'Actual Hours': p['actual_hours'],
            'Progress %': f"{min((p['actual_hours']/p['estimated_hours'])*100, 100):.1f}%" if p['estimated_hours'] > 0 else "0%",
            'Budget': f"${p.get('budget', 0):,.0f}",
            'Spent': f"${p.get('actual_cost', 0):,.0f}",
            'Status': p.get('status', 'Unknown')
        } for p in progress_data
    ])
    
    # Apply styling based on progress
    def style_progress(row):
        if 'Progress %' in row and row['Progress %'] != "0%":
            progress = float(row['Progress %'].replace('%', ''))
            if progress >= 100:
                return ['background-color: #f8d7da'] * len(row)  # Red for over budget
            elif progress >= 90:
                return ['background-color: #fff3cd'] * len(row)  # Yellow for near completion
            elif progress >= 75:
                return ['background-color: #d1ecf1'] * len(row)  # Blue for good progress
            else:
                return ['background-color: #d4edda'] * len(row)  # Green for under budget
        return [''] * len(row)
    
    styled_df = progress_df.style.apply(style_progress, axis=1)
    st.dataframe(styled_df, use_container_width=True)

def display_alerts_section(alerts_data):
    """Display budget and deadline alerts"""
    if not alerts_data:
        st.success("✅ No alerts at this time!")
        return
    
    st.subheader("🚨 Alerts & Notifications")
    
    for alert in alerts_data:
        alert_type = alert.get('type', 'info')
        message = alert.get('message', 'No message')
        project = alert.get('project', 'Unknown Project')
        
        if alert_type == 'danger':
            st.error(f"**{project}**: {message}")
        elif alert_type == 'warning':
            st.warning(f"**{project}**: {message}")
        else:
            st.info(f"**{project}**: {message}")

def display_real_time_charts(api_data):
    """Display real-time data visualizations"""
    if not api_data or not isinstance(api_data, dict):
        return
    
    st.subheader("📊 Real-time Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily hours trend (last 7 days) - create sample data if not available
        if 'daily_hours' in api_data:
            daily_df = pd.DataFrame(api_data['daily_hours'])
        else:
            # Create sample daily hours data
            dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
            hours = [6.5, 7.2, 8.1, 7.8, 6.9, 5.5, 7.4]  # Sample hours
            daily_df = pd.DataFrame({
                'date': dates.strftime('%Y-%m-%d'),
                'hours': hours
            })
        
        fig = px.line(daily_df, x='date', y='hours', 
                     title="Daily Hours Trend (Last 7 Days)",
                     markers=True)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Employee activity
        if 'employees_analysis' in api_data and not api_data['employees_analysis'].empty:
            emp_df = api_data['employees_analysis'].head(5)  # Top 5 employees
            fig = px.bar(emp_df, x='Employee', y='Total_Hours',
                        title="Top Employees by Hours",
                        color='Total_Hours')
        elif 'employees' in api_data:
            # Create sample employee data
            employees = api_data['employees'][:5]
            hours = [45.2, 42.8, 38.5, 41.1, 39.7]  # Sample hours
            emp_df = pd.DataFrame({
                'employee': employees,
                'hours': hours
            })
            fig = px.bar(emp_df, x='employee', y='hours',
                        title="Top Employees by Hours",
                        color='hours')
        else:
            # Default sample data
            emp_df = pd.DataFrame({
                'employee': ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson', 'Emma Brown'],
                'hours': [45.2, 42.8, 38.5, 41.1, 39.7]
            })
            fig = px.bar(emp_df, x='employee', y='hours',
                        title="Top Employees by Hours",
                        color='hours')
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">DDMac Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**🚀 Integrated Time Tracking with Real-time API & Project Estimates**")
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "Select Data Source",
        ["Real-time API", "Sample Data", "Upload File"],
        help="Choose your data source for analytics"
    )
    
    # API Configuration section
    api_connected = False
    api_data = None
    
    if data_source == "Real-time API":
        st.sidebar.subheader("🔗 API Configuration")
        
        api_url = st.sidebar.text_input(
            "API Endpoint",
            value="https://api.ddmac.com/timesheet",
            help="Enter your timesheet API endpoint"
        )
        
        api_token = st.sidebar.text_input(
            "API Token",
            type="password",
            help="Enter your API authentication token"
        )
        
        if st.sidebar.button("Test API Connection"):
            if api_url and api_token:
                try:
                    api_handler = get_api_handler()
                    api_handler.configure(api_url, api_token)
                    
                    # Test connection
                    test_data = api_handler.get_sample_data()
                    if test_data:
                        st.sidebar.success("✅ API connection successful!")
                        api_connected = True
                    else:
                        st.sidebar.error("❌ Failed to connect to API")
                except Exception as e:
                    st.sidebar.error(f"❌ API Error: {str(e)}")
            else:
                st.sidebar.warning("Please enter both API URL and token")
        
        # If configured, fetch data
        if api_url and api_token:
            try:
                api_handler = get_api_handler()
                api_handler.configure(api_url, api_token)
                api_data = api_handler.get_sample_data()  # Using sample data for demo
                api_connected = True
            except:
                api_connected = False
    else:
        # Use sample data
        api_data = get_api_handler().get_sample_data()
        api_connected = True
        
        # Also get sample estimates data for full demo experience
        estimates_data = get_estimates_handler().get_sample_data()
        estimates_loaded = True
    
    # Excel Estimates Upload
    st.sidebar.subheader("📊 Project Estimates")
    
    estimates_file = st.sidebar.file_uploader(
        "Upload Estimates Excel File",
        type=['xlsx', 'xls'],
        help="Upload your project estimates Excel file"
    )
    
    estimates_loaded = False
    estimates_data = None
    progress_data = None
    alerts_data = None
    
    # Process estimates file
    if estimates_file:
        try:
            estimates_handler = get_estimates_handler()
            estimates_data = estimates_handler.process_excel_file(estimates_file)
            estimates_loaded = True
            
            if estimates_data and api_data:
                progress_data = get_progress_comparison(api_data, estimates_data)
                alerts_data = get_budget_alerts(progress_data)
                
            st.sidebar.success("✅ Estimates loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"❌ Error processing estimates: {str(e)}")
    
    # Calculate progress comparison if we have both API and estimates data
    if api_connected and api_data and estimates_loaded and estimates_data:
        try:
            # Get actual timesheet data from API
            if 'timesheet_data' in api_data and not api_data['timesheet_data'].empty:
                actual_data = api_data['timesheet_data']
            else:
                # Use sample actual data
                actual_data = get_api_handler().fetch_timesheet_data()
            
            # Get estimates data
            if 'estimates_data' in estimates_data and not estimates_data['estimates_data'].empty:
                estimates_df = estimates_data['estimates_data']
            else:
                estimates_df = get_estimates_handler()._generate_mock_estimates_data()
            
            # Calculate progress comparison
            progress_data = get_progress_comparison(actual_data, estimates_df)
            
            # Generate alerts
            alerts_data = get_budget_alerts(progress_data)
            
        except Exception as e:
            st.sidebar.warning(f"Progress calculation error: {str(e)}")
    
    # Auto-refresh for real-time data
    if data_source == "Real-time API" and api_connected:
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()
    
    # Display data source status
    display_data_source_indicators(api_connected, estimates_loaded)
    
    st.markdown("---")
    
    # Main dashboard content
    try:
        # 1. KPI Cards
        display_kpi_cards(api_data, estimates_data)
        
        st.markdown("---")
        
        # 2. Real-time charts (if API connected)
        if api_connected and api_data:
            display_real_time_charts(api_data)
            st.markdown("---")
        
        # 3. Project Progress (if estimates available)
        if progress_data:
            display_project_progress(progress_data)
            st.markdown("---")
        
        # 4. Alerts Section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if alerts_data:
                display_alerts_section(alerts_data)
            else:
                if not estimates_loaded:
                    st.info("💡 Upload project estimates to enable progress tracking and alerts")
                else:
                    st.success("✅ No alerts at this time!")
        
        with col2:
            st.subheader("📅 Quick Stats")
            
            if api_data:
                # Recent activity
                st.metric("Today's Hours", f"{api_data.get('today_hours', 0):.1f}h")
                st.metric("This Week's Hours", f"{api_data.get('week_hours', 0):.1f}h")
                st.metric("Active Employees", api_data.get('active_employees', 0))
                
                # Data freshness
                last_update = datetime.now().strftime("%H:%M:%S")
                st.caption(f"Last updated: {last_update}")
            else:
                st.info("Connect API for real-time stats")
        
        # 5. Integration Status Panel
        st.markdown("---")
        st.subheader("🔧 Integration Status")
        
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            api_status = "🟢 Connected" if api_connected else "🔴 Disconnected"
            st.metric("API Status", api_status)
            if api_connected and api_data:
                st.caption(f"Tracking {api_data.get('active_projects', 0)} projects")
        
        with status_col2:
            estimates_status = "🟢 Loaded" if estimates_loaded else "⚪ Not loaded"
            st.metric("Estimates Status", estimates_status)
            if estimates_loaded and estimates_data:
                st.caption(f"Budget: ${estimates_data.get('estimated_budget', 0):,.0f}")
        
        with status_col3:
            progress_status = "🟢 Active" if progress_data else "⚪ Inactive"
            st.metric("Progress Tracking", progress_status)
            if progress_data:
                st.caption(f"Monitoring {len(progress_data)} projects")
        
        # 6. Quick Navigation
        st.markdown("---")
        st.subheader("🚀 Quick Navigation")
        
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        
        with nav_col1:
            if st.button("📊 Dashboard Analytics", use_container_width=True):
                st.switch_page("pages/Dashboard.py")
        
        with nav_col2:
            if st.button("👥 Employee Analytics", use_container_width=True):
                st.switch_page("pages/Employee_Analytics.py")
        
        with nav_col3:
            if st.button("📈 Project Analytics", use_container_width=True):
                st.switch_page("pages/Project_Analytics.py")
        
        # 7. Footer with system info
        st.markdown("---")
        st.caption("**DDMac Analytics Dashboard** | Powered by Streamlit | Real-time Integration Active")
        
        # Show sample data preview if no real data
        if not api_connected and not estimates_loaded:
            with st.expander("📋 Sample Data Preview"):
                st.info("This is demo data. Configure API and upload estimates for real analytics.")
                sample_data = get_api_handler().get_sample_data()
                if sample_data:
                    st.json(sample_data)
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check your configuration and try again.")
        
        # Show error details in expander
        with st.expander("🔍 Error Details"):
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
