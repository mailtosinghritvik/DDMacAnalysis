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
    analyze_clients,
    analyze_projects_for_client,
    TimeTrackingAnalyzer,
    
    # API functions
    get_api_handler,
    fetch_real_time_data,
    analyze_clients_api,
    analyze_projects_for_client_api,
    
    # Estimates functions
    get_estimates_handler,
    get_progress_comparison,
    get_budget_alerts
)

# Set page configuration
st.set_page_config(
    page_title="Dashboard Analytics - DDMac",
    page_icon="�",
    layout="wide"
)

# Custom CSS for dual data source dashboard
st.markdown("""
<style>
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .data-source-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .api-live {
        border-left-color: #28a745;
        background: #d4edda;
    }
    
    .estimates-loaded {
        border-left-color: #007bff;
        background: #d1ecf1;
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
    
    .alert-card {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .metric-comparison {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_dashboard_data():
    """Fetch data from both API and estimates sources"""
    api_data = None
    estimates_data = None
    progress_data = None
    alerts_data = None
    
    # Check session state for configuration
    api_connected = st.session_state.get('api_connected', False)
    estimates_loaded = st.session_state.get('estimates_loaded', False)
    
    try:
        # Get API data
        if api_connected or 'api_handler_config' in st.session_state:
            api_handler = get_api_handler()
            api_data = api_handler.get_sample_data()  # Using sample for demo
        else:
            # Fallback to sample data
            api_data = get_api_handler().get_sample_data()
        
        # Get estimates data
        if estimates_loaded or 'estimates_data' in st.session_state:
            estimates_handler = get_estimates_handler()
            estimates_data = estimates_handler.get_sample_data()
        
        # Generate progress comparison if both sources available
        if api_data and estimates_data:
            progress_data = get_progress_comparison(api_data, estimates_data)
            alerts_data = get_budget_alerts(progress_data)
    
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")
    
    return api_data, estimates_data, progress_data, alerts_data

def create_progress_gauge(actual, estimated, title="Progress"):
    """Create progress gauge for actual vs estimated"""
    if estimated > 0:
        progress_pct = min((actual / estimated) * 100, 100)
        
        # Color based on progress
        if progress_pct <= 75:
            color = "#28a745"
        elif progress_pct <= 90:
            color = "#ffc107"
        else:
            color = "#dc3545"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = progress_pct,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title},
            delta = {'reference': 100},
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
        
        fig.update_layout(height=300, showlegend=False)
        return fig
    return None

def create_budget_timeline_chart(progress_data):
    """Create budget vs actual spending timeline"""
    if not progress_data:
        return None
    
    timeline_data = []
    for project in progress_data:
        timeline_data.append({
            'Project': project['project_name'],
            'Estimated Budget': project.get('budget', 0),
            'Actual Spent': project.get('actual_cost', 0),
            'Budget Utilization %': (project.get('actual_cost', 0) / project.get('budget', 1)) * 100 if project.get('budget', 0) > 0 else 0
        })
    
    df = pd.DataFrame(timeline_data)
    
    fig = go.Figure()
    
    # Add estimated budget bars
    fig.add_trace(go.Bar(
        name='Estimated Budget',
        x=df['Project'],
        y=df['Estimated Budget'],
        marker_color='lightblue',
        opacity=0.7
    ))
    
    # Add actual spent bars
    fig.add_trace(go.Bar(
        name='Actual Spent',
        x=df['Project'],
        y=df['Actual Spent'],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='Budget vs Actual Spending by Project',
        xaxis_title='Projects',
        yaxis_title='Amount ($)',
        barmode='group',
        height=400
    )
    
    return fig

def create_client_progress_analysis(api_data, estimates_data):
    """Create client-level progress analysis"""
    if not api_data or not estimates_data:
        return None
    
    # Mock client progress data
    client_progress = [
        {
            'Client': 'TechCorp Inc',
            'Estimated Hours': 450,
            'Actual Hours': 380,
            'Progress %': 84.4,
            'Budget': 67500,
            'Spent': 57000,
            'Status': 'On Track'
        },
        {
            'Client': 'GlobalSoft',
            'Estimated Hours': 320,
            'Actual Hours': 340,
            'Progress %': 106.3,
            'Budget': 48000,
            'Spent': 51000,
            'Status': 'Over Budget'
        },
        {
            'Client': 'StartupX',
            'Estimated Hours': 180,
            'Actual Hours': 120,
            'Progress %': 66.7,
            'Budget': 27000,
            'Spent': 18000,
            'Status': 'Under Utilized'
        }
    ]
    
    df = pd.DataFrame(client_progress)
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='Estimated Hours',
        y='Actual Hours',
        size='Budget',
        color='Status',
        hover_data=['Client', 'Progress %'],
        title='Client Progress: Estimated vs Actual Hours',
        color_discrete_map={
            'On Track': '#28a745',
            'Over Budget': '#dc3545',
            'Under Utilized': '#ffc107'
        }
    )
    
    # Add diagonal line for perfect progress
    max_hours = max(df['Estimated Hours'].max(), df['Actual Hours'].max())
    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=max_hours, y1=max_hours,
        line=dict(color="gray", width=2, dash="dash"),
    )
    
    fig.update_layout(height=400)
    return fig, df

def display_data_source_status(api_data, estimates_data):
    """Display status of data sources"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if api_data:
            st.markdown("""
            <div class="data-source-card api-live">
                <h4>🟢 API Connected</h4>
                <p>Real-time data active</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="data-source-card">
                <h4>🔴 API Offline</h4>
                <p>Using sample data</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if estimates_data:
            st.markdown("""
            <div class="data-source-card estimates-loaded">
                <h4>📊 Estimates Loaded</h4>
                <p>Progress tracking active</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="data-source-card">
                <h4>📊 No Estimates</h4>
                <p>Upload estimates file</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if api_data and estimates_data:
            st.markdown("""
            <div class="data-source-card api-live">
                <h4>⚡ Full Integration</h4>
                <p>All features active</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="data-source-card">
                <h4>⚠️ Partial Data</h4>
                <p>Limited features</p>
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main Dashboard with dual data source integration"""
    
    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1>📊 DDMac Analytics Dashboard</h1>
        <p>Integrated Real-time Tracking & Project Estimates</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch data from both sources
    with st.spinner("Loading dashboard data..."):
        api_data, estimates_data, progress_data, alerts_data = get_dashboard_data()
    
    # Display data source status
    display_data_source_status(api_data, estimates_data)
    
    # Key Metrics Row
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if api_data:
            total_hours = api_data.get('total_hours', 0)
            st.metric("Total Hours", f"{total_hours:.1f}h")
        else:
            st.metric("Total Hours", "N/A")
    
    with col2:
        if api_data:
            active_projects = api_data.get('active_projects', 0)
            st.metric("Active Projects", active_projects)
        else:
            st.metric("Active Projects", "N/A")
    
    with col3:
        if estimates_data:
            total_budget = estimates_data.get('estimated_budget', 0)
            st.metric("Total Budget", f"${total_budget:,.0f}")
        else:
            st.metric("Total Budget", "N/A")
    
    with col4:
        if progress_data:
            avg_progress = np.mean([p['actual_hours']/p['estimated_hours']*100 for p in progress_data if p['estimated_hours'] > 0])
            st.metric("Avg Progress", f"{avg_progress:.1f}%")
        else:
            st.metric("Avg Progress", "N/A")
    
    with col5:
        if alerts_data:
            alert_count = len(alerts_data)
            st.metric("Active Alerts", alert_count, delta="Needs attention" if alert_count > 0 else "All good")
        else:
            st.metric("Active Alerts", "0")
    
    # Main Dashboard Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Progress Overview", 
        "💰 Budget Analysis", 
        "👥 Client Analytics",
        "🚨 Alerts & Insights"
    ])
    
    with tab1:
        st.subheader("Project Progress Overview")
        
        if progress_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Overall progress gauge
                total_actual = sum([p['actual_hours'] for p in progress_data])
                total_estimated = sum([p['estimated_hours'] for p in progress_data])
                progress_fig = create_progress_gauge(total_actual, total_estimated, "Overall Progress")
                if progress_fig:
                    st.plotly_chart(progress_fig, use_container_width=True)
            
            with col2:
                # Budget utilization gauge
                total_budget = sum([p.get('budget', 0) for p in progress_data])
                total_spent = sum([p.get('actual_cost', 0) for p in progress_data])
                budget_fig = create_progress_gauge(total_spent, total_budget, "Budget Utilization")
                if budget_fig:
                    st.plotly_chart(budget_fig, use_container_width=True)
            
            # Progress details table
            st.subheader("Project Progress Details")
            progress_df = pd.DataFrame([
                {
                    'Project': p['project_name'],
                    'Estimated Hours': p['estimated_hours'],
                    'Actual Hours': p['actual_hours'],
                    'Progress %': f"{(p['actual_hours']/p['estimated_hours']*100):.1f}%" if p['estimated_hours'] > 0 else "N/A",
                    'Status': p.get('status', 'Unknown')
                } for p in progress_data
            ])
            
            st.dataframe(progress_df, use_container_width=True)
        else:
            st.info("💡 Upload project estimates to enable progress tracking")
    
    with tab2:
        st.subheader("Budget Analysis & Financial Tracking")
        
        if progress_data:
            # Budget timeline chart
            budget_timeline_fig = create_budget_timeline_chart(progress_data)
            if budget_timeline_fig:
                st.plotly_chart(budget_timeline_fig, use_container_width=True)
            
            # Budget breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                # Budget utilization pie chart
                budget_data = []
                for p in progress_data:
                    if p.get('budget', 0) > 0:
                        remaining = max(0, p['budget'] - p.get('actual_cost', 0))
                        budget_data.append({
                            'Project': p['project_name'],
                            'Spent': p.get('actual_cost', 0),
                            'Remaining': remaining
                        })
                
                if budget_data:
                    budget_df = pd.DataFrame(budget_data)
                    fig = px.pie(
                        budget_df.melt(id_vars=['Project'], var_name='Category', value_name='Amount'),
                        values='Amount',
                        names='Category',
                        title='Budget Utilization Distribution'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Budget efficiency metrics
                st.subheader("Budget Efficiency")
                for p in progress_data:
                    if p.get('budget', 0) > 0:
                        efficiency = (p.get('actual_cost', 0) / p['budget']) * 100
                        status = "🟢" if efficiency <= 90 else "🟡" if efficiency <= 100 else "🔴"
                        st.write(f"{status} **{p['project_name']}**: {efficiency:.1f}% utilized")
        else:
            st.info("💡 Upload budget estimates to enable financial tracking")
    
    with tab3:
        st.subheader("Client Analytics & Progress")
        
        if api_data and estimates_data:
            # Client progress analysis
            client_fig, client_df = create_client_progress_analysis(api_data, estimates_data)
            if client_fig:
                st.plotly_chart(client_fig, use_container_width=True)
            
            # Client summary table
            st.subheader("Client Progress Summary")
            st.dataframe(client_df, use_container_width=True)
        
        elif api_data:
            # Fallback to API-only client analysis
            st.subheader("Client Activity (Real-time)")
            if 'client_summary' in api_data:
                client_activity_df = pd.DataFrame(api_data['client_summary'])
                st.dataframe(client_activity_df, use_container_width=True)
            else:
                st.info("No client data available from API")
        else:
            st.info("💡 Connect API or upload data to view client analytics")
    
    with tab4:
        st.subheader("Alerts & Business Insights")
        
        if alerts_data:
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
        else:
            st.success("✅ No active alerts - all projects are on track!")
        
        # Business insights
        st.subheader("📊 Business Insights")
        
        if api_data and estimates_data:
            insights = []
            
            # Calculate some basic insights
            if progress_data:
                over_budget_projects = [p for p in progress_data if p.get('actual_cost', 0) > p.get('budget', 0)]
                if over_budget_projects:
                    insights.append(f"📈 {len(over_budget_projects)} project(s) are over budget")
                
                under_utilized = [p for p in progress_data if p['actual_hours'] < p['estimated_hours'] * 0.8]
                if under_utilized:
                    insights.append(f"📉 {len(under_utilized)} project(s) may be under-utilized")
                
                on_track = [p for p in progress_data if 0.8 <= (p['actual_hours']/p['estimated_hours']) <= 1.1]
                insights.append(f"✅ {len(on_track)} project(s) are on track")
            
            for insight in insights:
                st.write(insight)
        else:
            st.info("💡 Connect both data sources for comprehensive business insights")

if __name__ == "__main__":
    main()

def create_client_profitability_chart(client_data, hourly_rate=150):
    """Create client profitability analysis chart"""
    # Calculate revenue and profitability metrics
    client_analysis = client_data.copy()
    client_analysis['Revenue'] = client_analysis['Total_Hours'] * hourly_rate
    client_analysis['Weekly_Revenue'] = client_analysis['Weekly_Average_Hours'] * hourly_rate
    
    # Create profitability categories
    def categorize_profitability(hours):
        if hours >= 100:
            return 'High Value'
        elif hours >= 50:
            return 'Medium Value'
        else:
            return 'Low Value'
    
    client_analysis['Value_Category'] = client_analysis['Total_Hours'].apply(categorize_profitability)
    
    # Create bubble chart
    fig = px.scatter(
        client_analysis,
        x='Total_Hours',
        y='Weekly_Average_Hours',
        size='Revenue',
        color='Value_Category',
        hover_data=['Client', 'Revenue'],
        title='Client Profitability Analysis',
        labels={
            'Total_Hours': 'Total Hours Invested',
            'Weekly_Average_Hours': 'Weekly Average Hours'
        },
        color_discrete_map={
            'High Value': '#28a745',
            'Medium Value': '#ffc107',
            'Low Value': '#dc3545'
        }
    )
    
    fig.update_layout(height=500)
    return fig, client_analysis

def create_client_timeline_chart(data):
    """Create client engagement timeline"""
    client_timeline = data.groupby(['client', 'date'])['hours'].sum().reset_index()
    
    fig = px.line(
        client_timeline,
        x='date',
        y='hours',
        color='client',
        title='Client Engagement Timeline',
        labels={'hours': 'Daily Hours', 'date': 'Date'}
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Hours per Day"
    )
    
    return fig

def create_client_resource_allocation(data):
    """Create client resource allocation visualization"""
    # Calculate employee hours per client
    allocation = data.groupby(['client', 'employee'])['hours'].sum().reset_index()
    
    fig = px.sunburst(
        allocation,
        path=['client', 'employee'],
        values='hours',
        title='Resource Allocation: Clients → Employees'
    )
    
    fig.update_layout(height=500)
    return fig

def main():
    """Main Client Analytics Dashboard"""
    
    st.title("💼 Client Analytics Dashboard")
    st.markdown("**Comprehensive client profitability, engagement analysis, and relationship insights**")
    
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
        st.header("🔧 Client Filters")
        
        # Client selection
        all_clients = sorted(data['client'].unique())
        selected_clients = st.multiselect(
            "Select Clients",
            all_clients,
            default=all_clients
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
        
        # Revenue settings
        st.subheader("💰 Revenue Settings")
        hourly_rate = st.number_input(
            "Hourly Rate ($)",
            min_value=50,
            max_value=500,
            value=150,
            step=25
        )
        
        # Apply filters
        if len(date_range) == 2:
            filtered_data = data[
                (data['client'].isin(selected_clients)) &
                (data['date'].dt.date >= date_range[0]) &
                (data['date'].dt.date <= date_range[1])
            ]
        else:
            filtered_data = data[data['client'].isin(selected_clients)]
    
    if filtered_data.empty:
        st.error("No data matches the selected filters. Please adjust your selection.")
        return
    
    # Generate analytics
    with st.spinner("Analyzing client data..."):
        client_summary = analyze_clients(filtered_data)
    
    # Key Metrics Row
    st.subheader("📊 Client Portfolio Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_clients = len(client_summary)
        st.metric("Active Clients", total_clients)
    
    with col2:
        total_hours = client_summary['Total_Hours'].sum()
        total_revenue = total_hours * hourly_rate
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    
    with col3:
        avg_hours_per_client = client_summary['Total_Hours'].mean()
        st.metric("Avg Hours/Client", f"{avg_hours_per_client:.0f}")
    
    with col4:
        if not client_summary.empty:
            top_client_hours = client_summary['Total_Hours'].max()
            top_client_name = client_summary.loc[client_summary['Total_Hours'].idxmax(), 'Client']
            st.metric("Top Client", f"{top_client_hours:.0f} hrs", delta=top_client_name)
    
    # Main Analytics Tabs
    tab1, tab2 = st.tabs([
        "💰 Profitability Analysis", 
        "📊 Client Portfolio"
    ])
    
    with tab1:
        st.subheader("Client Profitability Analysis")
        
        # Profitability chart
        profitability_fig, client_analysis = create_client_profitability_chart(client_summary, hourly_rate)
        st.plotly_chart(profitability_fig, use_container_width=True)
        
        # Revenue breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue pie chart
            fig_revenue = px.pie(
                client_analysis,
                values='Revenue',
                names='Client',
                title='Revenue Distribution by Client'
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        with col2:
            # Hours vs Revenue scatter
            fig_hours_revenue = px.scatter(
                client_analysis,
                x='Total_Hours',
                y='Revenue',
                size='Weekly_Average_Hours',
                hover_data=['Client'],
                title='Hours vs Revenue Analysis',
                labels={'Total_Hours': 'Total Hours', 'Revenue': 'Revenue ($)'}
            )
            st.plotly_chart(fig_hours_revenue, use_container_width=True)
        
        # Profitability table
        st.subheader("Client Profitability Metrics")
        
        # Style the profitability table
        def style_value_category(val):
            if val == 'High Value':
                return 'background-color: #d4edda'
            elif val == 'Medium Value':
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #f8d7da'
        
        display_columns = ['Client', 'Total_Hours', 'Revenue', 'Weekly_Average_Hours', 'Value_Category']
        styled_table = client_analysis[display_columns].style.applymap(
            style_value_category, subset=['Value_Category']
        )
        
        st.dataframe(styled_table, use_container_width=True)
    
    with tab2:
        st.subheader("Client Portfolio Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Client engagement timeline
            timeline_fig = create_client_timeline_chart(filtered_data)
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        with col2:
            # Resource allocation
            allocation_fig = create_client_resource_allocation(filtered_data)
            st.plotly_chart(allocation_fig, use_container_width=True)
        
        # Client summary table
        st.subheader("Client Summary")
        st.dataframe(client_summary, use_container_width=True)

if __name__ == "__main__":
    main()
