import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Import our custom utilities
from utils.time_analysis import (
    analyze_clients,
    analyze_projects_for_client,
    TimeTrackingAnalyzer
)

# Set page configuration
st.set_page_config(
    page_title="Client Analytics - DDMac",
    page_icon="💼",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .client-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .revenue-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .profitability-high { 
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
    }
    .profitability-medium { 
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
    }
    .profitability-low { 
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); 
        color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

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
