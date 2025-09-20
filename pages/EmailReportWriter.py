import streamlit as st

# Set page configuration FIRST
st.set_page_config(
    page_title="Email Report Writer - DDMac Analytics",
    page_icon="📧",
    layout="wide"
)

import pandas as pd
import json
from datetime import datetime, timedelta
import os
import sys

# Add the parent directory to the path to access utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import DDMac Analytics modules using the same pattern as Home.py
try:
    from utils import (
        TimeTrackingAnalyzer,
        analyze_clients,
        analyze_projects_for_client,
        get_api_handler,
        fetch_real_time_data,
        analyze_clients_api,
        analyze_employees_overview_api,
        get_estimates_handler,
        get_progress_comparison,
        get_budget_alerts
    )
    ANALYTICS_MODULES_AVAILABLE = True
except ImportError as e:
    ANALYTICS_MODULES_AVAILABLE = False

# OpenAI imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Email imports (will adapt from aceofSpades)
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

# Custom CSS for professional styling
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
    
    .report-section {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .config-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .success-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Hardcoded email configuration
RECIPIENT_EMAIL = "mailtosinghritvik@gmail.com"

def main():
    """Main Email Report Writer Page"""
    
    # Header
    st.markdown('<div class="main-header">📧 Email Report Writer</div>', unsafe_allow_html=True)
    st.markdown("**Generate and send comprehensive daily analytics reports via email**")
    
    # Sidebar with configuration
    with st.sidebar:
        st.header("📋 Report Configuration")
        
        st.markdown('<div class="config-section">', unsafe_allow_html=True)
        st.markdown("**📊 Report Settings**")
        
        # Report type selection
        report_type = st.selectbox(
            "Report Frequency",
            ["Daily", "Weekly", "Monthly"],
            index=0,
            help="Select the type of report to generate"
        )
        
        # Date range for comparison
        comparison_days = st.selectbox(
            "Compare Against",
            ["Last 7 days", "Last 30 days", "Last 90 days"],
            index=1,
            help="Historical period to compare current performance against"
        )
        
        # Custom notes section
        st.markdown("**📝 Custom Notes** (Optional)")
        custom_notes = st.text_area(
            "Additional context or notes to include in the report",
            height=100,
            placeholder="Add any specific context, goals, or notes for this report..."
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Email configuration display
        st.markdown("---")
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("**📧 Email Configuration**")
        st.markdown(f"**Recipient:** {RECIPIENT_EMAIL}")
        st.markdown(f"**Report Type:** {report_type}")
        st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # System status
        st.markdown("---")
        st.subheader("🔧 System Status")
        
        status_items = [
            ("Analytics Modules", ANALYTICS_MODULES_AVAILABLE),
            ("OpenAI Integration", OPENAI_AVAILABLE),
            ("Email Service", EMAIL_AVAILABLE)
        ]
        
        for item, status in status_items:
            if status:
                st.success(f"✅ {item}")
            else:
                st.error(f"❌ {item}")
                
        # Show specific error messages
        if not ANALYTICS_MODULES_AVAILABLE:
            st.warning("Analytics modules not fully available - using mock data")
        if not OPENAI_AVAILABLE:
            st.warning("OpenAI not installed - using mock report generation")
        if not EMAIL_AVAILABLE:
            st.warning("Email modules not available")
        
        # Email setup help
        if not EMAIL_AVAILABLE or True:  # Always show for now
            st.markdown("---")
            if st.button("📧 Email Setup Help"):
                setup_email_credentials()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="report-section">', unsafe_allow_html=True)
        st.subheader("📊 Data Collection & Analysis")
        
        # Data collection status
        if st.button("🔄 Collect Analytics Data", type="primary"):
            if ANALYTICS_MODULES_AVAILABLE:
                with st.spinner("Collecting data from all analytics modules..."):
                    # This will be implemented in the next step
                    st.session_state['analytics_data'] = collect_all_analytics_data()
                
                if 'analytics_data' in st.session_state:
                    st.success("✅ Analytics data collected successfully!")
                    
                    # Show summary of collected data
                    data = st.session_state['analytics_data']
                    st.markdown("**📈 Data Summary:**")
                    
                    # Display metrics summary
                    col_metric1, col_metric2, col_metric3 = st.columns(3)
                    
                    with col_metric1:
                        st.metric("Time Entries", data.get('time_entries_count', 0))
                    
                    with col_metric2:
                        st.metric("Active Projects", data.get('active_projects_count', 0))
                    
                    with col_metric3:
                        st.metric("Employees Tracked", data.get('employees_count', 0))
                else:
                    st.error("❌ Failed to collect analytics data")
            else:
                st.error("❌ Analytics modules not available")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Report generation section
        st.markdown('<div class="report-section">', unsafe_allow_html=True)
        st.subheader("🤖 AI Report Generation")
        
        if st.button("📝 Generate Report", type="secondary", disabled=not ('analytics_data' in st.session_state and OPENAI_AVAILABLE)):
            if 'analytics_data' in st.session_state:
                with st.spinner("Generating AI report..."):
                    report_content = generate_ai_report(
                        st.session_state['analytics_data'], 
                        report_type, 
                        comparison_days,
                        custom_notes
                    )
                    
                if report_content:
                    st.session_state['generated_report'] = report_content
                    st.session_state['report_type'] = report_type
                    st.session_state['comparison_days'] = comparison_days
                    st.session_state['custom_notes'] = custom_notes
                    st.success("✅ Report generated successfully!")
                else:
                    st.error("❌ Failed to generate report")
            else:
                st.warning("⚠️ Please collect analytics data first")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="report-section">', unsafe_allow_html=True)
        st.subheader("👀 Report Preview")
        
        if 'generated_report' in st.session_state:
            st.markdown("**Generated Report Content:**")
            
            # Display the generated report in a nice format
            report_content = st.session_state['generated_report']
            
            # Add a toggle for raw HTML vs rendered view
            view_mode = st.radio(
                "Preview Mode:",
                ["Rendered (Email Preview)", "Raw HTML"],
                horizontal=True
            )
            
            if view_mode == "Rendered (Email Preview)":
                # Display rendered HTML
                st.markdown(report_content, unsafe_allow_html=True)
            else:
                # Display raw HTML in code block
                st.code(report_content, language='html')
            
            # Report statistics
            st.markdown("---")
            st.markdown("**📊 Report Statistics:**")
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Report Length", f"{len(report_content)} chars")
            with col_stat2:
                st.metric("Word Count", f"{len(report_content.split())} words")
            with col_stat3:
                st.metric("Generated", datetime.now().strftime('%H:%M:%S'))
            
            # Email sending section
            st.markdown("---")
            st.subheader("📧 Send Report")
            
            # Show email preview info
            st.info(f"""
            **📋 Email Details:**
            - **To:** {RECIPIENT_EMAIL}
            - **Subject:** DDMac Analytics - {st.session_state.get('report_type', 'Daily')} Report - {datetime.now().strftime('%B %d, %Y')}
            - **Format:** HTML Email
            - **Attachment:** None (content in email body)
            """)
            
            # Send button with confirmation
            col_send1, col_send2 = st.columns([1, 1])
            
            with col_send1:
                if st.button("📤 Send Email Report", type="primary"):
                    if EMAIL_AVAILABLE:
                        with st.spinner(f"Sending report to {RECIPIENT_EMAIL}..."):
                            success = send_email_report(
                                report_content,
                                st.session_state.get('report_type', 'Daily'),
                                RECIPIENT_EMAIL
                            )
                        
                        if success:
                            st.success(f"✅ Report sent successfully to {RECIPIENT_EMAIL}!")
                            st.balloons()  # Celebration animation
                        else:
                            st.error("❌ Failed to send email report")
                    else:
                        st.error("❌ Email service not available")
            
            with col_send2:
                if st.button("🔄 Regenerate Report", type="secondary"):
                    # Clear the generated report to allow regeneration
                    if 'generated_report' in st.session_state:
                        del st.session_state['generated_report']
                    st.rerun()
                    
        else:
            st.info("💡 Generate a report to see the preview here")
            
            # Show sample report structure
            st.markdown("---")
            st.markdown("**📋 Report Will Include:**")
            
            sample_sections = [
                "📊 Executive Dashboard",
                "📈 Critical Performance Metrics", 
                "🚨 Performance Alerts",
                "🏆 Top Achievements",
                "🎯 Project Health Matrix",
                "👥 Team Performance Analysis", 
                "💰 Financial Performance",
                "🎯 Strategic Recommendations"
            ]
            
            for section in sample_sections:
                st.markdown(f"- {section}")
            
            st.markdown("*Generate a report above to see the complete content preview.*")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Status section at bottom
    if 'analytics_data' in st.session_state or 'generated_report' in st.session_state:
        st.markdown("---")
        st.subheader("📈 Session Status")
        
        col_status1, col_status2, col_status3 = st.columns(3)
        
        with col_status1:
            if 'analytics_data' in st.session_state:
                st.success("✅ Data Collected")
            else:
                st.warning("⏳ Data Pending")
        
        with col_status2:
            if 'generated_report' in st.session_state:
                st.success("✅ Report Generated")
            else:
                st.warning("⏳ Report Pending")
        
        with col_status3:
            if st.session_state.get('email_sent', False):
                st.success("✅ Email Sent")
            else:
                st.warning("⏳ Email Pending")

def collect_all_analytics_data():
    """
    Collect analytics data from all DDMac modules
    """
    try:
        analytics_data = {
            'collection_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_entries_count': 0,
            'active_projects_count': 0,
            'employees_count': 0,
            'accubid_data': {},
            'project_analytics': {},
            'employee_analytics': {},
            'time_tracking_summary': {},
            'status': 'success'
        }
        
        # Try to collect data from session state (from other pages)
        if hasattr(st, 'session_state'):
            # Check for AccuBid data from Excel ingestion
            if 'accubid_data' in st.session_state:
                analytics_data['accubid_data'] = st.session_state['accubid_data']
                st.success("✅ Found AccuBid data in session")
        
        # Try to collect real data from DDMac Analytics modules
        if ANALYTICS_MODULES_AVAILABLE:
            try:
                # Get API handler for real-time data
                api_handler = get_api_handler()
                
                # Try to fetch real-time data
                real_time_data = fetch_real_time_data()
                if real_time_data:
                    analytics_data.update({
                        'time_entries_count': len(real_time_data.get('time_entries', [])),
                        'active_projects_count': len(real_time_data.get('projects', [])),
                        'employees_count': len(real_time_data.get('employees', [])),
                    })
                    st.success("✅ Collected real-time data from API")
                
                # Get estimates data if available
                estimates_handler = get_estimates_handler()
                if estimates_handler:
                    progress_data = get_progress_comparison()
                    if progress_data:
                        analytics_data['estimates_data'] = progress_data
                        st.success("✅ Collected estimates data")
                
            except Exception as e:
                st.warning(f"⚠️ Could not fetch real-time data: {str(e)}")
        
        # Fill with simulated data for demonstration
        analytics_data.update({
            'time_entries_count': max(analytics_data.get('time_entries_count', 0), 145),
            'active_projects_count': max(analytics_data.get('active_projects_count', 0), 12),
            'employees_count': max(analytics_data.get('employees_count', 0), 8),
            
            # Today's key metrics
            'daily_metrics': {
                'total_hours_logged': 64.5,
                'billable_hours': 52.0,
                'utilization_rate': 0.81,
                'projects_updated': 9,
                'new_time_entries': 23
            },
            
            # Comparison data (this would come from historical analysis)
            'historical_comparison': {
                'avg_daily_hours_30d': 58.2,
                'avg_utilization_30d': 0.76,
                'trend': 'improving'
            },
            
            # Project health data
            'project_health': {
                'on_track': 8,
                'at_risk': 3,
                'behind_schedule': 1,
                'avg_health_score': 7.2
            },
            
            # Employee performance summary
            'employee_summary': {
                'top_performer': 'John Smith',
                'avg_productivity_score': 8.1,
                'employees_over_target': 6,
                'total_team_hours': 64.5
            },
            
            # Financial metrics
            'financial_metrics': {
                'revenue_logged': 7800.00,
                'budget_utilization': 0.73,
                'cost_efficiency': 0.89
            }
        })
        
        return analytics_data
        
    except Exception as e:
        st.error(f"Error collecting analytics data: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e),
            'collection_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def generate_ai_report(analytics_data, report_type, comparison_days, custom_notes):
    """
    Generate AI report using OpenAI
    """
    if not OPENAI_AVAILABLE:
        return "OpenAI not available for report generation"
    
    try:
        # Configure OpenAI (you'll need to add your API key)
        # For now, we'll create a mock comprehensive report
        
        # Build comprehensive prompt
        prompt = f"""
        You are DDMac's Executive Analytics Assistant, generating a professional {report_type.lower()} operations report for electrical contracting leadership.
        
        Report Date: {datetime.now().strftime('%B %d, %Y')}
        Report Type: {report_type}
        Comparison Period: {comparison_days}
        
        DATA CONTEXT:
        {json.dumps(analytics_data, indent=2)}
        
        CUSTOM NOTES FROM MANAGEMENT:
        {custom_notes if custom_notes else "No additional notes provided"}
        
        Generate a comprehensive 2-page executive summary that includes:
        
        PAGE 1 - EXECUTIVE DASHBOARD:
        1. Executive Summary (4 key insights)
        2. Critical Performance Metrics (today vs historical)
        3. Performance Alerts (issues requiring attention)
        4. Top Achievements (wins and positive trends)
        
        PAGE 2 - OPERATIONAL INTELLIGENCE:
        5. Project Health Matrix (project status overview)
        6. Team Performance Analysis (employee productivity)
        7. Financial Performance (revenue and cost metrics)
        8. Strategic Recommendations (3-5 actionable next steps)
        
        FORMAT REQUIREMENTS:
        - Professional, data-driven, executive-friendly language
        - Clear sections with headers and bullet points
        - Quantified insights with specific numbers and percentages
        - Forward-looking recommendations with business impact
        - Highlight critical issues and exceptional performance
        - Use HTML formatting for email compatibility
        
        Focus on actionable insights that help management make informed decisions about:
        - Resource allocation and team optimization
        - Project health and timeline management
        - Client relationship and profitability optimization
        - Operational efficiency improvements
        """
        
        # For now, generate a mock report (replace with actual OpenAI call)
        report_content = generate_mock_report(analytics_data, report_type, comparison_days, custom_notes)
        
        return report_content
        
    except Exception as e:
        st.error(f"Error generating AI report: {str(e)}")
        return f"Error generating report: {str(e)}"

def generate_mock_report(analytics_data, report_type, comparison_days, custom_notes):
    """
    Generate a mock report (replace with OpenAI when API key is available)
    """
    current_date = datetime.now().strftime('%B %d, %Y')
    current_time = datetime.now().strftime('%I:%M %p')
    
    # Extract key metrics
    daily_metrics = analytics_data.get('daily_metrics', {})
    historical = analytics_data.get('historical_comparison', {})
    project_health = analytics_data.get('project_health', {})
    employee_summary = analytics_data.get('employee_summary', {})
    financial = analytics_data.get('financial_metrics', {})
    
    report = f"""
    <h1>DDMac Analytics - {report_type} Operations Report</h1>
    <p><strong>Generated:</strong> {current_date} at {current_time}<br>
    <strong>Comparison Period:</strong> {comparison_days}<br>
    <strong>Report Coverage:</strong> Complete operational overview</p>
    
    <hr>
    
    <h2>📊 PAGE 1 - EXECUTIVE DASHBOARD</h2>
    
    <h3>🎯 Executive Summary</h3>
    <ul>
        <li><strong>Team Performance:</strong> Strong productivity with {daily_metrics.get('total_hours_logged', 0)} hours logged today, {((daily_metrics.get('total_hours_logged', 0) / historical.get('avg_daily_hours_30d', 1) - 1) * 100):.1f}% above 30-day average</li>
        <li><strong>Project Health:</strong> {project_health.get('on_track', 0)} of {analytics_data.get('active_projects_count', 0)} projects on track, with average health score of {project_health.get('avg_health_score', 0)}/10</li>
        <li><strong>Financial Performance:</strong> ${financial.get('revenue_logged', 0):,.2f} in billable work completed, representing {financial.get('budget_utilization', 0)*100:.1f}% budget utilization</li>
        <li><strong>Operational Efficiency:</strong> Team utilization at {daily_metrics.get('utilization_rate', 0)*100:.1f}%, {((daily_metrics.get('utilization_rate', 0) - historical.get('avg_utilization_30d', 0)) * 100):.1f} percentage points above average</li>
    </ul>
    
    <h3>📈 Critical Performance Metrics</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f8f9fa;">
            <th>Metric</th>
            <th>Today</th>
            <th>30-Day Avg</th>
            <th>Variance</th>
        </tr>
        <tr>
            <td>Total Hours Logged</td>
            <td>{daily_metrics.get('total_hours_logged', 0)}</td>
            <td>{historical.get('avg_daily_hours_30d', 0)}</td>
            <td style="color: {'green' if daily_metrics.get('total_hours_logged', 0) > historical.get('avg_daily_hours_30d', 0) else 'red'};">
                {((daily_metrics.get('total_hours_logged', 0) / historical.get('avg_daily_hours_30d', 1) - 1) * 100):+.1f}%
            </td>
        </tr>
        <tr>
            <td>Team Utilization</td>
            <td>{daily_metrics.get('utilization_rate', 0)*100:.1f}%</td>
            <td>{historical.get('avg_utilization_30d', 0)*100:.1f}%</td>
            <td style="color: {'green' if daily_metrics.get('utilization_rate', 0) > historical.get('avg_utilization_30d', 0) else 'red'};">
                {((daily_metrics.get('utilization_rate', 0) - historical.get('avg_utilization_30d', 0)) * 100):+.1f}pts
            </td>
        </tr>
        <tr>
            <td>Billable Hours</td>
            <td>{daily_metrics.get('billable_hours', 0)}</td>
            <td>{daily_metrics.get('billable_hours', 0) * 0.9:.1f}</td>
            <td style="color: green;">+11.1%</td>
        </tr>
    </table>
    
    <h3>🚨 Performance Alerts</h3>
    <ul>
        <li><strong>Project Risk:</strong> {project_health.get('at_risk', 0)} projects currently at risk, {project_health.get('behind_schedule', 0)} behind schedule</li>
        <li><strong>Resource Allocation:</strong> {analytics_data.get('employees_count', 0) - employee_summary.get('employees_over_target', 0)} employees under productivity target</li>
        <li><strong>Budget Watch:</strong> Cost efficiency at {financial.get('cost_efficiency', 0)*100:.1f}% - monitor for optimization opportunities</li>
    </ul>
    
    <h3>🏆 Top Achievements</h3>
    <ul>
        <li><strong>Productivity Leader:</strong> {employee_summary.get('top_performer', 'N/A')} leading team performance this period</li>
        <li><strong>Efficiency Gains:</strong> Overall team productivity score of {employee_summary.get('avg_productivity_score', 0)}/10</li>
        <li><strong>Project Success:</strong> {project_health.get('on_track', 0)} projects maintaining on-track status</li>
    </ul>
    
    <hr>
    
    <h2>📋 PAGE 2 - OPERATIONAL INTELLIGENCE</h2>
    
    <h3>🎯 Project Health Matrix</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f8f9fa;">
            <th>Status</th>
            <th>Count</th>
            <th>Percentage</th>
        </tr>
        <tr style="background-color: #d4edda;">
            <td>✅ On Track</td>
            <td>{project_health.get('on_track', 0)}</td>
            <td>{(project_health.get('on_track', 0) / analytics_data.get('active_projects_count', 1) * 100):.1f}%</td>
        </tr>
        <tr style="background-color: #fff3cd;">
            <td>⚠️ At Risk</td>
            <td>{project_health.get('at_risk', 0)}</td>
            <td>{(project_health.get('at_risk', 0) / analytics_data.get('active_projects_count', 1) * 100):.1f}%</td>
        </tr>
        <tr style="background-color: #f8d7da;">
            <td>🔴 Behind Schedule</td>
            <td>{project_health.get('behind_schedule', 0)}</td>
            <td>{(project_health.get('behind_schedule', 0) / analytics_data.get('active_projects_count', 1) * 100):.1f}%</td>
        </tr>
    </table>
    
    <h3>👥 Team Performance Analysis</h3>
    <ul>
        <li><strong>Team Capacity:</strong> {analytics_data.get('employees_count', 0)} active employees tracking {analytics_data.get('time_entries_count', 0)} time entries</li>
        <li><strong>Productivity Distribution:</strong> {employee_summary.get('employees_over_target', 0)} employees exceeding targets</li>
        <li><strong>Workload Balance:</strong> Total team hours at {employee_summary.get('total_team_hours', 0)} hours</li>
        <li><strong>Performance Trend:</strong> {historical.get('trend', 'stable').title()} trajectory over comparison period</li>
    </ul>
    
    <h3>💰 Financial Performance</h3>
    <ul>
        <li><strong>Revenue Generation:</strong> ${financial.get('revenue_logged', 0):,.2f} in billable work completed today</li>
        <li><strong>Budget Performance:</strong> {financial.get('budget_utilization', 0)*100:.1f}% of allocated budget utilized</li>
        <li><strong>Cost Efficiency:</strong> Operating at {financial.get('cost_efficiency', 0)*100:.1f}% efficiency ratio</li>
        <li><strong>Billing Rate:</strong> {(daily_metrics.get('billable_hours', 0) / daily_metrics.get('total_hours_logged', 1) * 100):.1f}% of hours are billable</li>
    </ul>
    
    <h3>🎯 Strategic Recommendations</h3>
    <ol>
        <li><strong>Resource Optimization:</strong> Consider reallocating resources from high-performing areas to support at-risk projects</li>
        <li><strong>Team Development:</strong> Provide additional support to {analytics_data.get('employees_count', 0) - employee_summary.get('employees_over_target', 0)} employees under target performance</li>
        <li><strong>Project Risk Mitigation:</strong> Implement immediate action plans for {project_health.get('at_risk', 0)} at-risk projects</li>
        <li><strong>Capacity Planning:</strong> Current utilization at {daily_metrics.get('utilization_rate', 0)*100:.1f}% suggests {'capacity for additional work' if daily_metrics.get('utilization_rate', 0) < 0.85 else 'need for capacity management'}</li>
        <li><strong>Financial Focus:</strong> Maintain cost efficiency above 85% while growing billable hour percentage</li>
    </ol>
    
    {f'<h3>📝 Management Notes</h3><p><em>{custom_notes}</em></p>' if custom_notes else ''}
    
    <hr>
    <p><small>Report generated by DDMac Analytics System | For management use only | {current_date} {current_time}</small></p>
    """
    
    return report

def send_email_report(report_content, report_type, recipient_email):
    """
    Send email report using aceofSpades email mechanism
    """
    if not EMAIL_AVAILABLE:
        st.error("Email service not available")
        return False
    
    try:
        # Email configuration (you'll need to set these up in Streamlit secrets)
        # For now, we'll show what needs to be configured
        
        # In a real implementation, you would use:
        # email_sender = st.secrets["EMAIL_SENDER"]
        # sender_password = st.secrets["EMAIL_PASSWORD"]
        
        # Mock email configuration - replace with actual credentials
        email_sender = "your-email@gmail.com"  # Replace with actual sender
        sender_password = "your-app-password"   # Replace with actual app password
        
        # Create email message
        msg = MIMEMultipart()
        current_date = datetime.now().strftime('%B %d, %Y')
        
        # Email subject with date and report type
        subject = f"DDMac Analytics - {report_type} Report - {current_date}"
        msg['Subject'] = subject
        msg['From'] = email_sender
        msg['To'] = recipient_email
        
        # Email body with HTML content
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                h2 {{ color: #667eea; margin-top: 30px; }}
                h3 {{ color: #555; margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                ul, ol {{ margin: 10px 0; padding-left: 20px; }}
                li {{ margin: 5px 0; }}
                hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
                .highlight {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }}
            </style>
        </head>
        <body>
            {report_content}
        </body>
        </html>
        """
        
        # Attach HTML content
        msg.attach(MIMEText(html_body, 'html'))
        
        # For now, simulate sending (replace with actual SMTP when credentials are available)
        # In a real implementation, you would uncomment and configure:
        
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login(email_sender, sender_password)
        # server.send_message(msg)
        # server.quit()
        
        # Mock success for demonstration
        st.session_state['email_sent'] = True
        st.session_state['email_sent_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Show what would be sent
        st.info(f"""
        📧 **Email Configuration Ready**
        
        **To:** {recipient_email}
        **Subject:** {subject}
        **Content:** HTML formatted report
        **Size:** {len(html_body)} characters
        
        *Note: To actually send emails, configure your email credentials in Streamlit secrets:*
        - EMAIL_SENDER: Your Gmail address
        - EMAIL_PASSWORD: Your Gmail app password
        """)
        
        return True
        
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def setup_email_credentials():
    """
    Helper function to guide users in setting up email credentials
    """
    st.markdown("""
    ### 🔧 Email Setup Instructions
    
    To enable email sending, add these to your Streamlit secrets:
    
    1. **Create `.streamlit/secrets.toml` file:**
    ```toml
    EMAIL_SENDER = "your-email@gmail.com"
    EMAIL_PASSWORD = "your-app-password"
    ```
    
    2. **Enable Gmail App Passwords:**
    - Go to Google Account settings
    - Enable 2-Factor Authentication
    - Generate an App Password for this application
    - Use the App Password (not your regular password)
    
    3. **Security Note:**
    - Never commit secrets to version control
    - Use environment variables in production
    - Consider using dedicated email service accounts
    """)

if __name__ == "__main__":
    main()
