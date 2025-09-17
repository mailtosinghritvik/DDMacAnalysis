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
    analyze_all_projects,
    analyze_projects_for_client,
    get_project_health_metrics,
    TimeTrackingAnalyzer,
    
    # API functions
    get_api_handler,
    analyze_projects_for_client_api,
    analyze_project_details_api,
    
    # Estimates functions
    get_estimates_handler,
    get_progress_comparison,
    get_budget_alerts
)

# Set page configuration
st.set_page_config(
    page_title="Project Analytics - DDMac",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS for project analytics with dual data sources
st.markdown("""
<style>
    .project-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .project-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
        margin: 0.5rem 0;
    }
    
    .risk-high { 
        border-left-color: #dc3545;
        background: #f8d7da;
    }
    
    .risk-medium { 
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    
    .risk-low { 
        border-left-color: #28a745;
        background: #d4edda;
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
    
    .timeline-card {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 10px;
        color: #333;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_project_data():
    """Fetch project data from both API and estimates sources"""
    api_data = None
    estimates_data = None
    progress_data = None
    alerts_data = None
    
    try:
        # Get API data for project analytics
        api_handler = get_api_handler()
        api_data = api_handler.get_sample_data()
        
        # Get estimates data
        estimates_handler = get_estimates_handler()
        estimates_data = estimates_handler.get_sample_data()
        
        # Generate progress comparison
        if api_data and estimates_data:
            progress_data = get_progress_comparison(api_data, estimates_data)
            alerts_data = get_budget_alerts(progress_data)
    
    except Exception as e:
        st.error(f"Error fetching project data: {str(e)}")
    
    return api_data, estimates_data, progress_data, alerts_data

def create_project_progress_timeline(progress_data):
    """Create project progress timeline chart"""
    if not progress_data:
        return None
    
    timeline_data = []
    for p in progress_data:
        # Calculate progress percentage
        progress_pct = (p['actual_hours'] / p['estimated_hours'] * 100) if p['estimated_hours'] > 0 else 0
        
        timeline_data.append({
            'Project': p['project_name'],
            'Progress %': min(progress_pct, 100),
            'Status': p.get('status', 'Unknown'),
            'Estimated Hours': p['estimated_hours'],
            'Actual Hours': p['actual_hours']
        })
    
    df = pd.DataFrame(timeline_data)
    
    # Create horizontal bar chart
    fig = px.bar(
        df,
        x='Progress %',
        y='Project',
        color='Status',
        orientation='h',
        title='Project Progress Overview',
        color_discrete_map={
            'On Track': '#28a745',
            'At Risk': '#ffc107',
            'Delayed': '#dc3545',
            'Completed': '#17a2b8'
        }
    )
    
    # Add 100% reference line
    fig.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="Target")
    
    fig.update_layout(height=400, xaxis_title="Progress Percentage")
    return fig

def create_project_budget_analysis(progress_data):
    """Create project budget analysis chart"""
    if not progress_data:
        return None
    
    budget_data = []
    for p in progress_data:
        if p.get('budget', 0) > 0:
            utilization = (p.get('actual_cost', 0) / p['budget']) * 100
            budget_data.append({
                'Project': p['project_name'],
                'Budget': p['budget'],
                'Spent': p.get('actual_cost', 0),
                'Remaining': max(0, p['budget'] - p.get('actual_cost', 0)),
                'Utilization %': utilization,
                'Status': 'Over Budget' if utilization > 100 else 'On Track' if utilization <= 90 else 'Caution'
            })
    
    if not budget_data:
        return None
    
    df = pd.DataFrame(budget_data)
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Spent',
        x=df['Project'],
        y=df['Spent'],
        marker_color='#dc3545'
    ))
    
    fig.add_trace(go.Bar(
        name='Remaining',
        x=df['Project'],
        y=df['Remaining'],
        marker_color='#28a745'
    ))
    
    fig.update_layout(
        title='Project Budget Utilization',
        xaxis_title='Projects',
        yaxis_title='Budget ($)',
        barmode='stack',
        height=400
    )
    
    return fig, df

def create_project_risk_matrix(progress_data):
    """Create project risk assessment matrix"""
    if not progress_data:
        return None
    
    risk_data = []
    for p in progress_data:
        # Calculate risk factors
        budget_risk = (p.get('actual_cost', 0) / p.get('budget', 1)) if p.get('budget', 0) > 0 else 0
        schedule_risk = (p['actual_hours'] / p['estimated_hours']) if p['estimated_hours'] > 0 else 0
        
        # Risk scoring (0-10 scale)
        budget_score = min(10, budget_risk * 10)
        schedule_score = min(10, schedule_risk * 10)
        
        risk_data.append({
            'Project': p['project_name'],
            'Budget Risk': budget_score,
            'Schedule Risk': schedule_score,
            'Overall Risk': (budget_score + schedule_score) / 2,
            'Status': p.get('status', 'Unknown')
        })
    
    df = pd.DataFrame(risk_data)
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='Budget Risk',
        y='Schedule Risk',
        size='Overall Risk',
        color='Status',
        hover_data=['Project'],
        title='Project Risk Matrix',
        labels={
            'Budget Risk': 'Budget Risk (0-10)',
            'Schedule Risk': 'Schedule Risk (0-10)'
        }
    )
    
    # Add risk zones
    fig.add_shape(type="rect", x0=0, y0=0, x1=5, y1=5, 
                  fillcolor="green", opacity=0.2, line_width=0)
    fig.add_shape(type="rect", x0=5, y0=5, x1=10, y1=10, 
                  fillcolor="red", opacity=0.2, line_width=0)
    
    fig.update_layout(height=400)
    return fig, df

def create_project_team_allocation(api_data):
    """Create project team allocation chart"""
    if not api_data:
        return None
    
    # Mock team allocation data
    allocation_data = [
        {'Project': 'TechCorp Mobile App', 'Team Size': 4, 'Lead': 'Alice Johnson', 'Total Hours': 280},
        {'Project': 'GlobalSoft Dashboard', 'Team Size': 3, 'Lead': 'Carol Davis', 'Total Hours': 220},
        {'Project': 'StartupX Website', 'Team Size': 2, 'Lead': 'Bob Smith', 'Total Hours': 180},
        {'Project': 'Internal Tools', 'Team Size': 2, 'Lead': 'David Wilson', 'Total Hours': 160},
        {'Project': 'Testing Framework', 'Team Size': 1, 'Lead': 'Emma Brown', 'Total Hours': 120}
    ]
    
    df = pd.DataFrame(allocation_data)
    
    # Create bubble chart
    fig = px.scatter(
        df,
        x='Team Size',
        y='Total Hours',
        size='Total Hours',
        color='Project',
        hover_data=['Lead'],
        title='Project Team Allocation & Hours',
        labels={
            'Team Size': 'Team Size (People)',
            'Total Hours': 'Total Hours Invested'
        }
    )
    
    fig.update_layout(height=400)
    return fig, df

def display_project_kpis(api_data, estimates_data, progress_data):
    """Display project-level KPIs"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if api_data:
            active_projects = api_data.get('active_projects', 0)
            st.metric("Active Projects", active_projects)
        else:
            st.metric("Active Projects", "N/A")
    
    with col2:
        if progress_data:
            completed_projects = len([p for p in progress_data if p.get('status') == 'Completed'])
            st.metric("Completed Projects", completed_projects)
        else:
            st.metric("Completed Projects", "N/A")
    
    with col3:
        if progress_data:
            total_budget = sum([p.get('budget', 0) for p in progress_data])
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
        if progress_data:
            at_risk_projects = len([p for p in progress_data if p.get('actual_cost', 0) > p.get('budget', 0) * 0.9])
            st.metric("At Risk Projects", at_risk_projects, delta="High budget utilization")
        else:
            st.metric("At Risk Projects", "N/A")

def main():
    """Main Project Analytics Dashboard"""
    
    # Header
    st.markdown("""
    <div class="project-header">
        <h1>🚀 Project Analytics Dashboard</h1>
        <p>Comprehensive Project Performance, Budget Tracking & Risk Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch project data
    with st.spinner("Loading project analytics..."):
        api_data, estimates_data, progress_data, alerts_data = get_project_data()
    
    # Display KPIs
    st.subheader("📊 Project Performance KPIs")
    display_project_kpis(api_data, estimates_data, progress_data)
    
    # Main Analytics Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Progress Tracking",
        "💰 Budget Analysis", 
        "⚠️ Risk Assessment",
        "👥 Team Allocation"
    ])
    
    with tab1:
        st.subheader("Project Progress Tracking")
        
        if progress_data:
            # Progress timeline chart
            progress_timeline_fig = create_project_progress_timeline(progress_data)
            if progress_timeline_fig:
                st.plotly_chart(progress_timeline_fig, use_container_width=True)
            
            # Progress details
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Progress Summary")
                for p in progress_data:
                    progress_pct = (p['actual_hours'] / p['estimated_hours'] * 100) if p['estimated_hours'] > 0 else 0
                    status_icon = "🟢" if progress_pct <= 100 else "🟡" if progress_pct <= 110 else "🔴"
                    st.write(f"{status_icon} **{p['project_name']}**: {progress_pct:.1f}% complete")
            
            with col2:
                st.subheader("⏱️ Hours Comparison")
                progress_df = pd.DataFrame([
                    {
                        'Project': p['project_name'],
                        'Estimated': p['estimated_hours'],
                        'Actual': p['actual_hours'],
                        'Variance': p['actual_hours'] - p['estimated_hours']
                    } for p in progress_data
                ])
                st.dataframe(progress_df, use_container_width=True)
        else:
            st.info("💡 Upload project estimates to enable progress tracking")
    
    with tab2:
        st.subheader("Budget Analysis & Financial Tracking")
        
        if progress_data:
            # Budget analysis chart
            budget_fig, budget_df = create_project_budget_analysis(progress_data)
            if budget_fig:
                st.plotly_chart(budget_fig, use_container_width=True)
            
            # Budget summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💰 Budget Status")
                if budget_df is not None:
                    for _, row in budget_df.iterrows():
                        status_color = "🟢" if row['Status'] == 'On Track' else "🟡" if row['Status'] == 'Caution' else "🔴"
                        st.write(f"{status_color} **{row['Project']}**: {row['Utilization %']:.1f}% utilized")
            
            with col2:
                st.subheader("📊 Financial Metrics")
                if budget_df is not None:
                    total_budget = budget_df['Budget'].sum()
                    total_spent = budget_df['Spent'].sum()
                    st.metric("Total Budget", f"${total_budget:,.0f}")
                    st.metric("Total Spent", f"${total_spent:,.0f}")
                    st.metric("Remaining", f"${total_budget - total_spent:,.0f}")
        else:
            st.info("💡 Upload budget estimates to enable financial tracking")
    
    with tab3:
        st.subheader("Risk Assessment & Management")
        
        if progress_data:
            # Risk matrix
            risk_fig, risk_df = create_project_risk_matrix(progress_data)
            if risk_fig:
                st.plotly_chart(risk_fig, use_container_width=True)
            
            # Risk insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚨 High Risk Projects")
                if risk_df is not None:
                    high_risk = risk_df[risk_df['Overall Risk'] > 7]
                    if not high_risk.empty:
                        for _, row in high_risk.iterrows():
                            st.error(f"**{row['Project']}**: Risk Score {row['Overall Risk']:.1f}/10")
                    else:
                        st.success("No high-risk projects identified")
            
            with col2:
                st.subheader("💡 Risk Mitigation")
                st.markdown("""
                **Recommended Actions:**
                - Monitor budget utilization weekly
                - Implement scope change controls
                - Increase team communication
                - Review resource allocation
                - Update estimates regularly
                """)
        else:
            st.info("💡 Enable progress tracking to view risk assessment")
    
    with tab4:
        st.subheader("Team Allocation & Resource Management")
        
        # Team allocation chart - simplified version
        if api_data and 'employees' in api_data:
            import plotly.express as px
            
            # Create simplified team allocation data
            employees = api_data['employees'][:5]  # Show top 5
            allocation = [85, 92, 78, 88, 95]  # Sample allocation percentages
            
            team_data = {
                'Employee': employees,
                'Allocation %': allocation,
                'Status': ['Optimal' if x > 80 else 'Under-utilized' for x in allocation]
            }
            
            fig = px.bar(team_data, x='Employee', y='Allocation %', 
                        color='Status', title='Team Resource Allocation')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 Team allocation data will be displayed when API data is available")
        
        # Team details
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Team Assignment")
            if api_data and 'projects' in api_data:
                projects = api_data['projects'][:3]  # Show top 3
                for i, project in enumerate(projects):
                    team_size = [4, 6, 3][i]
                    lead = ['Alice Johnson', 'Bob Smith', 'Carol Davis'][i]
                    st.write(f"**{project}**: {team_size} people, led by {lead}")
            else:
                st.info("Team assignment data will be shown when available")
        
        with col2:
            st.subheader("⚡ Resource Utilization")
            if api_data and 'projects' in api_data:
                total_people = 13  # Sum of team sizes
                total_hours = 2840  # Sample total hours
                avg_hours_per_person = total_hours / total_people
                
                st.metric("Total Team Members", total_people)
                st.metric("Total Project Hours", f"{total_hours:,.0f}")
                st.metric("Avg Hours/Person", f"{avg_hours_per_person:.1f}")
            else:
                st.info("Resource utilization data will be shown when available")
        
        # Sample team allocation table
        if api_data and 'projects' in api_data:
            st.subheader("Team Allocation Details")
            import pandas as pd
            
            sample_team_data = {
                'Project': api_data['projects'][:3],
                'Team Size': [4, 6, 3],
                'Lead': ['Alice Johnson', 'Bob Smith', 'Carol Davis'],
                'Total Hours': [1200, 1040, 600],
                'Status': ['Active', 'Active', 'Planning']
            }
            
            team_df = pd.DataFrame(sample_team_data)
            st.dataframe(team_df, use_container_width=True)
        else:
            st.info("Detailed team allocation will be shown when project data is available")
    
    # Alerts section
    if alerts_data:
        st.markdown("---")
        st.subheader("🚨 Project Alerts")
        
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

if __name__ == "__main__":
    main()
