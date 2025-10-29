import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("❌ Supabase not installed. Run: pip install supabase")

# Supabase configuration
SUPABASE_URL = "https://tgendmgdrljuxxxyynpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnZW5kbWdkcmxqdXh4eHl5bnB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1MjM5MTcsImV4cCI6MjA3MjA5OTkxN30.U6ntaBcINvgUH-UOOybhaUHvuIDfenSDzvgH5OQA3S4"

# Initialize Supabase client
if SUPABASE_AVAILABLE and SUPABASE_URL != "LMAO_WOW":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_CONFIGURED = True
    except Exception as e:
        SUPABASE_CONFIGURED = False
        st.error(f"❌ Supabase connection error: {str(e)}")
else:
    SUPABASE_CONFIGURED = False

# Set page configuration
st.set_page_config(
    page_title="AccuBid Data Viewer - DDMac Analytics",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for styling
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
    
    .data-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .data-table {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .sidebar-info {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_accubid_data():
    """
    Fetch all data from the accubid_breakdowns table
    """
    if not SUPABASE_CONFIGURED:
        return pd.DataFrame()
    
    try:
        response = supabase.table('accubid_breakdowns').select('*').execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Error fetching data: {str(e)}")
        return pd.DataFrame()

def format_currency(value):
    """Format numeric values as currency"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return value

def format_hours(value):
    """Format numeric values as hours"""
    try:
        return f"{float(value):,.1f} hrs"
    except (ValueError, TypeError):
        return value

def create_summary_metrics(df):
    """Create summary metrics from the data"""
    if df.empty:
        return {}
    
    metrics = {}
    
    # Basic counts
    metrics['total_records'] = len(df)
    metrics['unique_jobs'] = df['job_name'].nunique() if 'job_name' in df.columns else 0
    metrics['unique_clients'] = df['client_name'].nunique() if 'client_name' in df.columns else 0
    metrics['unique_tasks'] = df['Task_name'].nunique() if 'Task_name' in df.columns else 0
    
    # Financial metrics
    if 'cost_estimate' in df.columns:
        cost_estimates = pd.to_numeric(df['cost_estimate'], errors='coerce').dropna()
        metrics['total_cost'] = cost_estimates.sum()
        metrics['avg_cost'] = cost_estimates.mean()
        metrics['max_cost'] = cost_estimates.max()
    
    # Time metrics
    if 'time_estimate' in df.columns:
        time_estimates = pd.to_numeric(df['time_estimate'], errors='coerce').dropna()
        metrics['total_hours'] = time_estimates.sum()
        metrics['avg_hours'] = time_estimates.mean()
        metrics['max_hours'] = time_estimates.max()
    
    return metrics

def display_summary_metrics(metrics):
    """Display summary metrics in a nice layout"""
    st.markdown("### 📊 Data Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", metrics.get('total_records', 0))
        if 'total_cost' in metrics:
            st.metric("Total Cost", format_currency(metrics['total_cost']))
    
    with col2:
        st.metric("Unique Jobs", metrics.get('unique_jobs', 0))
        if 'avg_cost' in metrics:
            st.metric("Avg Cost", format_currency(metrics['avg_cost']))
    
    with col3:
        st.metric("Unique Clients", metrics.get('unique_clients', 0))
        if 'total_hours' in metrics:
            st.metric("Total Hours", format_hours(metrics['total_hours']))
    
    with col4:
        st.metric("Unique Tasks", metrics.get('unique_tasks', 0))
        if 'avg_hours' in metrics:
            st.metric("Avg Hours", format_hours(metrics['avg_hours']))

def create_visualizations(df):
    """Create various visualizations from the data"""
    if df.empty:
        return
    
    st.markdown("### 📈 Data Visualizations")
    
    # Tab layout for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Cost Analysis", "⏰ Time Analysis", "🏢 Client Overview", "🔧 Task Distribution"])
    
    with tab1:
        if 'cost_estimate' in df.columns and 'job_name' in df.columns:
            # Cost by job
            cost_by_job = df.groupby('job_name')['cost_estimate'].apply(
                lambda x: pd.to_numeric(x, errors='coerce').sum()
            ).sort_values(ascending=False)
            
            if not cost_by_job.empty:
                fig = px.bar(
                    x=cost_by_job.index,
                    y=cost_by_job.values,
                    title="Total Cost Estimate by Job",
                    labels={'x': 'Job Name', 'y': 'Cost Estimate ($)'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Cost distribution by task type
            if 'Task_name' in df.columns:
                task_costs = df.groupby('Task_name')['cost_estimate'].apply(
                    lambda x: pd.to_numeric(x, errors='coerce').sum()
                ).sort_values(ascending=False).head(10)
                
                if not task_costs.empty:
                    fig = px.pie(
                        values=task_costs.values,
                        names=task_costs.index,
                        title="Top 10 Tasks by Cost"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if 'time_estimate' in df.columns and 'job_name' in df.columns:
            # Time by job
            time_by_job = df.groupby('job_name')['time_estimate'].apply(
                lambda x: pd.to_numeric(x, errors='coerce').sum()
            ).sort_values(ascending=False)
            
            if not time_by_job.empty:
                fig = px.bar(
                    x=time_by_job.index,
                    y=time_by_job.values,
                    title="Total Time Estimate by Job",
                    labels={'x': 'Job Name', 'y': 'Time Estimate (hours)'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Time vs Cost scatter plot
            if 'cost_estimate' in df.columns:
                # Filter numeric data
                numeric_data = df.copy()
                numeric_data['time_estimate_num'] = pd.to_numeric(numeric_data['time_estimate'], errors='coerce')
                numeric_data['cost_estimate_num'] = pd.to_numeric(numeric_data['cost_estimate'], errors='coerce')
                numeric_data = numeric_data.dropna(subset=['time_estimate_num', 'cost_estimate_num'])
                
                if not numeric_data.empty:
                    fig = px.scatter(
                        numeric_data,
                        x='time_estimate_num',
                        y='cost_estimate_num',
                        hover_data=['job_name', 'Task_name'],
                        title="Time vs Cost Estimates",
                        labels={'time_estimate_num': 'Time Estimate (hours)', 'cost_estimate_num': 'Cost Estimate ($)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        if 'client_name' in df.columns:
            # Projects by client
            projects_by_client = df.groupby('client_name')['job_name'].nunique().sort_values(ascending=False)
            
            if not projects_by_client.empty:
                fig = px.bar(
                    x=projects_by_client.index,
                    y=projects_by_client.values,
                    title="Number of Projects by Client",
                    labels={'x': 'Client Name', 'y': 'Number of Projects'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Client cost analysis
            if 'cost_estimate' in df.columns:
                client_costs = df.groupby('client_name')['cost_estimate'].apply(
                    lambda x: pd.to_numeric(x, errors='coerce').sum()
                ).sort_values(ascending=False)
                
                if not client_costs.empty:
                    fig = px.pie(
                        values=client_costs.values,
                        names=client_costs.index,
                        title="Total Cost by Client"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        if 'Task_name' in df.columns:
            # Task frequency
            task_counts = df['Task_name'].value_counts().head(15)
            
            if not task_counts.empty:
                fig = px.bar(
                    x=task_counts.values,
                    y=task_counts.index,
                    orientation='h',
                    title="Top 15 Most Common Tasks",
                    labels={'x': 'Frequency', 'y': 'Task Name'}
                )
                st.plotly_chart(fig, use_container_width=True)

def apply_filters(df):
    """Apply filters to the dataframe based on user selection"""
    if df.empty:
        return df
    
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown("### 🔍 Filter Data")
    
    filtered_df = df.copy()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'client_name' in df.columns:
            clients = ['All'] + sorted(df['client_name'].unique().tolist())
            selected_client = st.selectbox("Select Client", clients)
            if selected_client != 'All':
                filtered_df = filtered_df[filtered_df['client_name'] == selected_client]
    
    with col2:
        if 'job_name' in df.columns:
            jobs = ['All'] + sorted(filtered_df['job_name'].unique().tolist())
            selected_job = st.selectbox("Select Job", jobs)
            if selected_job != 'All':
                filtered_df = filtered_df[filtered_df['job_name'] == selected_job]
    
    with col3:
        if 'Task_name' in df.columns:
            tasks = ['All'] + sorted(filtered_df['Task_name'].unique().tolist())
            selected_task = st.selectbox("Select Task", tasks)
            if selected_task != 'All':
                filtered_df = filtered_df[filtered_df['Task_name'] == selected_task]
    
    # Cost range filter
    if 'cost_estimate' in df.columns:
        cost_values = pd.to_numeric(df['cost_estimate'], errors='coerce').dropna()
        if not cost_values.empty:
            min_cost, max_cost = st.slider(
                "Cost Range ($)",
                min_value=float(cost_values.min()),
                max_value=float(cost_values.max()),
                value=(float(cost_values.min()), float(cost_values.max())),
                format="$%.0f"
            )
            
            # Apply cost filter
            numeric_costs = pd.to_numeric(filtered_df['cost_estimate'], errors='coerce')
            cost_mask = (numeric_costs >= min_cost) & (numeric_costs <= max_cost)
            filtered_df = filtered_df[cost_mask | numeric_costs.isna()]
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if len(filtered_df) != len(df):
        st.info(f"🔍 Showing {len(filtered_df)} of {len(df)} records after filtering")
    
    return filtered_df

def display_data_table(df):
    """Display the data in a formatted table"""
    if df.empty:
        st.warning("📭 No data available to display")
        return
    
    st.markdown('<div class="data-table">', unsafe_allow_html=True)
    st.markdown("### 📋 AccuBid Data Table")
    
    # Format the dataframe for better display
    display_df = df.copy()
    
    # Format cost and time columns
    if 'cost_estimate' in display_df.columns:
        display_df['Cost ($)'] = display_df['cost_estimate'].apply(
            lambda x: format_currency(x) if pd.notna(x) else 'N/A'
        )
    
    if 'time_estimate' in display_df.columns:
        display_df['Time (hrs)'] = display_df['time_estimate'].apply(
            lambda x: format_hours(x) if pd.notna(x) else 'N/A'
        )
    
    # Select columns to display
    columns_to_show = []
    for col in ['job_name', 'client_name', 'Task_name', 'Cost ($)', 'Time (hrs)']:
        if col in display_df.columns or col.split(' ')[0] in display_df.columns:
            columns_to_show.append(col)
    
    # Add any additional columns that exist
    for col in display_df.columns:
        if col not in columns_to_show and col not in ['cost_estimate', 'time_estimate']:
            columns_to_show.append(col)
    
    # Display the table
    if columns_to_show:
        final_df = display_df[columns_to_show]
        
        # Style the dataframe
        styled_df = final_df.style.set_properties(**{
            'background-color': '#f8f9fa',
            'color': '#333333',
            'border': '1px solid #dee2e6',
            'padding': '8px',
            'text-align': 'left'
        }).set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#667eea'),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('padding', '12px'),
                ('text-align', 'center')
            ]},
            {'selector': 'tr:nth-of-type(even)', 'props': [
                ('background-color', '#f8f9fa')
            ]},
            {'selector': 'tr:hover', 'props': [
                ('background-color', '#e9ecef')
            ]}
        ])
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Download option
        csv = final_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"accubid_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main AccuBid Data Viewer Page"""
    
    # Header
    st.markdown('<div class="main-header">📊 AccuBid Data Viewer</div>', unsafe_allow_html=True)
    st.markdown("**View and analyze all AccuBid estimates data from the database**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Data Overview")
        
        # Refresh button
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.markdown("**📈 Available Features:**")
        st.markdown("• View all AccuBid records")
        st.markdown("• Filter by client, job, or task")
        st.markdown("• Interactive visualizations")
        st.markdown("• Export data as CSV")
        st.markdown("• Real-time summary metrics")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Connection status
        st.markdown("---")
        st.subheader("🔗 Database Status")
        if SUPABASE_CONFIGURED:
            st.success("✅ Connected to Supabase")
        else:
            st.error("❌ Database connection failed")
    
    # Main content
    if not SUPABASE_CONFIGURED:
        st.error("❌ Database not configured. Please check your Supabase connection.")
        return
    
    # Fetch data
    with st.spinner("📡 Fetching data from database..."):
        df = fetch_accubid_data()
    
    if df.empty:
        st.warning("📭 No data found in the database.")
        st.info("💡 Upload some AccuBid files using the Excel Ingestion page to see data here.")
        return
    
    # Calculate metrics
    metrics = create_summary_metrics(df)
    
    # Display summary metrics
    display_summary_metrics(metrics)
    
    # Apply filters
    filtered_df = apply_filters(df)
    
    # Create visualizations
    create_visualizations(filtered_df)
    
    # Display data table
    display_data_table(filtered_df)
    
    # Additional information
    st.markdown("---")
    st.markdown("### ℹ️ About This Data")
    st.info("""
    This data comes from AccuBid electrical estimating software exports. Each record represents either:
    
    • **Overall Project** (Task: "EVERYTHING") - Total project estimates
    • **System Breakdown** - Individual electrical system estimates
    
    Use the filters above to explore specific clients, jobs, or tasks.
    """)

if __name__ == "__main__":
    main()