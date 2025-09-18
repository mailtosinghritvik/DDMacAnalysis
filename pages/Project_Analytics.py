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

def create_project_team_allocation(team_allocation_data):
    """Create project team allocation chart using real API data"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None, None
    
    # Create efficiency vs hours scatter plot
    fig = px.scatter(
        team_allocation_data,
        x='Total_Hours',
        y='Efficiency_Score',
        size='Days_Worked',
        color='Status',
        hover_data=['Client', 'Avg_Hours_Per_Day', 'Days_Worked'],
        title='Team Allocation: Efficiency vs Total Hours Analysis',
        labels={
            'Total_Hours': 'Total Hours',
            'Efficiency_Score': 'Efficiency Score (%)',
            'Days_Worked': 'Days Worked'
        },
        color_discrete_map={
            'High Performance': '#28a745',
            'Good Performance': '#17a2b8',
            'Average Performance': '#ffc107',
            'Low Performance': '#dc3545'
        }
    )
    
    # Add efficiency reference lines
    fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="High Performance (80%)")
    fig.add_hline(y=60, line_dash="dash", line_color="blue", annotation_text="Good Performance (60%)")
    fig.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text="Average Performance (40%)")
    
    # Improve layout
    fig.update_layout(
        height=600,
        xaxis_title="Total Hours (Log Scale)",
        yaxis_title="Efficiency Score (%)",
        xaxis=dict(type="log"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig, team_allocation_data

def create_team_allocation_summary_chart(team_allocation_data):
    """Create team allocation summary bar chart"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    # Group by status and calculate metrics
    status_summary = team_allocation_data.groupby('Status').agg({
        'Total_Hours': 'sum',
        'Client': 'count',
        'Efficiency_Score': 'mean'
    }).reset_index()
    
    status_summary.columns = ['Status', 'Total_Hours', 'Client_Count', 'Avg_Efficiency']
    
    # Create horizontal bar chart
    fig = px.bar(
        status_summary,
        x='Total_Hours',
        y='Status',
        color='Status',
        orientation='h',
        title='Team Allocation Summary by Performance Status',
        labels={
            'Total_Hours': 'Total Hours',
            'Status': 'Performance Status'
        },
        color_discrete_map={
            'High Performance': '#28a745',
            'Good Performance': '#17a2b8',
            'Average Performance': '#ffc107',
            'Low Performance': '#dc3545'
        }
    )
    
    # Add client count and efficiency as text annotations
    for i, row in status_summary.iterrows():
        fig.add_annotation(
            x=row['Total_Hours'] + max(status_summary['Total_Hours']) * 0.01,
            y=row['Status'],
            text=f"{int(row['Client_Count'])} clients<br>Avg: {row['Avg_Efficiency']:.1f}%",
            showarrow=False,
            font=dict(size=10),
            align="left"
        )
    
    # Add percentage annotations
    total_hours = status_summary['Total_Hours'].sum()
    for i, row in status_summary.iterrows():
        pct = (row['Total_Hours'] / total_hours) * 100
        fig.add_annotation(
            x=row['Total_Hours'] / 2,
            y=row['Status'],
            text=f"{pct:.1f}%",
            showarrow=False,
            font=dict(size=12, color="white", family="Arial Black"),
            align="center"
        )
    
    fig.update_layout(
        height=400,
        xaxis_title="Total Hours",
        yaxis_title="Performance Status",
        showlegend=False
    )
    return fig

def create_client_hours_distribution(team_allocation_data):
    """Create client hours distribution pie chart"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    # Get top 10 clients by hours
    top_clients = team_allocation_data.nlargest(10, 'Total_Hours')
    
    fig = px.pie(
        top_clients,
        values='Total_Hours',
        names='Client',
        title='Top 10 Clients by Total Hours',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    return fig

def create_efficiency_distribution_chart(team_allocation_data):
    """Create efficiency distribution histogram"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    fig = px.histogram(
        team_allocation_data,
        x='Efficiency_Score',
        nbins=20,
        title='Efficiency Score Distribution',
        labels={'Efficiency_Score': 'Efficiency Score (%)', 'count': 'Number of Clients'},
        color_discrete_sequence=['#17a2b8']
    )
    
    # Add efficiency reference lines
    fig.add_vline(x=80, line_dash="dash", line_color="green", annotation_text="High (80%)")
    fig.add_vline(x=60, line_dash="dash", line_color="blue", annotation_text="Good (60%)")
    fig.add_vline(x=40, line_dash="dash", line_color="orange", annotation_text="Avg (40%)")
    
    fig.update_layout(height=400)
    return fig

def create_hours_vs_days_chart(team_allocation_data):
    """Create hours vs days worked scatter plot"""
    if team_allocation_data is None or team_allocation_data.empty:
        return None
    
    fig = px.scatter(
        team_allocation_data,
        x='Days_Worked',
        y='Total_Hours',
        size='Efficiency_Score',
        color='Status',
        hover_data=['Client', 'Avg_Hours_Per_Day'],
        title='Hours vs Days Worked Analysis',
        labels={
            'Days_Worked': 'Days Worked',
            'Total_Hours': 'Total Hours',
            'Efficiency_Score': 'Efficiency Score'
        },
        color_discrete_map={
            'High Performance': '#28a745',
            'Good Performance': '#17a2b8',
            'Average Performance': '#ffc107',
            'Low Performance': '#dc3545'
        }
    )
    
    fig.update_layout(height=400)
    return fig

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
        
        # Get team allocation data from API
        team_allocation_data = api_data.get('team_allocation') if api_data else None
        
        if team_allocation_data is not None and not team_allocation_data.empty:
            # Display KPIs for team allocation
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_hours = team_allocation_data['Total_Hours'].sum()
                st.metric("Total Hours", f"{total_hours:,.0f}")
            
            with col2:
                total_clients = len(team_allocation_data)
                st.metric("Active Clients", total_clients)
            
            with col3:
                avg_efficiency = team_allocation_data['Efficiency_Score'].mean()
                st.metric("Avg Efficiency", f"{avg_efficiency:.1f}%")
            
            with col4:
                high_performers = len(team_allocation_data[team_allocation_data['Status'] == 'High Performance'])
                st.metric("High Performers", high_performers)
            
            # Main allocation chart
            allocation_fig, allocation_df = create_project_team_allocation(team_allocation_data)
            if allocation_fig:
                st.plotly_chart(allocation_fig, use_container_width=True)
            
            # Additional charts - Full width layout
            st.subheader("📊 Performance Analysis Charts")
            
            # Summary chart - Full width
            summary_fig = create_team_allocation_summary_chart(team_allocation_data)
            if summary_fig:
                st.plotly_chart(summary_fig, use_container_width=True)
            
            # Client distribution and efficiency charts side by side
            col1, col2 = st.columns(2)
            
            with col1:
                # Client distribution chart
                distribution_fig = create_client_hours_distribution(team_allocation_data)
                if distribution_fig:
                    st.plotly_chart(distribution_fig, use_container_width=True)
            
            with col2:
                # Efficiency distribution chart
                efficiency_fig = create_efficiency_distribution_chart(team_allocation_data)
                if efficiency_fig:
                    st.plotly_chart(efficiency_fig, use_container_width=True)
            
            # Additional analysis charts - Full width
            st.subheader("📈 Advanced Analytics")
            
            # Hours vs Days analysis - Full width
            hours_days_fig = create_hours_vs_days_chart(team_allocation_data)
            if hours_days_fig:
                st.plotly_chart(hours_days_fig, use_container_width=True)
            
            # Performance insights and metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("🎯 Performance Insights")
                
                # Top performers
                top_performers = team_allocation_data.nlargest(3, 'Efficiency_Score')
                st.write("**Top Performers:**")
                for _, row in top_performers.iterrows():
                    st.write(f"• **{row['Client']}**: {row['Efficiency_Score']:.1f}% efficiency ({row['Total_Hours']:.0f} hours)")
                
                # Areas for improvement
                low_performers = team_allocation_data[team_allocation_data['Status'] == 'Low Performance']
                if not low_performers.empty:
                    st.write("**Areas for Improvement:**")
                    for _, row in low_performers.iterrows():
                        st.write(f"• **{row['Client']}**: {row['Efficiency_Score']:.1f}% efficiency - needs attention")
            
            with col2:
                st.subheader("📊 Resource Distribution")
                
                # Hours distribution
                total_hours = team_allocation_data['Total_Hours'].sum()
                high_perf_hours = team_allocation_data[team_allocation_data['Status'] == 'High Performance']['Total_Hours'].sum()
                high_perf_pct = (high_perf_hours / total_hours * 100) if total_hours > 0 else 0
                
                st.metric("High Performance Hours", f"{high_perf_hours:,.0f} ({high_perf_pct:.1f}%)")
                
                # Average metrics
                avg_hours_per_client = team_allocation_data['Total_Hours'].mean()
                avg_days_per_client = team_allocation_data['Days_Worked'].mean()
                
                st.metric("Avg Hours per Client", f"{avg_hours_per_client:.1f}")
                st.metric("Avg Days per Client", f"{avg_days_per_client:.0f}")
            
            with col3:
                st.subheader("📈 Efficiency Metrics")
                
                # Efficiency statistics
                avg_efficiency = team_allocation_data['Efficiency_Score'].mean()
                max_efficiency = team_allocation_data['Efficiency_Score'].max()
                min_efficiency = team_allocation_data['Efficiency_Score'].min()
                
                st.metric("Average Efficiency", f"{avg_efficiency:.1f}%")
                st.metric("Max Efficiency", f"{max_efficiency:.1f}%")
                st.metric("Min Efficiency", f"{min_efficiency:.1f}%")
                
                # Performance breakdown
                status_counts = team_allocation_data['Status'].value_counts()
                st.write("**Performance Breakdown:**")
                for status, count in status_counts.items():
                    pct = (count / len(team_allocation_data)) * 100
                    st.write(f"• {status}: {count} ({pct:.1f}%)")
            
            # Data table with full width and better formatting
            st.subheader("📋 Complete Team Allocation Data")
            
            # Format the dataframe for better display
            display_df = team_allocation_data.copy()
            display_df = display_df.sort_values('Efficiency_Score', ascending=False)
            
            # Round numeric columns for better display
            numeric_columns = ['Total_Hours', 'Avg_Hours_Per_Day', 'Efficiency_Score']
            for col in numeric_columns:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(2)
            
            # Add color coding for status
            def highlight_status(row):
                colors = {
                    'High Performance': 'background-color: #d4edda; color: #155724;',
                    'Good Performance': 'background-color: #d1ecf1; color: #0c5460;',
                    'Average Performance': 'background-color: #fff3cd; color: #856404;',
                    'Low Performance': 'background-color: #f8d7da; color: #721c24;'
                }
                return [colors.get(row['Status'], '')] * len(row)
            
            # Apply styling
            styled_df = display_df.style.apply(highlight_status, axis=1)
            
            # Configure column formatting
            styled_df = styled_df.format({
                'Total_Hours': '{:,.1f}',
                'Avg_Hours_Per_Day': '{:.2f}',
                'Efficiency_Score': '{:.1f}%',
                'Days_Worked': '{:.0f}'
            })
            
            # Display the styled dataframe with selection
            selected_indices = st.dataframe(
                styled_df,
                use_container_width=True,
                height=400,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Handle row selection for detailed timesheet view
            if selected_indices.selection.rows:
                selected_row_idx = selected_indices.selection.rows[0]
                selected_row = display_df.iloc[selected_row_idx]
                
                # Display detailed timesheet data
                st.markdown("---")
                st.subheader(f"📊 User Details for {selected_row['Client']}")
                
                # Get detailed user data
                api_handler = get_api_handler()
                user_data = api_handler.fetch_client_user_data(
                    jobcode_id=selected_row['Jobcode_ID'],
                    user_id=selected_row['User_ID'],
                    period="daily",
                    page=1,
                    limit=10
                )
                
                if user_data and user_data.get('data'):
                    # Display summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Users", user_data.get('total', 0))
                    
                    with col2:
                        total_duration = sum(entry.get('total_duration', 0) for entry in user_data['data'])
                        st.metric("Total Duration", f"{total_duration:.1f} hours")
                    
                    with col3:
                        avg_duration = total_duration / len(user_data['data']) if user_data['data'] else 0
                        st.metric("Avg Duration/User", f"{avg_duration:.1f} hours")
                    
                    with col4:
                        total_days = sum(entry.get('days_worked', 0) for entry in user_data['data'])
                        st.metric("Total Days Worked", f"{total_days:.0f} days")
                    
                    # Display user details table
                    users_df = pd.DataFrame(user_data['data'])
                    
                    # Format the user data
                    if not users_df.empty:
                        # Calculate additional metrics
                        users_df['avg_hours_per_day'] = users_df['total_duration'] / users_df['days_worked'].replace(0, 1)
                        users_df['efficiency_score'] = (users_df['avg_hours_per_day'] / 8 * 100).clip(0, 100)
                        
                        # Format dates
                        users_df['start_date'] = pd.to_datetime(users_df['start_date']).dt.strftime('%Y-%m-%d')
                        users_df['end_date'] = pd.to_datetime(users_df['end_date']).dt.strftime('%Y-%m-%d')
                        
                        # Select and rename columns for display
                        display_columns = ['username', 'user_id', 'total_duration', 'days_worked', 'avg_hours_per_day', 'efficiency_score', 'start_date', 'end_date']
                        users_display = users_df[display_columns].copy()
                        users_display.columns = ['Username', 'User ID', 'Total Hours', 'Days Worked', 'Avg Hours/Day', 'Efficiency %', 'Start Date', 'End Date']
                        
                        # Round numeric columns
                        numeric_cols = ['Total Hours', 'Avg Hours/Day', 'Efficiency %']
                        for col in numeric_cols:
                            users_display[col] = users_display[col].round(2)
                        
                        # Add efficiency status
                        def get_efficiency_status(efficiency):
                            if efficiency >= 80:
                                return "High Performance"
                            elif efficiency >= 60:
                                return "Good Performance"
                            elif efficiency >= 40:
                                return "Average Performance"
                            else:
                                return "Low Performance"
                        
                        users_display['Status'] = users_display['Efficiency %'].apply(get_efficiency_status)
                        
                        # Add color coding for efficiency status
                        def highlight_user_status(row):
                            colors = {
                                'High Performance': 'background-color: #d4edda; color: #155724;',
                                'Good Performance': 'background-color: #d1ecf1; color: #0c5460;',
                                'Average Performance': 'background-color: #fff3cd; color: #856404;',
                                'Low Performance': 'background-color: #f8d7da; color: #721c24;'
                            }
                            return [colors.get(row['Status'], '')] * len(row)
                        
                        styled_users = users_display.style.apply(highlight_user_status, axis=1)
                        styled_users = styled_users.format({
                            'Total Hours': '{:.1f}',
                            'Avg Hours/Day': '{:.2f}',
                            'Efficiency %': '{:.1f}%'
                        })
                        
                        # Make the dataframe selectable for username clicks
                        selected_user_indices = st.dataframe(
                            styled_users,
                            use_container_width=True,
                            height=300,
                            on_select="rerun",
                            selection_mode="single-row"
                        )
                        
                        # Handle username selection for detailed daily data
                        if selected_user_indices.selection.rows:
                            selected_user_idx = selected_user_indices.selection.rows[0]
                            selected_user = users_display.iloc[selected_user_idx]
                            
                            # Display detailed daily timesheet data
                            st.markdown("---")
                            st.subheader(f"📅 Daily Timesheet for {selected_user['Username']} - {selected_row['Client']}")
                            
                            # Get detailed daily data for the selected user
                            daily_data = api_handler.fetch_user_daily_data(
                                jobcode_id=selected_row['Jobcode_ID'],
                                user_id=selected_user['User ID'],
                                period="daily",
                                page=1,
                                limit=10
                            )
                            
                            if daily_data and daily_data.get('data'):
                                # Display daily summary metrics
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Total Entries", daily_data.get('total', 0))
                                
                                with col2:
                                    total_duration = sum(entry.get('duration', 0) for entry in daily_data['data'])
                                    st.metric("Total Duration", f"{total_duration:.1f} hours")
                                
                                with col3:
                                    approved_count = len([entry for entry in daily_data['data'] if entry.get('status') == 'approved'])
                                    st.metric("Approved Entries", approved_count)
                                
                                with col4:
                                    pending_count = len([entry for entry in daily_data['data'] if entry.get('status') == 'pending'])
                                    st.metric("Pending Entries", pending_count)
                                
                                # Display detailed daily timesheet table
                                daily_df = pd.DataFrame(daily_data['data'])
                                
                                # Format the daily data
                                if not daily_df.empty:
                                    daily_df['date'] = pd.to_datetime(daily_df['date']).dt.strftime('%Y-%m-%d')
                                    daily_display = daily_df[['date', 'start_time', 'end_time', 'duration', 'description', 'status']].copy()
                                    daily_display.columns = ['Date', 'Start Time', 'End Time', 'Duration (hrs)', 'Description', 'Status']
                                    
                                    # Add status color coding
                                    def highlight_daily_status(row):
                                        if row['Status'] == 'approved':
                                            return ['background-color: #d4edda; color: #155724;'] * len(row)
                                        elif row['Status'] == 'pending':
                                            return ['background-color: #fff3cd; color: #856404;'] * len(row)
                                        else:
                                            return ['background-color: #f8d7da; color: #721c24;'] * len(row)
                                    
                                    styled_daily = daily_display.style.apply(highlight_daily_status, axis=1)
                                    styled_daily = styled_daily.format({'Duration (hrs)': '{:.1f}'})
                                    
                                    st.dataframe(
                                        styled_daily,
                                        use_container_width=True,
                                        height=300
                                    )
                                    
                                    # Display API call info
                                    st.info(f"📡 **API Call**: `GET /api/v1/client-user-data/{selected_row['Jobcode_ID']}?period=daily&limit=10&page=1&user_id={selected_user['User ID']}`")
                                    
                                    # Show pagination info
                                    if daily_data.get('total_pages', 0) > 1:
                                        st.write(f"📄 **Pagination**: Page {daily_data.get('page', 1)} of {daily_data.get('total_pages', 1)} (Total: {daily_data.get('total', 0)} entries)")
                            else:
                                st.warning("No daily timesheet data available for this user.")
                        
                        # Display API call info
                        st.info(f"📡 **API Call**: `GET /api/v1/client-user-data/{selected_row['Jobcode_ID']}?period=daily&limit=10&page=1`")
                        
                        # Show pagination info
                        if user_data.get('total_pages', 0) > 1:
                            st.write(f"📄 **Pagination**: Page {user_data.get('page', 1)} of {user_data.get('total_pages', 1)} (Total: {user_data.get('total', 0)} users)")
                        
                        # Additional insights
                        st.subheader("📈 User Performance Insights")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Top Performers by Hours:**")
                            top_users = users_display.nlargest(3, 'Total Hours')
                            for _, row in top_users.iterrows():
                                st.write(f"• **{row['Username']}**: {row['Total Hours']:.1f} hours ({row['Status']})")
                        
                        with col2:
                            st.write("**Most Efficient Users:**")
                            efficient_users = users_display.nlargest(3, 'Efficiency %')
                            for _, row in efficient_users.iterrows():
                                st.write(f"• **{row['Username']}**: {row['Efficiency %']:.1f}% efficiency")
                else:
                    st.warning("No user data available for this selection.")
            
            # Add summary statistics below the table
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Clients", len(display_df))
            
            with col2:
                st.metric("Total Hours", f"{display_df['Total_Hours'].sum():,.0f}")
            
            with col3:
                st.metric("Avg Efficiency", f"{display_df['Efficiency_Score'].mean():.1f}%")
            
            with col4:
                high_perf_count = len(display_df[display_df['Status'] == 'High Performance'])
                st.metric("High Performers", f"{high_perf_count}/{len(display_df)}")
            
        else:
            st.info("💡 Team allocation data will be displayed when API data is available")
            
            # Fallback display
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👥 Team Assignment")
                st.info("Team assignment data will be shown when available")
            
            with col2:
                st.subheader("⚡ Resource Utilization")
                st.info("Resource utilization data will be shown when available")
    
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
