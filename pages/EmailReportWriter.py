import streamlit as st
import os
import tempfile
from openai import OpenAI

# Basic imports
from datetime import datetime, timedelta

# Import database handler
from utils.supabase_queries import get_supabase_handler

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def create_ai_report_assistant(markdown_content, report_type, report_name):
    """Create a dedicated Assistant for generating comprehensive PDF reports (following Home.py pattern exactly)"""
    try:
        # Create a markdown file for the assistant
        temp_path = os.path.join(tempfile.gettempdir(), f"{report_name.replace(' ', '_')}_report.md")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Upload markdown file to OpenAI
        with open(temp_path, "rb") as f:
            file_obj = client.files.create(
                file=f,
                purpose='assistants'
            )

        # Clean up temp file
        os.remove(temp_path)
        
        # Create Assistant with simpler description (following Home.py pattern)
        assistant_name = f"DDMac Bot - {report_name} Analyzer"
        assistant_description = f"""DDMac Bot expert for {report_type.lower()} analytics and PDF generation.

Report: {report_name} | Type: {report_type}

Analyzes report data and creates professional PDFs with visualizations. Uses code interpreter for calculations and document generation."""

        assistant = client.beta.assistants.create(
            name=assistant_name,
            description=assistant_description,
            model="gpt-4o",
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter": {
                    "file_ids": [file_obj.id]
                }
            }
        )
        
        # Create a thread
        thread = client.beta.threads.create()
        
        return assistant.id, thread.id, file_obj.id, "AI Report Assistant created successfully"
        
    except Exception as e:
        return None, None, None, f"Error creating AI assistant: {str(e)}"

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
                    
                    # Add download button for the report
                    st.download_button(
                        label="📥 Download Report as Markdown",
                        data=user_markdown,
                        file_name=f"user_analytics_report_{config.get('selected_user', 'unknown').replace(' ', '_')}_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                
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
                    
                    # Add download button for the report
                    st.download_button(
                        label="📥 Download Report as Markdown",
                        data=project_markdown,
                        file_name=f"client_analytics_report_{config.get('selected_client', 'unknown').replace(' ', '_')}_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                
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
                    
                    # Add download button for the report
                    st.download_button(
                        label="📥 Download Report as Markdown",
                        data=time_markdown,
                        file_name=f"time_analytics_report_{config['start_date'].strftime('%Y%m%d')}_{config['end_date'].strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
            
            st.success("✅ Analytics functions triggered successfully!")

    # AI Report Generation Section (following Home.py pattern)
    if st.session_state.generated_markdown and 'report_config' in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 AI Enhanced PDF Report Generation")
        
        config = st.session_state['report_config']
        
        # Check if we need to show the AI button or if processing is already started
        if st.session_state.ai_processing_status == 'ready':
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🤖 Generate AI Enhanced PDF Report", type="primary", use_container_width=True):
                    st.session_state.proceed_with_ai_generation = True
                    st.session_state.ai_processing_status = 'processing'
                    st.rerun()
            
            with col2:
                st.info("💡 AI Report will create a comprehensive PDF with visualizations and insights")
        
        # Processing AI Report (following Home.py pattern)
        elif st.session_state.ai_processing_status == 'processing':
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
        elif st.session_state.ai_processing_status == 'complete':
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
            
            # Auto-trigger initial PDF generation if not done yet
            if not st.session_state.pdf_generated and not st.session_state.ai_chat_messages:
                st.info("🤖 Use the 'Generate Initial PDF Report' button below to create your first comprehensive PDF report.")
                st.info("💡 Then you can chat with the assistant to modify or enhance the report.")

    # AI Assistant Chat Interface (appears after PDF generation - following Home.py pattern)
    if st.session_state.ai_assistant_id and st.session_state.ai_thread_id and st.session_state.ai_processing_status == 'complete':
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
                                    image_data = client.files.content(image_file_id)
                                    image_bytes = image_data.read()
                                    st.image(image_bytes, caption=f"Generated visualization", use_column_width=True)
                                except Exception as img_error:
                                    st.error(f"Could not display image {image_file_id}: {str(img_error)}")
                        
                        # Display download buttons for any files generated (following Home.py pattern)
                        if message.get('files'):
                            st.markdown("**� Generated Files:**")
                            for file_info in message['files']:
                                try:
                                    file_id = file_info['file_id']
                                    # Get file info from OpenAI
                                    file_obj = client.files.retrieve(file_id)
                                    filename = file_obj.filename or f"generated_report_{i}.pdf"
                                    
                                    # Download file content
                                    file_data = client.files.content(file_id)
                                    file_bytes = file_data.read()
                                    
                                    # Create download button
                                    st.download_button(
                                        label=f"📥 Download {filename}",
                                        data=file_bytes,
                                        file_name=filename,
                                        mime="application/pdf" if filename.endswith('.pdf') else "application/octet-stream",
                                        key=f"download_file_{file_id}_{i}"
                                    )
                                    
                                except Exception as file_error:
                                    st.error(f"Could not prepare download for file {file_info}: {str(file_error)}")
                    
                    st.markdown("---")
        
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
                        # Create message in the thread (exactly like Home.py)
                        client.beta.threads.messages.create(
                            thread_id=st.session_state.ai_thread_id,
                            role="user",
                            content=message['content']
                        )
                        
                        # Run the assistant (exactly like Home.py)
                        run = client.beta.threads.runs.create(
                            thread_id=st.session_state.ai_thread_id,
                            assistant_id=st.session_state.ai_assistant_id
                        )
                        
                        # Wait for completion (with longer timeout for PDF generation)
                        import time
                        wait_count = 0
                        max_wait = 120  # 2 minutes
                        while run.status in ['queued', 'in_progress'] and wait_count < max_wait:
                            time.sleep(2)
                            run = client.beta.threads.runs.retrieve(
                                thread_id=st.session_state.ai_thread_id, 
                                run_id=run.id
                            )
                            wait_count += 1
                        
                        if run.status == 'completed': 
                            # Get the assistant's response (exactly like Home.py)
                            messages = client.beta.threads.messages.list(thread_id=st.session_state.ai_thread_id)
                            
                            # Process the message content (exactly like Home.py)
                            assistant_content = ""
                            images = []
                            files = []
                            
                            for content_block in messages.data[0].content:
                                if hasattr(content_block, 'text'):
                                    text_value = content_block.text.value
                                    assistant_content += text_value + "\n"
                                    
                                    if hasattr(content_block.text, 'annotations'):
                                        for annotation in content_block.text.annotations:
                                            if hasattr(annotation, 'file_path'):
                                                file_id = annotation.file_path.file_id
                                                files.append({
                                                    'file_id': file_id,
                                                    'filename': f"generated_report.pdf"
                                                })
                                                
                                elif hasattr(content_block, 'image_file'):
                                    file_id = content_block.image_file.file_id
                                    images.append(file_id)
                                    assistant_content += f"[Generated Image: file-{file_id}]\n"
                            
                            # Store the response (exactly like Home.py)
                            message_data = {
                                'role': 'assistant', 
                                'content': assistant_content.strip(),
                                'images': images if images else None,
                                'files': files if files else None
                            }
                            
                            st.session_state.ai_chat_messages.append(message_data)
                            
                            # Mark user message as processed
                            st.session_state.ai_chat_messages[i]['processed'] = True
                            
                            # Mark PDF as generated if files were created
                            if files:
                                st.session_state.pdf_generated = True
                            
                            st.rerun()
                        else:
                            st.error(f"Assistant run failed with status: {run.status}")
                            st.session_state.ai_chat_messages[i]['processed'] = True
                            
                    except Exception as e:
                        st.error(f"Chat error: {str(e)}")
                        st.session_state.ai_chat_messages[i]['processed'] = True


if __name__ == "__main__":
    main()