import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Settings - DDMac Analysis",
    page_icon="⚙️",
    layout="wide"
)

def save_settings():
    """Save settings to session state"""
    st.success("Settings saved successfully!")

def main():
    """Main settings function"""
    st.title("⚙️ Application Settings")
    st.markdown("Configure your DDMac Analysis Tool preferences")
    
    # API Configuration
    st.header("🔑 API Configuration")
    with st.expander("OpenAI API Settings", expanded=True):
        api_key = st.text_input(
            "OpenAI API Key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            help="Enter your OpenAI API key for AI chat functionality"
        )
        
        if api_key:
            # Store in session state (in production, use proper secure storage)
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ API Key required for AI chat functionality")
    
    # Display Settings
    st.header("🎨 Display Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "Auto"],
            index=0,
            help="Choose your preferred theme"
        )
        
        chart_color = st.selectbox(
            "Chart Color Scheme",
            ["Default", "Plotly", "Viridis", "Plasma", "Blues"],
            index=0,
            help="Default color scheme for charts"
        )
    
    with col2:
        rows_per_page = st.number_input(
            "Rows per page in data tables",
            min_value=10,
            max_value=1000,
            value=50,
            step=10,
            help="Number of rows to display in data tables"
        )
        
        auto_refresh = st.checkbox(
            "Auto-refresh data",
            value=False,
            help="Automatically refresh data every 30 seconds"
        )
    
    # Data Processing Settings
    st.header("📊 Data Processing Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        max_file_size = st.number_input(
            "Maximum file size (MB)",
            min_value=1,
            max_value=200,
            value=50,
            help="Maximum size for uploaded files"
        )
        
        cache_data = st.checkbox(
            "Cache processed data",
            value=True,
            help="Cache processed data to improve performance"
        )
    
    with col2:
        date_format = st.selectbox(
            "Date format",
            ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"],
            index=0,
            help="Default date format for parsing"
        )
        
        decimal_places = st.number_input(
            "Decimal places for numbers",
            min_value=0,
            max_value=10,
            value=2,
            help="Number of decimal places to display"
        )
    
    # Export Settings
    st.header("📤 Export Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.multiselect(
            "Default export formats",
            ["CSV", "Excel", "JSON", "PDF"],
            default=["CSV", "Excel"],
            help="Available export formats"
        )
    
    with col2:
        include_metadata = st.checkbox(
            "Include metadata in exports",
            value=True,
            help="Include processing timestamp and settings in exports"
        )
    
    # Advanced Settings
    with st.expander("🔧 Advanced Settings"):
        st.subheader("Performance")
        
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.number_input(
                "Data processing chunk size",
                min_value=1000,
                max_value=100000,
                value=10000,
                step=1000,
                help="Size of data chunks for processing large files"
            )
        
        with col2:
            memory_limit = st.number_input(
                "Memory limit (MB)",
                min_value=100,
                max_value=8192,
                value=1024,
                help="Memory limit for data processing"
            )
        
        st.subheader("Logging")
        log_level = st.selectbox(
            "Log level",
            ["ERROR", "WARNING", "INFO", "DEBUG"],
            index=2,
            help="Application logging level"
        )
        
        log_to_file = st.checkbox(
            "Log to file",
            value=False,
            help="Save logs to file"
        )
    
    # Save/Reset buttons
    st.header("💾 Save Settings")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Settings", type="primary"):
            # Store settings in session state
            st.session_state.settings = {
                'theme': theme,
                'chart_color': chart_color,
                'rows_per_page': rows_per_page,
                'auto_refresh': auto_refresh,
                'max_file_size': max_file_size,
                'cache_data': cache_data,
                'date_format': date_format,
                'decimal_places': decimal_places,
                'export_format': export_format,
                'include_metadata': include_metadata,
                'chunk_size': chunk_size,
                'memory_limit': memory_limit,
                'log_level': log_level,
                'log_to_file': log_to_file
            }
            save_settings()
    
    with col2:
        if st.button("🔄 Reset to Defaults"):
            # Clear settings from session state
            if 'settings' in st.session_state:
                del st.session_state.settings
            st.warning("Settings reset to defaults. Please refresh the page.")
    
    # Show current settings info
    if 'settings' in st.session_state:
        st.info(f"⚙️ Settings last saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
