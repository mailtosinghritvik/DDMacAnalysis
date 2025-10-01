"""
Report Generation Utilities

This module contains utility functions for generating markdown reports,
helper functions for data retrieval, and fallback report generators.

These functions are used by EmailReportWriter.py to handle the formatting
and generation of various analytics reports.
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.supabase_queries import get_supabase_handler


def get_last_entry_date():
    """
    Get the last date of entry from the system
    For now, this returns a mock date - will be replaced with real data later
    """
    # Mock implementation - replace with actual data retrieval
    return datetime.now().date() - timedelta(days=1)


def get_available_users():
    """
    Get list of available users from the database
    Returns a list of user IDs with names for dropdown selection
    """
    try:
        # Get database handler
        db_handler = get_supabase_handler()
        
        # Get users from database
        users_data = db_handler.get_available_users()
        
        # Extract user IDs with names for the dropdown
        user_options = []
        for user in users_data:
            user_id = user.get('id')
            if not user_id:
                continue
                
            # Create display name
            if user.get('display_name') and user.get('display_name').strip():
                display_name = user['display_name']
            elif user.get('first_name') and user.get('last_name'):
                display_name = f"{user['first_name']} {user['last_name']}"
            else:
                display_name = user.get('email', 'Unknown User')
            
            # Format as "Display Name (ID: user_id)"
            user_options.append(f"{display_name} (ID: {user_id})")
        
        return user_options
        
    except Exception as e:
        st.error(f"Error retrieving users: {str(e)}")
        # Return fallback data
        return [
            "John Smith (ID: 1)", 
            "Jane Doe (ID: 2)", 
            "Mike Johnson (ID: 3)", 
            "Sarah Wilson (ID: 4)", 
            "Tom Brown (ID: 5)",
            "Lisa Chen (ID: 6)",
            "David Rodriguez (ID: 7)"
        ]


def get_available_clients():
    """
    Get list of available clients from the database
    Returns a list of client names with jobcode IDs for dropdown selection
    """
    try:
        # Get database handler
        db_handler = get_supabase_handler()
        
        # Get clients from database
        clients_data = db_handler.get_available_clients()
        
        # Extract client names with jobcode IDs for the dropdown
        client_options = []
        for client in clients_data:
            jobcode_id = client.get('id')
            if not jobcode_id:
                continue
                
            # Get client name
            client_name = client.get('name', 'Unknown Client')
            
            # Format as "Client Name (Jobcode ID: jobcode_id)"
            client_options.append(f"{client_name} (Jobcode ID: {jobcode_id})")
        
        return client_options
        
    except Exception as e:
        st.error(f"Error retrieving clients: {str(e)}")
        # Return fallback data
        return [
            "Client A - TechCorp (Jobcode ID: 1)",
            "Client B - BuildCo (Jobcode ID: 2)",
            "Client C - DesignStudio (Jobcode ID: 3)", 
            "Client D - ManufacturingInc (Jobcode ID: 4)",
            "Client E - RetailChain (Jobcode ID: 5)",
            "Client F - HealthcarePlus (Jobcode ID: 6)",
            "Client G - EducationGroup (Jobcode ID: 7)"
        ]


def find_user_in_database(selected_user_option, users_data):
    """
    Find a user in the database by extracting ID from selected option
    
    Args:
        selected_user_option (str): The selected user option in format "Name (ID: user_id)"
        users_data (list): List of user data from database
    
    Returns:
        tuple: (user_id, user_display_name) or (None, None) if not found
    """
    if not users_data or not selected_user_option:
        return None, None
    
    # Extract user ID from the selected option
    # Format: "Display Name (ID: user_id)"
    if "(ID:" in selected_user_option and ")" in selected_user_option:
        try:
            # Extract the ID part
            id_part = selected_user_option.split("(ID:")[-1].split(")")[0].strip()
            user_id = int(id_part)
            
            # Find the user with this ID
            for user in users_data:
                if user.get('id') == user_id:
                    # Create display name
                    if user.get('display_name') and user.get('display_name').strip():
                        display_name = user['display_name']
                    elif user.get('first_name') and user.get('last_name'):
                        display_name = f"{user['first_name']} {user['last_name']}"
                    else:
                        display_name = user.get('email', 'Unknown User')
                    
                    return user_id, display_name
            
        except (ValueError, IndexError):
            pass
    
    # Fallback: try to match by name (for backward compatibility)
    selected_normalized = selected_user_option.lower().strip()
    
    for user in users_data:
        # Check display_name
        if user.get('display_name') and user.get('display_name').lower().strip() == selected_normalized:
            return user.get('id'), user.get('display_name')
        
        # Check first_name + last_name combination
        first_name = user.get('first_name', '').strip()
        last_name = user.get('last_name', '').strip()
        if first_name and last_name:
            full_name = f"{first_name} {last_name}".lower().strip()
            if full_name == selected_normalized:
                return user.get('id'), f"{first_name} {last_name}"
    
    return None, None


def find_client_in_database(selected_client_option, clients_data):
    """
    Find a client in the database by extracting jobcode ID from selected option
    
    Args:
        selected_client_option (str): The selected client option in format "Name (Jobcode ID: jobcode_id)"
        clients_data (list): List of client data from database
    
    Returns:
        tuple: (jobcode_id, client_display_name) or (None, None) if not found
    """
    if not clients_data or not selected_client_option:
        return None, None
    
    # Extract jobcode ID from the selected option
    # Format: "Client Name (Jobcode ID: jobcode_id)"
    if "(Jobcode ID:" in selected_client_option and ")" in selected_client_option:
        try:
            # Extract the ID part
            id_part = selected_client_option.split("(Jobcode ID:")[-1].split(")")[0].strip()
            jobcode_id = int(id_part)
            
            # Find the client with this jobcode ID
            for client in clients_data:
                if client.get('id') == jobcode_id:
                    client_name = client.get('name', 'Unknown Client')
                    return jobcode_id, client_name
            
        except (ValueError, IndexError):
            pass
    
    # Fallback: try to match by name (for backward compatibility)
    selected_normalized = selected_client_option.lower().strip()
    
    for client in clients_data:
        client_name = client.get('name', '').lower().strip()
        if client_name == selected_normalized:
            return client.get('id'), client.get('name')
    
    return None, None


def generate_user_analytics_markdown(user_name, start_date, end_date, daily_work, client_distribution, team_comparison, period_summary):
    """Generate markdown content for user analytics report"""
    
    # Report header
    markdown = f"""# User Analytics Report: {user_name}

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Period Summary

| Metric | Value |
|--------|-------|
| Total Hours in Period | {period_summary.get('total_hours', 0):.1f} |
| Total Working Days | {period_summary.get('working_days', 0)} |
| Average Hours per Day | {period_summary.get('avg_hours_per_day', 0):.1f} |
| Clients Served | {period_summary.get('clients_served', 0)} |
| Total Sessions | {period_summary.get('total_sessions', 0)} |
| Average Session Length | {period_summary.get('avg_session_length', 0):.1f} hours |

---

## 📅 Daily Work Summary

| Date | Total Hours | Clients Worked | Sessions | Longest Session |
|------|-------------|----------------|----------|-----------------|
"""
    
    # Add daily work data
    if daily_work:
        for day in daily_work:
            markdown += f"| {day.get('work_date', 'N/A')} | {day.get('total_hours', 0):.1f} | {day.get('clients_worked', 0)} | {day.get('sessions', 0)} | {day.get('longest_session_hours', 0):.1f} |\n"
    else:
        markdown += "| No data available for this period |\n"
    
    markdown += "\n---\n\n## 🏢 Client Time Distribution\n\n"
    markdown += "| Client | Total Hours | Sessions | Avg Session | First Date | Last Date |\n"
    markdown += "|--------|-------------|----------|-------------|------------|----------|\n"
    
    # Add client distribution data
    if client_distribution:
        for client in client_distribution:
            markdown += f"| {client.get('client_name', 'N/A')} | {client.get('total_hours', 0):.1f} | {client.get('sessions', 0)} | {client.get('avg_session_hours', 0):.1f} | {client.get('first_date', 'N/A')} | {client.get('last_date', 'N/A')} |\n"
    else:
        markdown += "| No client data available for this period |\n"
    
    markdown += "\n---\n\n## 🏆 User vs DDMAC Team Comparison\n\n"
    markdown += "| Metric | This User | DDMAC Average | Rank | Percentile |\n"
    markdown += "|--------|-----------|---------------|------|------------|\n"
    
    # Add team comparison data
    if team_comparison:
        for metric in team_comparison:
            markdown += f"| {metric.get('metric_name', 'N/A')} | {metric.get('user_value', 0):.1f} | {metric.get('team_average', 0):.1f} | {metric.get('user_rank', 0)}/{metric.get('total_users', 0)} | {metric.get('percentile', 0):.1f}% |\n"
    else:
        markdown += "| No comparison data available |\n"
    
    markdown += "\n---\n\n*Report generated by DDMac Analytics System*"
    
    return markdown


def generate_fallback_user_report(user_name, start_date, end_date):
    """Generate a fallback report when database data is not available"""
    
    markdown = f"""# User Analytics Report: {user_name}

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** ⚠️ Using sample data - database connection unavailable

---

## 📊 Period Summary

| Metric | Value |
|--------|-------|
| Total Hours in Period | 40.0 |
| Total Working Days | 5 |
| Average Hours per Day | 8.0 |
| Clients Served | 3 |
| Total Sessions | 12 |
| Average Session Length | 3.3 hours |

---

## 📅 Daily Work Summary

| Date | Total Hours | Clients Worked | Sessions | Longest Session |
|------|-------------|----------------|----------|-----------------|
| {end_date.strftime('%Y-%m-%d')} | 8.0 | 2 | 3 | 4.0 |
| {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')} | 8.0 | 1 | 2 | 5.0 |
| {(end_date - timedelta(days=2)).strftime('%Y-%m-%d')} | 8.0 | 2 | 3 | 3.5 |
| {(end_date - timedelta(days=3)).strftime('%Y-%m-%d')} | 8.0 | 1 | 2 | 4.5 |
| {(end_date - timedelta(days=4)).strftime('%Y-%m-%d')} | 8.0 | 2 | 2 | 4.0 |

---

## 🏢 Client Time Distribution

| Client | Total Hours | Sessions | Avg Session | First Date | Last Date |
|--------|-------------|----------|-------------|------------|----------|
| Client A - TechCorp | 20.0 | 6 | 3.3 | {start_date.strftime('%Y-%m-%d')} | {end_date.strftime('%Y-%m-%d')} |
| Client B - BuildCo | 15.0 | 4 | 3.8 | {(start_date + timedelta(days=1)).strftime('%Y-%m-%d')} | {end_date.strftime('%Y-%m-%d')} |
| Client C - DesignStudio | 5.0 | 2 | 2.5 | {(start_date + timedelta(days=2)).strftime('%Y-%m-%d')} | {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')} |

---

## 🏆 User vs DDMAC Team Comparison

| Metric | This User | DDMAC Average | Rank | Percentile |
|--------|-----------|---------------|------|------------|
| Total Hours | 40.0 | 35.2 | 2/5 | 80.0% |
| Avg Hours/Day | 8.0 | 7.1 | 1/5 | 100.0% |
| Clients Served | 3 | 2.8 | 2/5 | 80.0% |
| Avg Session Length | 3.3 | 2.9 | 3/5 | 60.0% |
| Longest Session | 5.0 | 4.2 | 1/5 | 100.0% |

---

*Report generated by DDMac Analytics System - Sample Data Mode*
"""
    
    return markdown


def generate_client_analytics_markdown(client_name, start_date, end_date, overview_summary, user_allocation, client_comparison, weekly_summary):
    """Generate markdown content for client analytics report"""
    
    # Report header
    markdown = f"""# Client Analytics Report: {client_name}

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Client Overview Summary

| Metric | Value |
|--------|-------|
| Total Hours Logged | {overview_summary.get('total_hours', 0):.1f} |
| Number of Users Assigned | {overview_summary.get('users_assigned', 0)} |
| Number of Sessions | {overview_summary.get('total_sessions', 0)} |
| Average Hours Per Day | {overview_summary.get('avg_hours_per_day', 0):.1f} |
| Working Days | {overview_summary.get('working_days', 0)} |
| First Date Worked | {overview_summary.get('first_date_worked', 'N/A')} |
| Last Date Worked | {overview_summary.get('last_date_worked', 'N/A')} |

---

## 👥 User Allocation Table

| User | Total Hours | Percentage | Sessions | Avg Session | First Date | Last Date |
|------|-------------|------------|----------|-------------|------------|----------|
"""
    
    # Add user allocation data
    if user_allocation:
        for user in user_allocation:
            markdown += f"| {user.get('user_name', 'N/A')} | {user.get('total_hours', 0):.1f} | {user.get('percentage', 0):.1f}% | {user.get('sessions', 0)} | {user.get('avg_session_hours', 0):.1f} | {user.get('first_date', 'N/A')} | {user.get('last_date', 'N/A')} |\n"
    else:
        markdown += "| No user allocation data available for this period |\n"
    
    markdown += "\n---\n\n## 🏆 Client vs Other Clients Comparison\n\n"
    markdown += "| Metric | This Client | DDMAC Average | Rank | Percentile |\n"
    markdown += "|--------|-------------|---------------|------|------------|\n"
    
    # Add client comparison data
    if client_comparison:
        for metric in client_comparison:
            markdown += f"| {metric.get('metric_name', 'N/A')} | {metric.get('client_value', 0):.1f} | {metric.get('ddmac_average', 0):.1f} | {metric.get('client_rank', 0)}/{metric.get('total_clients', 0)} | {metric.get('percentile', 0):.1f}% |\n"
    else:
        markdown += "| No comparison data available |\n"
    
    markdown += "\n---\n\n## 📅 Weekly Summary\n\n"
    markdown += "| Week | Total Hours | Users Active | Sessions | Average Session |\n"
    markdown += "|------|-------------|--------------|----------|-----------------|\n"
    
    # Add weekly summary data
    if weekly_summary:
        for week in weekly_summary:
            markdown += f"| {week.get('week_start', 'N/A')} to {week.get('week_end', 'N/A')} | {week.get('total_hours', 0):.1f} | {week.get('users_active', 0)} | {week.get('sessions', 0)} | {week.get('avg_session_hours', 0):.1f} |\n"
    else:
        markdown += "| No weekly data available for this period |\n"
    
    markdown += "\n---\n\n*Report generated by DDMac Analytics System*"
    
    return markdown


def generate_fallback_client_report(client_name, start_date, end_date):
    """Generate a fallback client report when database data is not available"""
    
    markdown = f"""# Client Analytics Report: {client_name}

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** ⚠️ Using sample data - database connection unavailable

---

## 📊 Client Overview Summary

| Metric | Value |
|--------|-------|
| Total Hours Logged | 120.0 |
| Number of Users Assigned | 3 |
| Number of Sessions | 25 |
| Average Hours Per Day | 8.0 |
| Working Days | 15 |
| First Date Worked | {start_date.strftime('%Y-%m-%d')} |
| Last Date Worked | {end_date.strftime('%Y-%m-%d')} |

---

## 👥 User Allocation Table

| User | Total Hours | Percentage | Sessions | Avg Session | First Date | Last Date |
|------|-------------|------------|----------|-------------|------------|----------|
| John Smith | 60.0 | 50.0% | 12 | 5.0 | {start_date.strftime('%Y-%m-%d')} | {end_date.strftime('%Y-%m-%d')} |
| Jane Doe | 40.0 | 33.3% | 8 | 5.0 | {(start_date + timedelta(days=2)).strftime('%Y-%m-%d')} | {end_date.strftime('%Y-%m-%d')} |
| Mike Johnson | 20.0 | 16.7% | 5 | 4.0 | {(start_date + timedelta(days=5)).strftime('%Y-%m-%d')} | {(end_date - timedelta(days=2)).strftime('%Y-%m-%d')} |

---

## 🏆 Client vs Other Clients Comparison

| Metric | This Client | DDMAC Average | Rank | Percentile |
|--------|-------------|---------------|------|------------|
| Total Hours | 120.0 | 95.5 | 2/8 | 87.5% |
| Users Assigned | 3 | 2.4 | 3/8 | 75.0% |
| Avg Session Length | 4.8 | 3.2 | 1/8 | 100.0% |
| Working Days | 15 | 12.3 | 2/8 | 87.5% |
| Hours per Week | 56.0 | 45.2 | 1/8 | 100.0% |

---

## 📅 Weekly Summary

| Week | Total Hours | Users Active | Sessions | Average Session |
|------|-------------|--------------|----------|-----------------|
| {start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(days=6)).strftime('%Y-%m-%d')} | 40.0 | 3 | 8 | 5.0 |
| {(start_date + timedelta(days=7)).strftime('%Y-%m-%d')} to {(start_date + timedelta(days=13)).strftime('%Y-%m-%d')} | 50.0 | 2 | 10 | 5.0 |
| {(start_date + timedelta(days=14)).strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} | 30.0 | 2 | 7 | 4.3 |

---

*Report generated by DDMac Analytics System - Sample Data Mode*
"""
    
    return markdown


def generate_time_analytics_markdown(start_date, end_date, period_overview, daily_distribution, user_performance, client_activity, weekly_summary, session_analysis):
    """Generate markdown content for time analytics report"""
    
    # Report header
    markdown = f"""# Time Analytics Report - DDMAC Company Overview

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Period Overview Summary

| Metric | Value |
|--------|-------|
| Total Hours Logged | {period_overview.get('total_hours', 0):.1f} |
| Total Users Active | {period_overview.get('total_users', 0)} |
| Total Clients Served | {period_overview.get('total_clients', 0)} |
| Total Sessions | {period_overview.get('total_sessions', 0)} |
| Working Days | {period_overview.get('working_days', 0)} |
| Average Daily Hours | {period_overview.get('avg_daily_hours', 0):.1f} |
| Average Session Length | {period_overview.get('avg_session_length', 0):.1f} hours |

---

## 📅 Daily Time Distribution

| Date | Total Hours | Users Active | Clients Active | Sessions | Longest Session |
|------|-------------|--------------|----------------|----------|-----------------|
"""
    
    # Add daily distribution data
    if daily_distribution:
        for day in daily_distribution:
            markdown += f"| {day.get('work_date', 'N/A')} | {day.get('total_hours', 0):.1f} | {day.get('users_active', 0)} | {day.get('clients_active', 0)} | {day.get('sessions', 0)} | {day.get('longest_session_hours', 0):.1f} |\n"
    else:
        markdown += "| No data available for this period |\n"
    
    markdown += "\n---\n\n## 🏆 User Performance Ranking\n\n"
    markdown += "| Rank | User | Total Hours | Working Days | Avg Hours/Day | Clients Served | Sessions |\n"
    markdown += "|------|------|-------------|--------------|---------------|----------------|----------|\n"
    
    # Add user performance data
    if user_performance:
        for rank, user in enumerate(user_performance, 1):
            markdown += f"| {rank} | {user.get('user_name', 'N/A')} | {user.get('total_hours', 0):.1f} | {user.get('working_days', 0)} | {user.get('avg_hours_per_day', 0):.1f} | {user.get('clients_served', 0)} | {user.get('sessions', 0)} |\n"
    else:
        markdown += "| No user performance data available for this period |\n"
    
    markdown += "\n---\n\n## 🏢 Client Activity Summary\n\n"
    markdown += "| Client | Total Hours | Users Assigned | Sessions | Avg Session | Working Days |\n"
    markdown += "|--------|-------------|----------------|----------|-------------|--------------|\n"
    
    # Add client activity data
    if client_activity:
        for client in client_activity:
            markdown += f"| {client.get('client_name', 'N/A')} | {client.get('total_hours', 0):.1f} | {client.get('users_assigned', 0)} | {client.get('sessions', 0)} | {client.get('avg_session_hours', 0):.1f} | {client.get('working_days', 0)} |\n"
    else:
        markdown += "| No client activity data available for this period |\n"
    
    markdown += "\n---\n\n## 📅 Weekly Summary\n\n"
    markdown += "| Week | Total Hours | Daily Average | Users | Clients | Sessions |\n"
    markdown += "|------|-------------|---------------|-------|---------|----------|\n"
    
    # Add weekly summary data
    if weekly_summary:
        for week in weekly_summary:
            markdown += f"| {week.get('week_start', 'N/A')} to {week.get('week_end', 'N/A')} | {week.get('total_hours', 0):.1f} | {week.get('daily_average', 0):.1f} | {week.get('users', 0)} | {week.get('clients', 0)} | {week.get('sessions', 0)} |\n"
    else:
        markdown += "| No weekly data available for this period |\n"
    
    markdown += "\n---\n\n## ⏱️ Session Length Analysis\n\n"
    markdown += "| Session Type | Count | Total Hours | Percentage |\n"
    markdown += "|--------------|-------|-------------|------------|\n"
    
    # Add session analysis data
    if session_analysis:
        for session_type in session_analysis:
            markdown += f"| {session_type.get('session_type', 'N/A')} | {session_type.get('count', 0)} | {session_type.get('total_hours', 0):.1f} | {session_type.get('percentage', 0):.1f}% |\n"
    else:
        markdown += "| No session analysis data available for this period |\n"
    
    markdown += "\n---\n\n*Report generated by DDMac Analytics System*"
    
    return markdown


def generate_fallback_time_analytics_report(start_date, end_date):
    """Generate a fallback time analytics report when database data is not available"""
    
    # Calculate some basic metrics for the fallback
    days_diff = (end_date - start_date).days + 1
    working_days = min(days_diff, 5)  # Assume 5 working days per week
    
    markdown = f"""# Time Analytics Report - DDMAC Company Overview

**Report Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** ⚠️ Using sample data - database connection unavailable

---

## 📊 Period Overview Summary

| Metric | Value |
|--------|-------|
| Total Hours Logged | 320.0 |
| Total Users Active | 5 |
| Total Clients Served | 7 |
| Total Sessions | 85 |
| Working Days | {working_days} |
| Average Daily Hours | {320.0/working_days:.1f} |
| Average Session Length | 3.8 hours |

---

## 📅 Daily Time Distribution

| Date | Total Hours | Users Active | Clients Active | Sessions | Longest Session |
|------|-------------|--------------|----------------|----------|-----------------|
"""
    
    # Generate sample daily data
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Only weekdays
            markdown += f"| {current_date.strftime('%Y-%m-%d')} | 64.0 | 4 | 3 | 17 | 6.5 |\n"
        current_date += timedelta(days=1)
    
    markdown += "\n---\n\n## 🏆 User Performance Ranking\n\n"
    markdown += "| Rank | User | Total Hours | Working Days | Avg Hours/Day | Clients Served | Sessions |\n"
    markdown += "|------|------|-------------|--------------|---------------|----------------|----------|\n"
    markdown += "| 1 | John Smith | 85.0 | 5 | 17.0 | 4 | 22 |\n"
    markdown += "| 2 | Jane Doe | 75.0 | 5 | 15.0 | 3 | 20 |\n"
    markdown += "| 3 | Mike Johnson | 65.0 | 5 | 13.0 | 5 | 18 |\n"
    markdown += "| 4 | Sarah Wilson | 55.0 | 4 | 13.8 | 2 | 15 |\n"
    markdown += "| 5 | Tom Brown | 40.0 | 3 | 13.3 | 3 | 10 |\n"
    
    markdown += "\n---\n\n## 🏢 Client Activity Summary\n\n"
    markdown += "| Client | Total Hours | Users Assigned | Sessions | Avg Session | Working Days |\n"
    markdown += "|--------|-------------|----------------|----------|-------------|--------------|\n"
    markdown += "| Client A - TechCorp | 120.0 | 3 | 32 | 3.8 | 5 |\n"
    markdown += "| Client B - BuildCo | 85.0 | 2 | 22 | 3.9 | 4 |\n"
    markdown += "| Client C - DesignStudio | 60.0 | 2 | 15 | 4.0 | 3 |\n"
    markdown += "| Client D - ManufacturingInc | 35.0 | 1 | 9 | 3.9 | 2 |\n"
    markdown += "| Client E - RetailChain | 20.0 | 1 | 7 | 2.9 | 1 |\n"
    
    markdown += "\n---\n\n## 📅 Weekly Summary\n\n"
    markdown += "| Week | Total Hours | Daily Average | Users | Clients | Sessions |\n"
    markdown += "|------|-------------|---------------|-------|---------|----------|\n"
    
    # Generate sample weekly data
    week_start = start_date
    week_num = 1
    while week_start <= end_date:
        week_end = min(week_start + timedelta(days=6), end_date)
        markdown += f"| Week {week_num} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}) | 160.0 | 32.0 | 4 | 5 | 42 |\n"
        week_start += timedelta(days=7)
        week_num += 1
    
    markdown += "\n---\n\n## ⏱️ Session Length Analysis\n\n"
    markdown += "| Session Type | Count | Total Hours | Percentage |\n"
    markdown += "|--------------|-------|-------------|------------|\n"
    markdown += "| Short Sessions (< 2 hours) | 25 | 37.5 | 11.7% |\n"
    markdown += "| Medium Sessions (2-4 hours) | 45 | 135.0 | 42.2% |\n"
    markdown += "| Long Sessions (4+ hours) | 15 | 147.5 | 46.1% |\n"
    
    markdown += "\n---\n\n*Report generated by DDMac Analytics System - Sample Data Mode*"
    
    return markdown