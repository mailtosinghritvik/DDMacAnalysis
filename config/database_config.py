"""
Database Configuration for Employee Analytics
Update these parameters with your actual database details
"""

import os
from typing import Dict

def get_database_config() -> Dict:
    """
    Get database configuration from environment variables or defaults
    
    Returns:
        Dict: Database connection parameters
    """
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': int(os.getenv('DB_PORT', 5432))
    }

def get_streamlit_secrets_config() -> Dict:
    """
    Get database configuration from Streamlit secrets
    
    Returns:
        Dict: Database connection parameters
    """
    try:
        import streamlit as st
        return {
            'host': st.secrets.get('DB_HOST', 'localhost'),
            'database': st.secrets.get('DB_NAME', 'postgres'),
            'user': st.secrets.get('DB_USER', 'postgres'),
            'password': st.secrets.get('DB_PASSWORD', 'password'),
            'port': st.secrets.get('DB_PORT', 5432)
        }
    except:
        # Fallback if streamlit is not available
        return get_database_config()

# Common database configurations for different environments
DATABASE_CONFIGS = {
    'development': {
        'host': 'localhost',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    },
    'production': {
        'host': 'your_production_host',
        'database': 'your_production_database',
        'user': 'your_production_user',
        'password': 'your_production_password',
        'port': 5432
    },
    'supabase': {
        'host': 'your_supabase_host',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'your_supabase_password',
        'port': 5432
    }
}

def get_config_by_environment(env: str = 'development') -> Dict:
    """
    Get database configuration by environment
    
    Args:
        env (str): Environment name ('development', 'production', 'supabase')
        
    Returns:
        Dict: Database connection parameters
    """
    return DATABASE_CONFIGS.get(env, DATABASE_CONFIGS['development'])
