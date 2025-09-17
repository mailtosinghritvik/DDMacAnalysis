import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Import our custom utilities
from utils.time_analysis import (
    analyze_all_projects,
    analyze_projects_for_client,
    get_project_health_metrics,
    TimeTrackingAnalyzer
)

# Set page configuration
st.set_page_config(
    page_title="Project Analytics - DDMac",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .project-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
        margin: 0.5rem 0;
    }
    .risk-high { border-left-color: #dc3545 !important; }
    .risk-medium { border-left-color: #ffc107 !important; }
    .risk-low { border-left-color: #28a745 !important; }
</style>
""", unsafe_allow_html=True)

def create_project_timeline_gantt(data, selected_projects=None):
    """Create a Gantt-like timeline for projects"""
    if selected_projects:
        data = data[data['project'].isin(selected_projects)]
    
    project_timeline = data.groupby('project').agg({
        'date': ['min', 'max'],
        'hours': 'sum'
    }).reset_index()
    
    project_timeline.columns = ['Project', 'Start', 'End', 'Total_Hours']
    
    # Create timeline chart
    fig = px.timeline(
        project_timeline,
        x_start='Start',
        x_end='End',
        y='Project',
        color='Total_Hours',
        title='Project Timeline & Duration',
        labels={'Total_Hours': 'Total Hours'}
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Timeline",
        yaxis_title="Projects"
    )
    
    return fig

def create_burndown_chart(data, project_name):
    """Create a burndown chart for a specific project"""
    project_data = data[data['project'] == project_name].copy()
    
    if project_data.empty:
        return None
    
    # Calculate cumulative hours
    daily_hours = project_data.groupby('date')['hours'].sum().reset_index()
    daily_hours = daily_hours.sort_values('date')
    daily_hours['cumulative_hours'] = daily_hours['hours'].cumsum()
    
    fig = go.Figure()
    
    # Actual progress
    fig.add_trace(go.Scatter(
        x=daily_hours['date'],
        y=daily_hours['cumulative_hours'],
        mode='lines+markers',
        name='Actual Hours',
        line=dict(color='#1f77b4', width=3)
    ))
    
    # Ideal burnup line (assuming steady progress)
    if len(daily_hours) > 1:
        total_hours = daily_hours['cumulative_hours'].iloc[-1]
        start_date = daily_hours['date'].iloc[0]
        end_date = daily_hours['date'].iloc[-1]
        
        ideal_line = pd.DataFrame({
            'date': [start_date, end_date],
            'ideal_hours': [0, total_hours]
        })
        
        fig.add_trace(go.Scatter(
            x=ideal_line['date'],
            y=ideal_line['ideal_hours'],
            mode='lines',
            name='Ideal Progress',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title=f'Project Progress: {project_name}',
        xaxis_title='Date',
        yaxis_title='Cumulative Hours',
        height=400
    )
    
    return fig

def create_resource_allocation_chart(data):
    """Create resource allocation across projects"""
    # Calculate hours per employee per project
    allocation = data.groupby(['project', 'employee'])['hours'].sum().reset_index()
    
    fig = px.sunburst(
        allocation,
        path=['project', 'employee'],
        values='hours',
        title='Resource Allocation: Projects → Employees'
    )
    
    fig.update_layout(height=500)
    return fig

def calculate_project_predictions(data, project_name):
    """Calculate project completion predictions"""
    project_data = data[data['project'] == project_name].copy()
    
    if len(project_data) < 7:  # Need at least a week of data
        return None
    
    # Calculate daily average hours
    daily_hours = project_data.groupby('date')['hours'].sum().reset_index()
    daily_hours = daily_hours.sort_values('date')
    
    # Get recent trend (last 7 days)
    recent_data = daily_hours.tail(7)
    avg_daily_hours = recent_data['hours'].mean()
    
    # Calculate velocity (hours per day trend)
    if len(recent_data) > 1:
        x = np.arange(len(recent_data))
        y = recent_data['hours'].values
        velocity = np.polyfit(x, y, 1)[0]  # Linear trend coefficient
    else:
        velocity = 0
    
    predictions = {
        'avg_daily_hours': round(avg_daily_hours, 2),
        'velocity_trend': 'Increasing' if velocity > 0.1 else 'Decreasing' if velocity < -0.1 else 'Stable',
        'velocity_value': round(velocity, 2),
        'total_hours': project_data['hours'].sum(),
        'active_days': project_data['date'].nunique(),
        'last_activity': project_data['date'].max()
    }
    
    return predictions

def main():
    """Main Project Analytics Dashboard"""
    
    st.title("🚀 Project Analytics Dashboard")
    st.markdown("**Comprehensive project health monitoring, resource allocation, and predictive analytics**")
    
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
        st.header("🔧 Project Filters")
        
        # Project selection
        all_projects = sorted(data['project'].unique())
        selected_projects = st.multiselect(
            "Select Projects",
            all_projects,
            default=all_projects[:5] if len(all_projects) > 5 else all_projects
        )
        
        # Client filter
        all_clients = sorted(data['client'].unique())
        selected_clients = st.multiselect(
            "Filter by Client",
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
        
        # Apply filters
        if len(date_range) == 2:
            filtered_data = data[
                (data['project'].isin(selected_projects)) &
                (data['client'].isin(selected_clients)) &
                (data['date'].dt.date >= date_range[0]) &
                (data['date'].dt.date <= date_range[1])
            ]
        else:
            filtered_data = data[
                (data['project'].isin(selected_projects)) &
                (data['client'].isin(selected_clients))
            ]
    
    if filtered_data.empty:
        st.error("No data matches the selected filters. Please adjust your selection.")
        return
    
    # Generate analytics for filtered data
    with st.spinner("Analyzing project data..."):
        project_health = get_project_health_metrics(filtered_data)
        all_projects_summary = analyze_all_projects(filtered_data)
    
    # Key Metrics Row
    st.subheader("📊 Project Portfolio Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_projects = filtered_data['project'].nunique()
        st.metric("Active Projects", active_projects)
    
    with col2:
        if not project_health.empty:
            healthy_count = len(project_health[project_health['Status'] == 'Healthy'])
            st.metric("Healthy Projects", healthy_count, delta=f"{healthy_count/len(project_health)*100:.0f}%")
        else:
            st.metric("Healthy Projects", 0)
    
    with col3:
        total_hours = filtered_data['hours'].sum()
        st.metric("Total Hours", f"{total_hours:,.0f}")
    
    with col4:
        if not project_health.empty:
            avg_health = project_health['Health_Score'].mean()
            st.metric("Avg Health Score", f"{avg_health:.0f}/100")
        else:
            st.metric("Avg Health Score", "N/A")
    
    # Main Analytics Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Project Health", 
        "⏱️ Timeline & Progress", 
        "👥 Resource Allocation", 
        "🔮 Predictive Analytics"
    ])
    
    with tab1:
        st.subheader("Project Health Dashboard")
        
        if not project_health.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Health score vs hours scatter
                fig_health = px.scatter(
                    project_health,
                    x='Total_Hours',
                    y='Health_Score',
                    size='Team_Size',
                    color='Status',
                    hover_data=['Project', 'Avg_Weekly_Hours'],
                    title='Project Health vs Investment (Hours)',
                    color_discrete_map={
                        'Healthy': '#28a745',
                        'At Risk': '#ffc107',
                        'Critical': '#dc3545'
                    }
                )
                fig_health.update_layout(height=400)
                st.plotly_chart(fig_health, use_container_width=True)
            
            with col2:
                # Status distribution
                status_counts = project_health['Status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title='Project Status Distribution',
                    color_discrete_map={
                        'Healthy': '#28a745',
                        'At Risk': '#ffc107',
                        'Critical': '#dc3545'
                    }
                )
                fig_status.update_layout(height=400)
                st.plotly_chart(fig_status, use_container_width=True)
            
            # Project Health Table
            st.subheader("Detailed Project Health Metrics")
            
            # Style the health table
            def style_health_score(val):
                if val >= 70:
                    return 'background-color: #d4edda'
                elif val >= 40:
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #f8d7da'
            
            styled_health = project_health.style.applymap(
                style_health_score, 
                subset=['Health_Score']
            )
            st.dataframe(styled_health, use_container_width=True)
            
            # Critical projects alert
            critical_projects = project_health[project_health['Status'] == 'Critical']
            if len(critical_projects) > 0:
                st.error("🚨 Critical Projects Requiring Immediate Attention:")
                for _, proj in critical_projects.iterrows():
                    st.markdown(f"• **{proj['Project']}**: Health Score {proj['Health_Score']:.0f}/100")
        else:
            st.info("No project health data available for the selected filters.")
    
    with tab2:
        st.subheader("Project Timeline & Progress Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Project timeline
            if not filtered_data.empty:
                timeline_fig = create_project_timeline_gantt(filtered_data, selected_projects)
                st.plotly_chart(timeline_fig, use_container_width=True)
        
        with col2:
            # Individual project burndown
            st.markdown("#### Project Progress Analysis")
            selected_project = st.selectbox(
                "Select Project for Detailed Analysis",
                selected_projects
            )
            
            if selected_project:
                burndown_fig = create_burndown_chart(filtered_data, selected_project)
                if burndown_fig:
                    st.plotly_chart(burndown_fig, use_container_width=True)
                else:
                    st.info("Insufficient data for progress analysis")
        
        # Project duration analysis
        st.subheader("Project Duration Analysis")
        project_durations = filtered_data.groupby('project').agg({
            'date': ['min', 'max'],
            'hours': 'sum'
        }).reset_index()
        
        project_durations.columns = ['Project', 'Start_Date', 'End_Date', 'Total_Hours']
        project_durations['Duration_Days'] = (
            project_durations['End_Date'] - project_durations['Start_Date']
        ).dt.days + 1
        project_durations['Hours_per_Day'] = (
            project_durations['Total_Hours'] / project_durations['Duration_Days']
        ).round(2)
        
        fig_duration = px.bar(
            project_durations,
            x='Project',
            y='Duration_Days',
            color='Hours_per_Day',
            title='Project Duration vs Daily Intensity',
            labels={'Hours_per_Day': 'Avg Hours/Day'}
        )
        fig_duration.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig_duration, use_container_width=True)
    
    with tab3:
        st.subheader("Resource Allocation Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Resource allocation sunburst
            allocation_fig = create_resource_allocation_chart(filtered_data)
            st.plotly_chart(allocation_fig, use_container_width=True)
        
        with col2:
            # Team size vs project hours
            team_analysis = filtered_data.groupby('project').agg({
                'employee': 'nunique',
                'hours': 'sum'
            }).reset_index()
            team_analysis.columns = ['Project', 'Team_Size', 'Total_Hours']
            team_analysis['Hours_per_Person'] = (
                team_analysis['Total_Hours'] / team_analysis['Team_Size']
            ).round(1)
            
            fig_team = px.scatter(
                team_analysis,
                x='Team_Size',
                y='Total_Hours',
                size='Hours_per_Person',
                hover_data=['Project'],
                title='Team Size vs Project Hours',
                labels={'Hours_per_Person': 'Hours per Person'}
            )
            fig_team.update_layout(height=500)
            st.plotly_chart(fig_team, use_container_width=True)
        
        # Resource utilization heatmap
        st.subheader("Employee-Project Allocation Heatmap")
        
        # Create employee-project matrix
        allocation_matrix = filtered_data.pivot_table(
            values='hours',
            index='employee',
            columns='project',
            aggfunc='sum',
            fill_value=0
        )
        
        if not allocation_matrix.empty:
            fig_heatmap = px.imshow(
                allocation_matrix.values,
                x=allocation_matrix.columns,
                y=allocation_matrix.index,
                title='Employee-Project Hours Allocation',
                labels={'color': 'Hours'},
                aspect='auto'
            )
            fig_heatmap.update_layout(height=400)
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab4:
        st.subheader("🔮 Predictive Analytics & Insights")
        
        # Project predictions
        st.markdown("#### Project Completion Predictions")
        
        prediction_project = st.selectbox(
            "Select Project for Prediction Analysis",
            selected_projects,
            key="prediction_select"
        )
        
        if prediction_project:
            predictions = calculate_project_predictions(filtered_data, prediction_project)
            
            if predictions:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Current Velocity",
                        f"{predictions['avg_daily_hours']:.1f} hrs/day",
                        delta=predictions['velocity_trend']
                    )
                
                with col2:
                    st.metric(
                        "Total Investment",
                        f"{predictions['total_hours']:.0f} hours",
                        delta=f"{predictions['active_days']} active days"
                    )
                
                with col3:
                    days_since_activity = (
                        datetime.now().date() - predictions['last_activity'].date()
                    ).days
                    st.metric(
                        "Last Activity",
                        f"{days_since_activity} days ago",
                        delta="Recent" if days_since_activity <= 3 else "Stale"
                    )
                
                # Velocity trend analysis
                project_daily = filtered_data[
                    filtered_data['project'] == prediction_project
                ].groupby('date')['hours'].sum().reset_index()
                
                if len(project_daily) > 1:
                    # Add trend line
                    fig_trend = px.line(
                        project_daily,
                        x='date',
                        y='hours',
                        title=f'Daily Hours Trend: {prediction_project}',
                        markers=True
                    )
                    
                    # Add trend line
                    x_numeric = np.arange(len(project_daily))
                    z = np.polyfit(x_numeric, project_daily['hours'], 1)
                    p = np.poly1d(z)
                    
                    fig_trend.add_trace(
                        go.Scatter(
                            x=project_daily['date'],
                            y=p(x_numeric),
                            mode='lines',
                            name='Trend Line',
                            line=dict(dash='dash', color='red')
                        )
                    )
                    
                    fig_trend.update_layout(height=400)
                    st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Insufficient data for prediction analysis (need at least 7 days of data)")
        
        # Risk analysis
        st.markdown("#### Risk Analysis")
        
        if not project_health.empty:
            # Identify at-risk projects
            at_risk = project_health[project_health['Status'].isin(['At Risk', 'Critical'])]
            
            if len(at_risk) > 0:
                st.warning(f"⚠️ {len(at_risk)} project(s) require attention:")
                
                for _, proj in at_risk.iterrows():
                    risk_level = proj['Status'].lower().replace(' ', '-')
                    
                    st.markdown(f"""
                    <div class="metric-container risk-{risk_level.split('-')[0] if '-' in risk_level else risk_level}">
                        <strong>{proj['Project']}</strong><br>
                        Status: {proj['Status']} | Health Score: {proj['Health_Score']:.0f}/100<br>
                        Team Size: {proj['Team_Size']} | Weekly Hours: {proj['Avg_Weekly_Hours']:.1f}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ All projects are currently healthy!")
        
        # Recommendations
        st.markdown("#### AI-Powered Recommendations")
        
        recommendations = []
        
        if not project_health.empty:
            # Low health score projects
            low_health = project_health[project_health['Health_Score'] < 50]
            if len(low_health) > 0:
                recommendations.append("🔴 **Critical**: Review project scope and resource allocation for low-health projects")
            
            # High team size but low hours
            high_team_low_hours = project_health[
                (project_health['Team_Size'] > 3) & 
                (project_health['Avg_Weekly_Hours'] < 20)
            ]
            if len(high_team_low_hours) > 0:
                recommendations.append("⚡ **Efficiency**: Large teams with low weekly hours may indicate underutilization")
            
            # Unbalanced workload
            high_variance = project_health[project_health['Workload_Balance'] > 1.0]
            if len(high_variance) > 0:
                recommendations.append("⚖️ **Balance**: Consider redistributing workload for projects with high variance")
        
        if recommendations:
            for rec in recommendations:
                st.markdown(rec)
        else:
            st.info("💡 All projects appear to be well-managed based on current metrics!")

if __name__ == "__main__":
    main()
