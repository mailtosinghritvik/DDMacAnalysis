import streamlit as st
import os
import tempfile
import requests
import json
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
# Perplexity functions are now imported from utils.perplexity_client



# Basic imports
from datetime import datetime, timedelta

# Import database handler
from utils.supabase_queries import get_supabase_handler

# Import Perplexity client
from utils.perplexity_client import get_perplexity_client

# Initialize Perplexity client
client = get_perplexity_client()

# Initialize session state (following Home.py pattern)
if 'ai_assistant_id' not in st.session_state:
    st.session_state.ai_assistant_id = None
if 'ai_thread_id' not in st.session_state:
    st.session_state.ai_thread_id = None
if 'ai_chat_messages' not in st.session_state:
    st.session_state.ai_chat_messages = []
if 'generated_markdown' not in st.session_state:
    st.session_state.generated_markdown = None
if 'pdf_generated' not in st.session_state:
    st.session_state.pdf_generated = False
if 'ai_processing_status' not in st.session_state:
    st.session_state.ai_processing_status = 'ready'
if 'proceed_with_ai_generation' not in st.session_state:
    st.session_state.proceed_with_ai_generation = False
if 'report_results' not in st.session_state:
    st.session_state.report_results = []
if 'ai_pdf_bytes' not in st.session_state:
    st.session_state.ai_pdf_bytes = None
if 'ai_pdf_path' not in st.session_state:
    st.session_state.ai_pdf_path = None


def _sanitize_text_for_pdf(text: str) -> str:
    """Sanitize text for FPDF (latin-1) output to avoid encoding errors."""
    try:
        if not isinstance(text, str):
            text = str(text)
        return text.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return str(text)


def generate_pdf_from_markdown(markdown_content: str, title: str = "Analytics Report") -> bytes:
    """Generate a simple PDF from markdown content locally using FPDF.

    This is a lightweight renderer: headings, paragraphs, and bullet lists.
    """
    def _soft_wrap_long_tokens(s: str, max_len: int = 60) -> str:
        # Break very long tokens (e.g., URLs, long numbers) to avoid width errors
        parts = []
        for token in s.split(' '):
            if len(token) > max_len:
                chunks = [token[i:i+max_len] for i in range(0, len(token), max_len)]
                parts.append(' '.join(chunks))
            else:
                parts.append(token)
        return ' '.join(parts)

    pdf = FPDF(format='Letter', unit='pt')
    pdf.set_margins(36, 36, 36)
    pdf.set_auto_page_break(auto=True, margin=48)
    pdf.add_page()

    # Title
    epw = getattr(pdf, 'epw', pdf.w - pdf.l_margin - pdf.r_margin)
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(epw, 24, _sanitize_text_for_pdf(_soft_wrap_long_tokens(title, 40)))
    pdf.ln(6)

    # Normalize content: collapse excessive blank lines
    raw_lines = markdown_content.splitlines()
    lines = []
    blank_streak = 0
    for raw in raw_lines:
        s = raw.rstrip()
        if not s.strip():
            blank_streak += 1
            if blank_streak <= 1:
                lines.append("")
        else:
            blank_streak = 0
            lines.append(s)
    for raw in lines:
        line = raw.rstrip()

        if not line.strip():
            pdf.ln(6)
            continue

        if line.startswith("### "):
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(epw, 16, _sanitize_text_for_pdf(_soft_wrap_long_tokens(line[4:], 60)))
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(epw, 18, _sanitize_text_for_pdf(_soft_wrap_long_tokens(line[3:], 60)))
            pdf.ln(4)
        elif line.startswith("# "):
            pdf.set_font("Arial", "B", 16)
            pdf.multi_cell(epw, 20, _sanitize_text_for_pdf(_soft_wrap_long_tokens(line[2:], 60)))
            pdf.ln(6)
        elif line.lstrip().startswith(("- ", "* ")):
            bullet_text = line.lstrip()[2:]
            pdf.set_font("Arial", "", 11)
            # Draw bullet and indent text for the remaining width
            # Use ASCII dash for maximum font compatibility
            pdf.set_x(pdf.l_margin)
            pdf.cell(14, 14, "-")
            pdf.multi_cell(epw - 14, 14, _sanitize_text_for_pdf(_soft_wrap_long_tokens(bullet_text, 60)))
            pdf.ln(2)
        else:
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(epw, 16, _sanitize_text_for_pdf(_soft_wrap_long_tokens(line, 80)))

    # Return PDF bytes
    raw = pdf.output(dest='S')
    # fpdf2 may return str, bytes, or bytearray depending on version
    if isinstance(raw, bytearray):
        return bytes(raw)
    if isinstance(raw, bytes):
        return raw
    # Fallback: encode string to latin-1
    return str(raw).encode('latin-1', 'ignore')


def send_pdf_via_email(recipient_email: str, subject: str, body: str, pdf_bytes: bytes, filename: str) -> None:
    """Send a PDF via SMTP using environment variables if available.
    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    """
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    mail_from = os.getenv('SMTP_FROM', smtp_user or '')

    if not (smtp_host and smtp_user and smtp_pass and mail_from):
        raise RuntimeError("SMTP not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM.")

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = mail_from
    msg['To'] = recipient_email
    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=filename)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


def save_pdf_to_disk(pdf_bytes: bytes, filename: str) -> str:
    """Save PDF bytes to disk under temp/ai_reports and return the absolute path."""
    reports_dir = os.path.join(os.getcwd(), 'temp', 'ai_reports')
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    return file_path

def create_ai_report_assistant(markdown_content, report_type, report_name):
    """Create a dedicated Assistant for generating comprehensive PDF reports"""
    try:
        # Create a markdown file for the assistant
        temp_path = os.path.join(tempfile.gettempdir(), f"{report_name.replace(' ', '_')}_report.md")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Upload markdown file to Perplexity
        file_obj = client.upload_file(temp_path, 'assistants')

        # Clean up temp file
        os.remove(temp_path)
        
        # Create Assistant with Perplexity
        assistant_name = f"DDMac Bot - {report_name} Analyzer"
        assistant_description = f"""DDMac Bot expert for {report_type.lower()} analytics and PDF generation.

Report: {report_name} | Type: {report_type}

Analyzes report data and creates professional PDFs with visualizations. Specializes in electrical estimation and construction project analytics."""

        assistant = client.create_assistant(assistant_name, assistant_description)
        
        # Create a thread
        thread = client.create_thread()
        
        return assistant["id"], thread["id"], file_obj["id"], "Perplexity AI Report Assistant created successfully"
        
    except Exception as e:
        return None, None, None, f"Error creating Perplexity AI assistant: {str(e)}"

# Import utility functions for report generation
from utils.report_generators import (
    get_last_entry_date,
    get_available_users,
    get_available_clients,
    find_user_in_database,
    find_client_in_database,
    generate_user_analytics_markdown,
    generate_fallback_user_report,
    generate_client_analytics_markdown,
    generate_fallback_client_report,
    generate_time_analytics_markdown,
    generate_fallback_time_analytics_report
)


def get_user_analytics_report(selected_user, start_date, end_date, use_system_date):
    """
    Generate user analytics report based on configuration
    
    Args:
        selected_user (str): The selected user name
        start_date (date): Start date for the report
        end_date (date): End date for the report  
        use_system_date (bool): Whether using system last entry date or custom
    
    Returns:
        str: User analytics report in markdown format
    """
    try:
        # Get database handler
        db_handler = get_supabase_handler()
        
        # Get users from database
        users_data = db_handler.get_available_users()
        
        # Find the user with flexible matching
        user_id, user_display_name = find_user_in_database(selected_user, users_data)
        
        if not user_id:
            # Show available users for debugging
            available_users = []
            for user in users_data[:10]:  # Show first 10 users
                if user.get('display_name'):
                    available_users.append(user.get('display_name'))
                elif user.get('first_name') and user.get('last_name'):
                    available_users.append(f"{user.get('first_name')} {user.get('last_name')}")
                else:
                    available_users.append(user.get('email', 'Unknown'))
            
            st.error(f"User '{selected_user}' not found in database")
            st.info(f"Available users (first 10): {', '.join(available_users)}")
            return generate_fallback_user_report(selected_user, start_date, end_date)
        
        # Convert dates to string format for database queries
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch all the analytics data
        daily_work = db_handler.get_user_daily_work_summary(user_id, start_date_str, end_date_str)
        client_distribution = db_handler.get_user_client_time_distribution(user_id, start_date_str, end_date_str)
        team_comparison = db_handler.get_user_team_comparison(user_id, start_date_str, end_date_str)
        period_summary = db_handler.get_user_period_summary(user_id, start_date_str, end_date_str)
        
        # Generate the markdown report
        return generate_user_analytics_markdown(
            user_display_name, 
            start_date, 
            end_date, 
            daily_work, 
            client_distribution, 
            team_comparison, 
            period_summary
        )
        
    except Exception as e:
        st.error(f"Error generating user analytics report: {str(e)}")
        return generate_fallback_user_report(selected_user, start_date, end_date)


def get_project_analytics_report(selected_client, start_date, end_date):
    """
    Generate project/client analytics report based on configuration
    
    Args:
        selected_client (str): The selected client option in format "Name (Jobcode ID: jobcode_id)"
        start_date (date): Start date for the report
        end_date (date): End date for the report
    
    Returns:
        str: Project/client analytics report in markdown format
    """
    try:
        # Get database handler
        db_handler = get_supabase_handler()
        
        # Get clients from database
        clients_data = db_handler.get_available_clients()
        
        # Find the client with jobcode ID matching
        jobcode_id, client_display_name = find_client_in_database(selected_client, clients_data)
        
        if not jobcode_id:
            # Show available clients for debugging
            available_clients = []
            for client in clients_data[:10]:  # Show first 10 clients
                client_name = client.get('name', 'Unknown Client')
                jobcode_id = client.get('id')
                if jobcode_id:
                    available_clients.append(f"{client_name} (Jobcode ID: {jobcode_id})")
            
            st.error(f"Client '{selected_client}' not found in database")
            st.info(f"Available clients (first 10): {', '.join(available_clients)}")
            return generate_fallback_client_report(selected_client, start_date, end_date)
        
        # Convert dates to string format for database queries
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch all the analytics data using jobcode_id
        overview_summary = db_handler.get_client_overview_summary(jobcode_id, start_date_str, end_date_str)
        user_allocation = db_handler.get_client_user_allocation(jobcode_id, start_date_str, end_date_str)
        client_comparison = db_handler.get_client_comparison(jobcode_id, start_date_str, end_date_str)
        weekly_summary = db_handler.get_client_weekly_summary(jobcode_id, start_date_str, end_date_str)
        
        # Check if we have any real data, if not use fallback
        has_data = (
            overview_summary.get('total_hours', 0) > 0 or
            len(user_allocation) > 0 or
            len(client_comparison) > 0 or
            len(weekly_summary) > 0
        )
        
        if not has_data:
            # Use fallback data when no real data is available
            return generate_fallback_client_report(client_display_name, start_date, end_date)
        
        # Generate the markdown report with real data
        return generate_client_analytics_markdown(
            client_display_name, 
            start_date, 
            end_date, 
            overview_summary, 
            user_allocation, 
            client_comparison, 
            weekly_summary
        )
        
    except Exception as e:
        st.error(f"Error generating client analytics report: {str(e)}")
        return generate_fallback_client_report(selected_client, start_date, end_date)


def get_time_analytics_report(start_date, end_date):
    """
    Generate time analytics report based on configuration
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
    
    Returns:
        str: Time analytics report in markdown format
    """
    try:
        # Get database handler
        db_handler = get_supabase_handler()
        
        # Convert dates to string format for database queries
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch all the time analytics data
        period_overview = db_handler.get_time_period_overview(start_date_str, end_date_str)
        daily_distribution = db_handler.get_time_daily_distribution(start_date_str, end_date_str)
        user_performance = db_handler.get_time_user_performance(start_date_str, end_date_str)
        client_activity = db_handler.get_time_client_activity(start_date_str, end_date_str)
        weekly_summary = db_handler.get_time_weekly_summary(start_date_str, end_date_str)
        session_analysis = db_handler.get_time_session_analysis(start_date_str, end_date_str)
        
        # Check if we have any real data, if not use fallback
        has_data = (
            period_overview.get('total_hours', 0) > 0 or
            len(daily_distribution) > 0 or
            len(user_performance) > 0 or
            len(client_activity) > 0 or
            len(weekly_summary) > 0 or
            len(session_analysis) > 0
        )
        
        if not has_data:
            # Use fallback data when no real data is available
            return generate_fallback_time_analytics_report(start_date, end_date)
        
        # Generate the markdown report with real data
        return generate_time_analytics_markdown(
            start_date, 
            end_date, 
            period_overview, 
            daily_distribution, 
            user_performance, 
            client_activity, 
            weekly_summary, 
            session_analysis
        )
        
    except Exception as e:
        st.error(f"Error generating time analytics report: {str(e)}")
        return generate_fallback_time_analytics_report(start_date, end_date)


def main():
    """
    Email Report Writer - Step 1: Report Type Selection & Date Logic
    """
    st.title("📧 Email Report Writer")
    st.subheader("Step 1: Report Configuration")
    
    # Report type selection
    st.markdown("### 📊 Select Report Type")
    report_type = st.selectbox(
        "Choose the type of report to generate:",
        ["User Report", "Client Report", "Time Report"],
        help="Different report types have different date selection logic"
    )
    
    # Date selection based on report type
    st.markdown("### 📅 Date Selection")
    
    if report_type == "User Report":
        st.info("📝 **User Report Logic**: Automatically uses start day to last day of entry")
        
        # User selection
        st.markdown("#### 👤 Select User")
        available_users = get_available_users()
        selected_user = st.selectbox(
            "Choose user for the report:",
            available_users,
            help="Select a specific user for the report"
        )
        
        # Get last entry date
        system_last_entry_date = get_last_entry_date()
        
        # Option to use system last entry date or custom date
        st.markdown("#### 📅 End Date Selection")
        use_system_date = st.checkbox(
            "Use system last entry date",
            value=True,
            help="Check to use the system's last entry date, uncheck to select custom end date"
        )
        
        # Default start date (you can adjust this logic)
        default_start = system_last_entry_date - timedelta(days=30)  # Last 30 days as default
        
        # Display the date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=default_start,
                help="Starting date for user report data collection"
            )
        
        with col2:
            if use_system_date:
                st.date_input(
                    "End Date (Last Entry)",
                    value=system_last_entry_date,
                    disabled=True,
                    help="Automatically set to system's last day of entry"
                )
                end_date = system_last_entry_date  # Use system last entry date
            else:
                end_date = st.date_input(
                    "End Date (Custom)",
                    value=system_last_entry_date,
                    help="Select custom end date for user report"
                )
        
        # Show different success messages based on date selection
        if use_system_date:
            st.success(f"✅ User Report: {selected_user} | {start_date} to {end_date} (system last entry)")
        else:
            st.success(f"✅ User Report: {selected_user} | {start_date} to {end_date} (custom end date)")
        
    elif report_type == "Client Report":
        st.info("📝 **Client Report Logic**: Manual start day and end day selection")
        
        # Client selection
        st.markdown("#### 🏢 Select Client")
        available_clients = get_available_clients()
        selected_client = st.selectbox(
            "Choose client for the report:",
            available_clients,
            help="Select a specific client for the report"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=30),
                help="Starting date for client report data collection"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                help="Ending date for client report data collection"
            )
        
        st.success(f"✅ Client Report: {selected_client} | {start_date} to {end_date}")
        
    elif report_type == "Time Report":
        st.info("📝 **Time Report Logic**: Manual start day and end day selection")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=7),  # Default to last week
                help="Starting date for time report data collection"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                help="Ending date for time report data collection"
            )
        
        st.success(f"✅ Time Report: {start_date} to {end_date}")
    
    # Display current configuration
    st.markdown("---")
    st.markdown("### 📋 Current Configuration")
    
    config_info = {
        "Report Type": report_type,
        "Start Date": start_date.strftime("%Y-%m-%d"),
        "End Date": end_date.strftime("%Y-%m-%d"),
        "Date Range": f"{(end_date - start_date).days} days"
    }
    
    # Add user/client selection to config based on report type
    if report_type == "User Report":
        config_info["Selected User"] = selected_user
    elif report_type == "Client Report":
        config_info["Selected Client"] = selected_client
    
    for key, value in config_info.items():
        st.write(f"**{key}:** {value}")
    
    # Quick validation
    if start_date > end_date:
        st.error("❌ Start date cannot be after end date!")
    elif start_date == end_date:
        st.warning("⚠️ Start and end dates are the same - this will be a single day report")
    else:
        st.success(f"✅ Valid date range: {(end_date - start_date).days} days of data")
    
    # Store configuration in session state for next steps
    if st.button("💾 Save Configuration", type="primary"):
        config_data = {
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'date_range_days': (end_date - start_date).days
        }
        
        # Add user/client selection based on report type
        if report_type == "User Report":
            config_data['selected_user'] = selected_user
            config_data['use_system_date'] = use_system_date
        elif report_type == "Client Report":
            config_data['selected_client'] = selected_client
        
        st.session_state['report_config'] = config_data
        st.success("✅ Configuration saved! Ready for next step.")
        
        # Show what's saved
        with st.expander("🔍 View Saved Configuration"):
            st.json(st.session_state['report_config'])
    
    # Trigger analytics functions based on saved configuration
    if 'report_config' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Generate Analytics Report")
        
        config = st.session_state['report_config']
        
        if st.button("🚀 Generate Report", type="primary"):
            st.markdown("#### 🔄 Processing Analytics...")
            
            # Determine which function to call based on report type
            if config['report_type'] == "User Report":
                st.info(f"Generating User Analytics Report for: {config.get('selected_user', 'Unknown')}")
                
                # Call user analytics function
                with st.spinner("Collecting user analytics data..."):
                    user_markdown = get_user_analytics_report(
                        selected_user=config.get('selected_user'),
                        start_date=config['start_date'],
                        end_date=config['end_date'],
                        use_system_date=config.get('use_system_date', True)
                    )
                    
                    # Store markdown in session state (following Home.py pattern)
                    st.session_state.generated_markdown = user_markdown
                    
                    # Display the generated report
                    st.markdown("### 📊 Generated User Analytics Report")
                    st.markdown(user_markdown)
                    
                    # Download buttons: Markdown and local PDF
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Markdown",
                            data=user_markdown,
                            file_name=f"user_analytics_report_{config.get('selected_user', 'unknown').replace(' ', '_')}_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            key=f"user_md_dl_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}"
                        )
                    with col_dl2:
                        try:
                            pdf_bytes = generate_pdf_from_markdown(
                                user_markdown,
                                title=f"User Analytics Report - {config.get('selected_user', 'Unknown')}"
                            )
                            st.download_button(
                                label="📄 Download PDF",
                                data=pdf_bytes,
                                file_name=f"user_analytics_report_{config.get('selected_user', 'unknown').replace(' ', '_')}_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key=f"user_pdf_dl_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}"
                            )
                        except Exception as pdf_err:
                            st.warning(f"PDF generation issue: {pdf_err}")
                
            elif config['report_type'] == "Client Report":
                st.info(f"Generating Project Analytics Report for: {config.get('selected_client', 'Unknown')}")
                
                # Call project analytics function
                with st.spinner("Collecting project analytics data..."):
                    project_markdown = get_project_analytics_report(
                        selected_client=config.get('selected_client'),
                        start_date=config['start_date'],
                        end_date=config['end_date']
                    )
                    
                    # Store markdown in session state (following Home.py pattern)
                    st.session_state.generated_markdown = project_markdown
                    
                    # Display the generated report
                    st.markdown("### 📊 Generated Client Analytics Report")
                    st.markdown(project_markdown)
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Markdown",
                            data=project_markdown,
                            file_name=f"client_analytics_report_{config.get('selected_client', 'unknown').replace(' ', '_')}_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            key=f"client_md_dl_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}"
                        )
                    with col_dl2:
                        try:
                            pdf_bytes = generate_pdf_from_markdown(
                                project_markdown,
                                title=f"Client Analytics Report - {config.get('selected_client', 'Unknown')}"
                            )
                            st.download_button(
                                label="📄 Download PDF",
                                data=pdf_bytes,
                                file_name=f"client_analytics_report_{config.get('selected_client', 'unknown').replace(' ', '_')}_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key=f"client_pdf_dl_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}"
                            )
                        except Exception as pdf_err:
                            st.warning(f"PDF generation issue: {pdf_err}")
                
            elif config['report_type'] == "Time Report":
                st.info("Generating Time Analytics Report")
                
                # Call time analytics function
                with st.spinner("Collecting time analytics data..."):
                    time_markdown = get_time_analytics_report(
                        start_date=config['start_date'],
                        end_date=config['end_date']
                    )
                    
                    # Store markdown in session state (following Home.py pattern)
                    st.session_state.generated_markdown = time_markdown
                    
                    # Display the generated report
                    st.markdown("### 📊 Generated Time Analytics Report")
                    st.markdown(time_markdown)
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Markdown",
                            data=time_markdown,
                            file_name=f"time_analytics_report_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            key=f"time_md_dl_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}"
                        )
                    with col_dl2:
                        try:
                            pdf_bytes = generate_pdf_from_markdown(
                                time_markdown,
                                title=f"Time Analytics Report - {config['start_date'].strftime('%Y-%m-%d')} to {config['end_date'].strftime('%Y-%m-%d')}"
                            )
                            st.download_button(
                                label="📄 Download PDF",
                                data=pdf_bytes,
                                file_name=f"time_analytics_report_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key=f"time_pdf_dl_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}"
                            )
                        except Exception as pdf_err:
                            st.warning(f"PDF generation issue: {pdf_err}")
            
            st.success("✅ Analytics functions triggered successfully!")

    # Persistent download buttons whenever a report exists
    if st.session_state.get('generated_markdown') and 'report_config' in st.session_state:
        st.markdown("---")
        st.markdown("### 📥 Download Your Report")
        cfg = st.session_state['report_config']
        md_content = st.session_state['generated_markdown']

        # Derive filenames and titles based on report type
        if cfg.get('report_type') == 'User Report':
            base_name = f"user_analytics_report_{cfg.get('selected_user', 'unknown').replace(' ', '_')}_{cfg['start_date'].strftime('%Y%m%d')}_{cfg['end_date'].strftime('%Y%m%d')}"
            pdf_title = f"User Analytics Report - {cfg.get('selected_user', 'Unknown')}"
        elif cfg.get('report_type') == 'Client Report':
            base_name = f"client_analytics_report_{cfg.get('selected_client', 'unknown').replace(' ', '_')}_{cfg['start_date'].strftime('%Y%m%d')}_{cfg['end_date'].strftime('%Y%m%d')}"
            pdf_title = f"Client Analytics Report - {cfg.get('selected_client', 'Unknown')}"
        else:
            base_name = f"time_analytics_report_{cfg['start_date'].strftime('%Y%m%d')}_{cfg['end_date'].strftime('%Y%m%d')}"
            pdf_title = f"Time Analytics Report - {cfg['start_date'].strftime('%Y-%m-%d')} to {cfg['end_date'].strftime('%Y-%m-%d')}"

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.download_button(
                label="📄 Download Markdown",
                data=md_content,
                file_name=f"{base_name}.md",
                mime="text/markdown",
                key=f"persist_md_{base_name}"
            )
        with col_p2:
            try:
                pdf_bytes = generate_pdf_from_markdown(md_content, title=pdf_title)
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{base_name}.pdf",
                    mime="application/pdf",
                    key=f"persist_pdf_{base_name}"
                )
            except Exception as e:
                st.warning(f"PDF generation issue: {e}")

    # AI Report Generation Section (following Home.py pattern)
    if st.session_state.generated_markdown and 'report_config' in st.session_state and client.is_configured():
        st.markdown("---")
        st.markdown("### 🤖 AI Enhanced PDF Report Generation")
        
        # Add reset button for debugging
        if st.button("🔄 Reset AI Status", help="Reset AI processing status to ready"):
            st.session_state.ai_processing_status = 'ready'
            st.session_state.proceed_with_ai_generation = False
            st.session_state.ai_assistant_id = None
            st.session_state.ai_thread_id = None
            st.session_state.ai_chat_messages = []
            st.session_state.pdf_generated = False
            st.rerun()
        
        config = st.session_state['report_config']
        
        # Always show the AI button - simplified approach
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🤖 Generate AI Enhanced PDF Report", type="primary", use_container_width=True):
            # Reset any previous state
                st.session_state.ai_processing_status = 'processing'
                st.session_state.proceed_with_ai_generation = True
                st.session_state.ai_assistant_id = None
                st.session_state.ai_thread_id = None
                st.session_state.ai_chat_messages = []
                st.session_state.pdf_generated = False
                st.rerun()
        
        with col2:
            st.info("💡 AI Report will create a comprehensive PDF with visualizations and insights")
        
        # Show current status for debugging
        st.write(f"🔍 Current AI Status: {st.session_state.ai_processing_status}")
        
        # Processing AI Report (following Home.py pattern)
        if st.session_state.ai_processing_status == 'processing':
            if st.session_state.proceed_with_ai_generation:
                
                # Create report name based on type
                if config['report_type'] == "User Report":
                    report_name = f"User Analytics Report - {config.get('selected_user', 'Unknown')}"
                elif config['report_type'] == "Client Report":
                    report_name = f"Client Analytics Report - {config.get('selected_client', 'Unknown')}"
                else:
                    report_name = f"Time Analytics Report - {config['start_date'].strftime('%Y-%m-%d')} to {config['end_date'].strftime('%Y-%m-%d')}"
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Create AI Assistant
                    progress_bar.progress(20)
                    status_text.text('🤖 Creating AI Assistant for comprehensive PDF generation...')
                    
                    assistant_id, thread_id, file_id, status_msg = create_ai_report_assistant(
                        st.session_state.generated_markdown, 
                        config['report_type'], 
                        report_name
                    )
                    
                    if not assistant_id:
                        st.error(f"❌ AI Assistant Creation Failed: {status_msg}")
                        st.session_state.ai_processing_status = 'error'
                        st.session_state.proceed_with_ai_generation = False
                        st.stop()
                    
                    # Step 2: Create AI Assistant (no immediate PDF generation)
                    progress_bar.progress(60)
                    status_text.text('🤖 Creating AI Assistant for PDF generation...')
                    
                    assistant_id, thread_id, file_id, status_msg = create_ai_report_assistant(
                        st.session_state.generated_markdown, 
                        config['report_type'], 
                        report_name
                    )
                    
                    if not assistant_id:
                        st.error(f"❌ AI Assistant Creation Failed: {status_msg}")
                        st.session_state.ai_processing_status = 'error'
                        st.session_state.proceed_with_ai_generation = False
                        st.stop()
                    
                    # Step 3: Complete processing (no immediate PDF generation - following Home.py pattern)
                    progress_bar.progress(100)
                    status_text.text('✅ AI Assistant ready for PDF generation!')
                    
                    # Store results (following Home.py pattern)
                    st.session_state.ai_assistant_id = assistant_id
                    st.session_state.ai_thread_id = thread_id
                    st.session_state.ai_chat_messages = []  # Start with empty chat
                    st.session_state.pdf_generated = False  # Will be set to True after first PDF generation
                    
                    # Create results for display (following Home.py pattern)
                    st.session_state.report_results = [
                        {
                            "type": "AI Report Assistant",
                            "filename": f"Assistant ID: {assistant_id}",
                            "icon": "🤖",
                            "description": "Dedicated AI assistant ready for PDF generation and report questions"
                        }
                    ]
                    
                    # Clear processing flags (following Home.py pattern)
                    st.session_state.proceed_with_ai_generation = False
                    st.session_state.ai_processing_status = 'complete'
                    st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ AI Processing Failed: {str(e)}")
                    st.session_state.ai_processing_status = 'error'
                    st.session_state.proceed_with_ai_generation = False
                    st.stop()
        
        # Show completed AI report results (following Home.py pattern)
        if st.session_state.ai_processing_status == 'complete':
            st.success("🎉 AI Assistant Created Successfully!")
            
            # Display results
            if st.session_state.report_results:
                for result in st.session_state.report_results:
                    with st.container():
                        st.markdown(f"""
                        <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 4px solid #28a745;">
                            <h4>{result['icon']} {result['type']}</h4>
                            <p><strong>Output:</strong> {result['filename']}</p>
                            <p><em>{result.get('description', '')}</em></p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Auto-generate AI-enhanced PDF once after assistant setup
            if st.session_state.ai_pdf_bytes is None:
                st.info("🤖 Generating AI‑enhanced PDF content...")
                try:
                    enhanced_text = client.analyze_report_data(
                        report_data=st.session_state.generated_markdown,
                        report_type=config['report_type'],
                        user_name=config.get('selected_user', config.get('selected_client', 'User'))
                    )
                    st.session_state.ai_pdf_bytes = generate_pdf_from_markdown(
                        enhanced_text or st.session_state.generated_markdown,
                        title=f"{config['report_type']} - AI Enhanced"
                    )
                    # Persist to disk so the file can be reused/sent
                    base = config.get('report_type', 'Report').replace(' ', '_').lower()
                    ai_pdf_name = f"{base}_ai_enhanced.pdf"
                    st.session_state.ai_pdf_path = save_pdf_to_disk(st.session_state.ai_pdf_bytes, ai_pdf_name)
                    st.success("✅ AI‑enhanced PDF ready to download.")
                except Exception as ai_pdf_err:
                    st.warning(f"AI PDF generation issue: {ai_pdf_err}")

    # AI Assistant Chat Interface (appears after PDF generation - following Home.py pattern)
    if client.is_configured() and st.session_state.ai_assistant_id and st.session_state.ai_thread_id and st.session_state.ai_processing_status == 'complete':
        st.markdown("---")
        st.markdown("### 🤖 AI Report Assistant Chat")
        
        # Display assistant info (following Home.py pattern)
        config = st.session_state.get('report_config', {})
        report_type = config.get('report_type', 'Unknown')
        st.write(f"**Report Type:** {report_type}")
        st.write(f"**Assistant ID:** `{st.session_state.ai_assistant_id}`")
        st.write(f"**Thread ID:** `{st.session_state.ai_thread_id}`")
        st.info("💡 This assistant can create visualizations, modify reports, and answer questions about your data!")
        
        # Display chat messages (following Home.py pattern)
        if st.session_state.ai_chat_messages:
            st.markdown("#### 💬 Chat History")
            chat_container = st.container()
            with chat_container:
                for i, message in enumerate(st.session_state.ai_chat_messages):
                    if message['role'] == 'user':
                        st.markdown(f"**You:** {message['content']}")
                    else:
                        st.markdown(f"**AI Assistant:** {message['content']}")
                        
                        # Display any images generated by Code Interpreter (following Home.py pattern)
                        if message.get('images'):
                            for image_file_id in message['images']:
                                try:
                                    # Download and display the image
                                    # Perplexity doesn't support file downloads
                                    st.info("Image display not supported with Perplexity")
                                except Exception as img_error:
                                    st.error(f"Could not display image {image_file_id}: {str(img_error)}")
                        
                        # Display download buttons for any files generated (following Home.py pattern)
                        if message.get('files'):
                            st.markdown("**� Generated Files:**")
                            for file_info in message['files']:
                                try:
                                    file_id = file_info['file_id']
                                    # Get file info from OpenAI
                                    # Perplexity doesn't support file downloads
                                    st.info("File download not supported with Perplexity")
                                    
                                except Exception as file_error:
                                    st.error(f"Could not prepare download for file {file_info}: {str(file_error)}")
                    
                    st.markdown("---")
        
        # AI PDF download and email send (optional)
        st.markdown("#### 📥 Download AI‑Enhanced PDF")
        if st.session_state.ai_pdf_bytes:
            cfg = st.session_state.get('report_config', {})
            base = cfg.get('report_type', 'Report').replace(' ', '_').lower()
            ai_pdf_name = f"{base}_ai_enhanced.pdf"
            st.download_button(
                label="📄 Download AI Enhanced PDF",
                data=st.session_state.ai_pdf_bytes,
                file_name=ai_pdf_name,
                mime="application/pdf",
                key=f"ai_pdf_dl_{ai_pdf_name}"
            )
            if st.session_state.get('ai_pdf_path'):
                st.caption(f"Saved to: {st.session_state.ai_pdf_path}")
            with st.expander("✉️ Email this PDF"):
                to_email = st.text_input("Recipient email", key="ai_pdf_email")
                if st.button("Send Email", key="ai_pdf_send_btn"):
                    try:
                        send_pdf_via_email(
                            recipient_email=to_email,
                            subject="AI Enhanced Analytics Report",
                            body="Please find the attached AI-enhanced analytics report.",
                            pdf_bytes=st.session_state.ai_pdf_bytes,
                            filename=ai_pdf_name
                        )
                        st.success("Email sent successfully.")
                    except Exception as mail_err:
                        st.error(f"Email send failed: {mail_err}")

        # Chat input (following Home.py pattern)
        st.markdown("#### ✍️ Ask about your report or generate PDF")
        
        # If no PDF generated yet, show auto-generate button
        if not st.session_state.pdf_generated:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎯 Generate Initial PDF Report", type="primary", use_container_width=True):
                    config = st.session_state['report_config']
                    initial_message = f"Please analyze the {config['report_type'].lower()} data provided and create a comprehensive, professional PDF report. Include executive summary, key insights, data visualizations, detailed analysis, and recommendations. Make it business-ready and visually appealing."
                    
                    # Add to chat and process immediately
                    st.session_state.ai_chat_messages.append({
                        'role': 'user',
                        'content': initial_message
                    })
                    st.rerun()
            with col2:
                st.info("👆 Generate your first PDF report")
        
        user_input = st.text_input(
            "Ask questions about your report, request modifications, or get insights:",
            placeholder="e.g., Can you add more charts? What are the key takeaways? Can you create an executive summary?",
            key="ai_chat_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Send", type="primary", use_container_width=True):
                if user_input.strip():
                    # Add user message to chat
                    st.session_state.ai_chat_messages.append({
                        'role': 'user',
                        'content': user_input
                    })
                    st.rerun()
        
        with col2:
            st.info("💡 You can ask for report modifications, additional analysis, or clarifications")
        
        # Process any unprocessed user messages
        for i, message in enumerate(st.session_state.ai_chat_messages):
            if message['role'] == 'user' and not message.get('processed', False):
                with st.spinner(f"Assistant is working on: {message['content'][:50]}..."):
                    try:
                        # Send message to Perplexity AI
                        response = client.chat_with_data(
                            user_message=message['content'],
                            context_data=st.session_state.generated_markdown
                        )
                        
                        # Store the response
                        message_data = {
                            'role': 'assistant', 
                            'content': response,
                            'images': None,
                            'files': None
                        }
                        
                        st.session_state.ai_chat_messages.append(message_data)
                        
                        # Mark user message as processed
                        st.session_state.ai_chat_messages[i]['processed'] = True
                        
                        st.rerun()
                            
                    except Exception as e:
                        st.error(f"Chat error: {str(e)}")
                        st.session_state.ai_chat_messages[i]['processed'] = True


if __name__ == "__main__":
    main()