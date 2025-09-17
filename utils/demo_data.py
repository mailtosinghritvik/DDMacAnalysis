"""
Demo Data Initialization for DDMac Analytics Platform
Ensures all pages work seamlessly with realistic sample data
"""

import streamlit as st
from utils import (
    get_api_handler,
    get_estimates_handler,
    get_progress_comparison,
    get_budget_alerts
)

def initialize_demo_data():
    """Initialize demo data for all components"""
    try:
        # Initialize API handler with sample data
        api_handler = get_api_handler()
        api_sample_data = api_handler.get_sample_data()
        
        # Initialize estimates handler with sample data
        estimates_handler = get_estimates_handler()
        estimates_sample_data = estimates_handler.get_sample_data()
        
        # Generate progress comparison
        progress_data = get_progress_comparison(api_sample_data, estimates_sample_data)
        
        # Generate alerts
        alerts_data = get_budget_alerts(progress_data)
        
        # Store in session state
        st.session_state['demo_api_data'] = api_sample_data
        st.session_state['demo_estimates_data'] = estimates_sample_data
        st.session_state['demo_progress_data'] = progress_data
        st.session_state['demo_alerts_data'] = alerts_data
        st.session_state['demo_initialized'] = True
        
        return True
        
    except Exception as e:
        st.error(f"Error initializing demo data: {str(e)}")
        return False

def get_demo_data():
    """Get demo data, initializing if necessary"""
    if not st.session_state.get('demo_initialized', False):
        initialize_demo_data()
    
    return {
        'api_data': st.session_state.get('demo_api_data'),
        'estimates_data': st.session_state.get('demo_estimates_data'),
        'progress_data': st.session_state.get('demo_progress_data'),
        'alerts_data': st.session_state.get('demo_alerts_data')
    }

def create_sample_excel_data():
    """Create sample Excel data structure for testing uploads"""
    import pandas as pd
    
    sample_estimates = [
        {
            'project_name': 'TechCorp Mobile App',
            'estimated_hours': 320,
            'estimated_cost': 48000,
            'deadline': '2024-04-15',
            'status': 'In Progress',
            'client': 'TechCorp Inc',
            'priority': 'High'
        },
        {
            'project_name': 'GlobalSoft Dashboard',
            'estimated_hours': 280,
            'estimated_cost': 42000,
            'deadline': '2024-03-30',
            'status': 'In Progress',
            'client': 'GlobalSoft',
            'priority': 'Medium'
        },
        {
            'project_name': 'StartupX Website',
            'estimated_hours': 180,
            'estimated_cost': 27000,
            'deadline': '2024-02-28',
            'status': 'In Progress',
            'client': 'StartupX',
            'priority': 'High'
        },
        {
            'project_name': 'Internal Tools',
            'estimated_hours': 160,
            'estimated_cost': 24000,
            'deadline': '2024-05-15',
            'status': 'Planning',
            'client': 'Internal',
            'priority': 'Low'
        }
    ]
    
    return pd.DataFrame(sample_estimates)

def validate_integration():
    """Validate that all components are working together"""
    validation_results = {
        'api_handler': False,
        'estimates_handler': False,
        'progress_comparison': False,
        'budget_alerts': False
    }
    
    try:
        # Test API handler
        api_handler = get_api_handler()
        api_data = api_handler.get_sample_data()
        validation_results['api_handler'] = api_data is not None
        
        # Test estimates handler
        estimates_handler = get_estimates_handler()
        estimates_data = estimates_handler.get_sample_data()
        validation_results['estimates_handler'] = estimates_data is not None
        
        # Test progress comparison
        if api_data and estimates_data:
            progress_data = get_progress_comparison(api_data, estimates_data)
            validation_results['progress_comparison'] = progress_data is not None
            
            # Test budget alerts
            if progress_data:
                alerts_data = get_budget_alerts(progress_data)
                validation_results['budget_alerts'] = alerts_data is not None
    
    except Exception as e:
        st.error(f"Validation error: {str(e)}")
    
    return validation_results

def display_demo_status():
    """Display demo data status in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🎮 Demo Mode Status")
        
        # Initialize demo data button
        if st.button("🚀 Initialize Demo Data"):
            if initialize_demo_data():
                st.success("✅ Demo data initialized!")
                st.rerun()
            else:
                st.error("❌ Failed to initialize demo data")
        
        # Show current status
        if st.session_state.get('demo_initialized', False):
            st.success("✅ Demo data active")
            
            # Show data summary
            demo_data = get_demo_data()
            if demo_data['api_data']:
                st.metric("API Data", "Active")
            if demo_data['estimates_data']:
                st.metric("Estimates Data", "Active")
            if demo_data['progress_data']:
                st.metric("Progress Tracking", f"{len(demo_data['progress_data'])} projects")
            if demo_data['alerts_data']:
                st.metric("Active Alerts", len(demo_data['alerts_data']))
        else:
            st.info("Demo data not initialized")
        
        # Validation button
        if st.button("🔍 Validate Integration"):
            results = validate_integration()
            
            st.markdown("**Validation Results:**")
            for component, status in results.items():
                icon = "✅" if status else "❌"
                st.write(f"{icon} {component.replace('_', ' ').title()}")

# Helper functions for pages to use demo data
def get_page_data(page_name):
    """Get data specific to a page, with demo fallback"""
    demo_data = get_demo_data()
    
    # Return appropriate data based on page
    if page_name.lower() in ['home', 'dashboard']:
        return demo_data['api_data'], demo_data['estimates_data'], demo_data['progress_data'], demo_data['alerts_data']
    elif page_name.lower() == 'employee':
        return demo_data['api_data'], demo_data['estimates_data'], demo_data['progress_data']
    elif page_name.lower() == 'project':
        return demo_data['api_data'], demo_data['estimates_data'], demo_data['progress_data'], demo_data['alerts_data']
    else:
        return demo_data['api_data'], demo_data['estimates_data'], None, None

def ensure_demo_data():
    """Decorator function to ensure demo data is available"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('demo_initialized', False):
                initialize_demo_data()
            return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the demo data system
    st.title("Demo Data Test")
    
    if st.button("Test Demo Data"):
        if initialize_demo_data():
            st.success("Demo data initialized successfully!")
            
            demo_data = get_demo_data()
            st.json(demo_data)
        else:
            st.error("Failed to initialize demo data")
    
    # Display validation results
    if st.button("Run Validation"):
        results = validate_integration()
        st.json(results)
