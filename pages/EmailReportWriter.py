import streamlit as st

# Basic imports
from datetime import datetime, timedelta

def get_last_entry_date():
    """
    Get the last date of entry from the system
    For now, this returns a mock date - will be replaced with real data later
    """
    # Mock implementation - replace with actual data retrieval
    return datetime.now().date() - timedelta(days=1)

def get_available_users():
    """
    Get list of available users from the system
    For now, this returns mock data - will be replaced with real data later
    """
    # Mock implementation - replace with actual user data retrieval
    return [
        "John Smith", 
        "Jane Doe", 
        "Mike Johnson", 
        "Sarah Wilson", 
        "Tom Brown",
        "Lisa Chen",
        "David Rodriguez"
    ]

def get_available_clients():
    """
    Get list of available clients from the system
    For now, this returns mock data - will be replaced with real data later
    """
    # Mock implementation - replace with actual client data retrieval
    return [
        "Client A - TechCorp",
        "Client B - BuildCo",
        "Client C - DesignStudio", 
        "Client D - ManufacturingInc",
        "Client E - RetailChain",
        "Client F - HealthcarePlus",
        "Client G - EducationGroup"
    ]

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
    # Data Source: TSheet format (user, client, task, startdatetime, enddatetime)
    # Focus on CLIENT-LEVEL analytics since many clients don't have defined tasks
    # 
    # SIMPLIFIED USER ANALYTICS TABLES (what we can actually calculate):
    # 
    # 1. **Daily Work Summary**
    # | Date | Total Hours | Clients Worked | Sessions | Longest Session |
    # - Total Hours = sum of (enddatetime - startdatetime) for each day
    # - Clients Worked = count of unique clients per day
    # - Sessions = count of time entries per day
    # - Longest Session = max(enddatetime - startdatetime) per day
    #
    # 2. **Client Time Distribution**
    # | Client | Total Hours | Sessions | Avg Session | First Date | Last Date |
    # - Total Hours = sum of all session durations for each client
    # - Sessions = count of entries for each client
    # - Avg Session = Total Hours / Sessions
    # - First/Last Date = min/max dates worked for each client
    #
    # 3. **User vs DDMAC Team Comparison**
    # | Metric | This User | DDMAC Average | Rank | Percentile |
    # - Total Hours in Period = sum of all session durations
    # - Average Hours per Day = Total Hours / Working Days  
    # - Working Days = count of unique dates with entries
    # - Clients Served = count of unique clients
    # - Average Session Length = Total Hours / Total Sessions
    # - Longest Single Session = max(enddatetime - startdatetime)
    # 
    # Calculations:
    # - DDMAC Average = calculate same metric for all other users, then average
    # - Rank = position when all users sorted by metric (1 = highest)
    # - Percentile = (rank / total_users) * 100
    #
    #
    # 6. **Period Summary**
    # | Metric | Value |
    # - Total Hours in Period = sum of all session durations
    # - Total Working Days = count of unique dates
    # - Average Hours per Day = Total Hours / Working Days
    # - Clients Served = count of unique clients
    # - Total Sessions = count of all entries
    # - Average Session Length = Total Hours / Total Sessions
    #
    # TODO: Implement TSheet data fetching for selected_user
    # TODO: Fetch TSheet data for ALL users for comparison calculations
    # TODO: Filter data by start_date to end_date
    # TODO: Calculate hours from datetime differences
    # TODO: Group by client and date for analysis
    # TODO: Calculate DDMAC team averages and rankings
    # TODO: Generate markdown tables with real data
    pass

def get_project_analytics_report(selected_client, start_date, end_date):
    """
    Generate project/client analytics report based on configuration
    
    Args:
        selected_client (str): The selected client name
        start_date (date): Start date for the report
        end_date (date): End date for the report
    
    Returns:
        str: Project/client analytics report in markdown format
    """
    # Data Source: TSheet format (user, client, task, startdatetime, enddatetime)
    # Focus on what we can calculate for a specific client
    # 
    # SIMPLIFIED CLIENT ANALYTICS TABLES (what we can actually calculate):
    # 
    # 1. **Client Overview Summary**
    # | Metric | Value |
    # - Total Hours Logged
    # - Number of Users Assigned = count of unique users for this client
    # - Number of Tasks/Sessions = count of entries for this client
    # - Average Hours Per Day = Total Hours / Working Days
    # - Working Days = count of unique dates for this client
    # - First Date Worked = min(date) for this client
    # - Last Date Worked = max(date) for this client
    #
    # 2. **User Allocation Table**
    # | User | Total Hours | Percentage | Sessions | Avg Session | First Date | Last Date |
    # - Total Hours = sum of session durations for each user on this client
    # - Percentage = (User Hours / Total Client Hours) * 100
    # - Sessions = count of entries per user for this client
    # - Avg Session = Total Hours / Sessions
    # - First/Last Date = min/max dates each user worked on this client
    #
    #
    # 4. **Client vs Other Clients Comparison**
    # | Metric | This Client | DDMAC Average | Rank | Percentile |
    # - Total Hours = sum of all session durations
    # - Users Assigned = count of unique users
    # - Average Session Length = Total Hours / Total Sessions
    # - Working Days = count of unique dates
    # - Hours per Week = Total Hours / (Working Days / 7)
    # 
    # Calculations:
    # - DDMAC Average = calculate same metric for all other clients, then average
    # - Rank = position when all clients sorted by metric
    # - Percentile = (rank / total_clients) * 100
    #
    # 5. **Weekly Summary**
    # | Week | Total Hours | Users Active | Sessions | Average Session |
    # Weekly breakdown of client activity
    #
    # TODO: Implement TSheet data fetching for selected_client
    # TODO: Fetch TSheet data for ALL clients for comparison calculations
    # TODO: Filter data by start_date to end_date
    # TODO: Calculate hours from datetime differences
    # TODO: Group by user, date, and week for analysis
    # TODO: Calculate client ranking vs other DDMAC clients
    # TODO: Generate markdown tables with real data
    pass

def get_time_analytics_report(start_date, end_date):
    """
    Generate time analytics report based on configuration
    
    Args:
        start_date (date): Start date for the report
        end_date (date): End date for the report
    
    Returns:
        str: Time analytics report in markdown format
    """
    # Data Source: TSheet format (user, client, task, startdatetime, enddatetime)
    # Focus on COMPANY-WIDE time analytics for the specified period
    # 
    # SIMPLIFIED TIME ANALYTICS TABLES (what we can actually calculate):
    # 
    # 1. **Period Overview Summary**
    # | Metric | Value |
    # - Total Hours Logged = sum of (enddatetime - startdatetime) for all entries
    # - Total Users Active = count of unique users in period
    # - Total Clients Served = count of unique clients in period
    # - Total Sessions = count of all entries in period
    # - Working Days = count of unique dates in period
    # - Average Daily Hours = Total Hours / Working Days
    # - Average Session Length = Total Hours / Total Sessions
    #
    # 2. **Daily Time Distribution**
    # | Date | Total Hours | Users Active | Clients Active | Sessions | Longest Session |
    # - Total Hours = sum of session durations per day
    # - Users Active = count of unique users per day
    # - Clients Active = count of unique clients per day
    # - Sessions = count of entries per day
    # - Longest Session = max(enddatetime - startdatetime) per day
    #
    # 3. **User Performance Ranking**
    # | Rank | User | Total Hours | Working Days | Avg Hours/Day | Clients Served | Sessions |
    # - Total Hours = sum of session durations per user
    # - Working Days = count of unique dates per user
    # - Avg Hours/Day = Total Hours / Working Days
    # - Clients Served = count of unique clients per user
    # - Sessions = count of entries per user
    #
    # 4. **Client Activity Summary**
    # | Client | Total Hours | Users Assigned | Sessions | Avg Session | Working Days |
    # - Total Hours = sum of session durations per client
    # - Users Assigned = count of unique users per client
    # - Sessions = count of entries per client
    # - Avg Session = Total Hours / Sessions
    # - Working Days = count of unique dates per client
    #
    # 5. **Weekly Summary**
    # | Week | Total Hours | Daily Average | Users | Clients | Sessions |
    # Weekly aggregation of company activity
    #
    # 6. **Session Length Analysis**
    # | Session Type | Count | Total Hours | Percentage |
    # - Short Sessions (< 2 hours) = count and sum where duration < 2
    # - Medium Sessions (2-4 hours) = count and sum where 2 <= duration < 4
    # - Long Sessions (4+ hours) = count and sum where duration >= 4
    # - Percentage = (Type Hours / Total Hours) * 100
    # 
    #
    # TODO: Implement TSheet data fetching for ALL users and clients
    # TODO: Filter data by start_date to end_date
    # TODO: Calculate hours from datetime differences
    # TODO: Group by user, client, date, and week for analysis
    # TODO: Calculate session length categories
    # TODO: Generate markdown tables with real data
    pass

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
                    # TODO: Display user_markdown
                    st.warning("⚠️ User analytics function not yet implemented")
                
            elif config['report_type'] == "Client Report":
                st.info(f"Generating Project Analytics Report for: {config.get('selected_client', 'Unknown')}")
                
                # Call project analytics function
                with st.spinner("Collecting project analytics data..."):
                    project_markdown = get_project_analytics_report(
                        selected_client=config.get('selected_client'),
                        start_date=config['start_date'],
                        end_date=config['end_date']
                    )
                    # TODO: Display project_markdown
                    st.warning("⚠️ Project analytics function not yet implemented")
                
            elif config['report_type'] == "Time Report":
                st.info("Generating Time Analytics Report")
                
                # Call time analytics function
                with st.spinner("Collecting time analytics data..."):
                    time_markdown = get_time_analytics_report(
                        start_date=config['start_date'],
                        end_date=config['end_date']
                    )
                    # TODO: Display time_markdown
                    st.warning("⚠️ Time analytics function not yet implemented")
            
            st.success("✅ Analytics functions triggered successfully!")
            st.info("💡 **Next Steps**: Implement the analytics functions to return markdown content")

if __name__ == "__main__":
    main()
