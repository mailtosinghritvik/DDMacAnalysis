"""
DDMac Analytics Utils Package
Exports all analytics functions for easy import across the application
"""

# Chart utilities and data processors
try:
    from .data_processor import *
except ImportError:
    pass

try:
    from .chart_utils import *
except ImportError:
    pass

# Original time analysis functions (for local/uploaded data)
from .time_analysis import (
    TimeTrackingAnalyzer,
    analyze_clients,
    analyze_projects_for_client,
    analyze_employees_overview,
    analyze_employee_detailed,
    analyze_all_projects,
    get_project_health_metrics,
    get_employee_performance_metrics,
    generate_sample_timesheet_data
)

# Real-time API data handler functions
from .api_data_handler import (
    TimesheetAPIHandler,
    get_api_handler,
    fetch_real_time_data,
    analyze_clients_api,
    analyze_projects_for_client_api,
    analyze_employees_overview_api,
    analyze_employee_detailed_api,
    analyze_project_details_api
)

# Excel estimates handler functions
from .estimates_handler import (
    EstimatesHandler,
    get_estimates_handler,
    process_excel_upload,
    get_progress_comparison,
    get_budget_alerts
)

# Demo data utilities
from .demo_data import (
    initialize_demo_data,
    get_demo_data,
    get_page_data,
    display_demo_status,
    validate_integration,
    create_sample_excel_data,
    ensure_demo_data
)

__all__ = [
    # Original functions
    'TimeTrackingAnalyzer',
    'analyze_clients',
    'analyze_projects_for_client',
    'analyze_employees_overview', 
    'analyze_employee_detailed',
    'analyze_all_projects',
    'get_project_health_metrics',
    'get_employee_performance_metrics',
    'generate_sample_timesheet_data',
    
    # API functions
    'TimesheetAPIHandler',
    'get_api_handler',
    'fetch_real_time_data',
    'analyze_clients_api',
    'analyze_projects_for_client_api',
    'analyze_employees_overview_api',
    'analyze_employee_detailed_api',
    'analyze_project_details_api',
    
    # Estimates functions
    'EstimatesHandler',
    'get_estimates_handler',
    'process_excel_upload',
    'get_progress_comparison',
    'get_budget_alerts',
    
    # Demo data functions
    'initialize_demo_data',
    'get_demo_data',
    'get_page_data',
    'display_demo_status',
    'validate_integration',
    'create_sample_excel_data',
    'ensure_demo_data'
]
