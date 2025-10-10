import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import tempfile
import os

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("❌ Supabase not installed. Run: pip install supabase")

# Supabase configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
if SUPABASE_AVAILABLE and SUPABASE_URL != "LMAO_WOW":
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        SUPABASE_CONFIGURED = True
    except Exception as e:
        SUPABASE_CONFIGURED = False
        st.error(f"❌ Supabase connection error: {str(e)}")
else:
    SUPABASE_CONFIGURED = False

# Set page configuration
st.set_page_config(
    page_title="Accubid Estimates - DDMac Analytics",
    page_icon="📊",
    layout="wide"
)

# Custom CSS matching DDMac design language
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
    
    .upload-zone {
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    /* Style the file uploader */
    .stFileUploader > div {
        border: 2px dashed #667eea !important;
        border-radius: 15px !important;
        padding: 2rem !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        text-align: center !important;
        margin: 1rem 0 !important;
    }
    
    .stFileUploader > div:hover {
        border-color: #764ba2 !important;
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2) !important;
    }
    
    .file-info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .indicator-table {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
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
    
    .sidebar-info {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def process_accubid_excel(uploaded_file):
    """
    Process AccuBid Excel file and extract Key Indicators and Breakdown sheets
    """
    try:
        # Read the Excel file
        excel_file = pd.ExcelFile(uploaded_file)
        
        results = {}
        
        # Process Key Indicators sheet
        if 'Key Indicators' not in excel_file.sheet_names:
            st.error("❌ 'Key Indicators' sheet not found in the uploaded file.")
        else:
            # Read the Key Indicators sheet
            key_indicators_df = pd.read_excel(excel_file, sheet_name='Key Indicators')
            
            # Validate that we have the expected columns
            if len(key_indicators_df.columns) >= 2:
                # Get the first two columns and rename them
                indicators_data = key_indicators_df.iloc[:, :2].copy()
                indicators_data.columns = ['Key Indicators', 'Values']
                
                # Remove any empty rows
                indicators_data = indicators_data.dropna(subset=['Key Indicators'])
                results['key_indicators'] = indicators_data
            else:
                st.error("❌ Key Indicators sheet must have at least 2 columns.")
        
        # Process Breakdown sheet
        if 'Breakdown' not in excel_file.sheet_names:
            st.warning("⚠️ 'Breakdown' sheet not found in the uploaded file.")
        else:
            # Read the Breakdown sheet
            breakdown_df = pd.read_excel(excel_file, sheet_name='Breakdown')
            
            # Look for the required columns (case-insensitive)
            breakdown_columns = breakdown_df.columns.str.lower()
            
            system_col = None
            total_hrs_col = None
            total_col = None
            
            # Find the columns (flexible matching)
            for col in breakdown_df.columns:
                col_lower = col.lower().strip()
                if 'system' in col_lower:
                    system_col = col
                elif col_lower == 'total hrs' or col_lower == 'total_hrs':
                    total_hrs_col = col
                elif col_lower == 'total':
                    total_col = col
            
            if system_col and (total_hrs_col or total_col):
                # Create the breakdown data
                breakdown_data = breakdown_df.copy()
                
                # Select relevant columns in the correct order
                selected_cols = [system_col]
                if total_hrs_col:
                    selected_cols.append(total_hrs_col)
                if total_col:
                    selected_cols.append(total_col)
                
                breakdown_data = breakdown_data[selected_cols]
                
                # Rename columns for consistency while preserving original names
                column_mapping = {system_col: 'System'}
                if total_hrs_col:
                    column_mapping[total_hrs_col] = 'Total Hrs'
                if total_col:
                    column_mapping[total_col] = 'Total'
                
                breakdown_data = breakdown_data.rename(columns=column_mapping)
                
                # Remove empty rows
                breakdown_data = breakdown_data.dropna(subset=['System'])
                results['breakdown'] = breakdown_data
            else:
                st.warning("⚠️ Breakdown sheet doesn't contain expected columns (System, Total Hrs, Total).")
                st.info(f"Available columns: {', '.join(breakdown_df.columns)}")
        
        return results, excel_file.sheet_names
        
    except Exception as e:
        st.error(f"❌ Error processing Excel file: {str(e)}")
        return {}, []

def generate_upload_preview(data, job_name, client_name):
    """
    Generate a preview of records that will be uploaded to Supabase
    """
    preview_records = []
    
    # Process Key Indicators data (EVERYTHING record)
    if 'key_indicators' in data:
        key_data = data['key_indicators']
        
        # Find Total Labor Hours and Final Price
        labor_hours_row = key_data[key_data['Key Indicators'] == 'Total Labor Hours']
        final_price_row = key_data[key_data['Key Indicators'] == 'Final Price']
        
        if not labor_hours_row.empty and not final_price_row.empty:
            try:
                labor_hours = float(labor_hours_row['Values'].iloc[0])
                final_price_str = str(final_price_row['Values'].iloc[0]).replace('$', '').replace(',', '')
                final_price = float(final_price_str)
                
                # Create "EVERYTHING" record
                preview_records.append({
                    "job_name": job_name,
                    "client_name": client_name,
                    "Task_name": "EVERYTHING",
                    "time_estimate": labor_hours,
                    "cost_estimate": final_price
                })
            except (ValueError, TypeError) as e:
                # Add error record for debugging
                preview_records.append({
                    "job_name": job_name,
                    "client_name": client_name,
                    "Task_name": "EVERYTHING",
                    "time_estimate": f"Error: {str(e)}",
                    "cost_estimate": f"Error: {str(e)}"
                })
    
    # Process Breakdown data (individual system records)
    if 'breakdown' in data:
        breakdown_data = data['breakdown']
        
        # Filter out excluded systems
        excluded_systems = ['Revised Totals', 'Remainder', 'Final Price']
        filtered_breakdown = breakdown_data[~breakdown_data['System'].isin(excluded_systems)]
        
        # Create record for each system
        for _, row in filtered_breakdown.iterrows():
            system = row['System']
            
            # Get time and cost estimates if available
            time_est = 0
            cost_est = 0
            
            if 'Total Hrs' in row:
                try:
                    time_est = float(row['Total Hrs']) if pd.notna(row['Total Hrs']) else 0
                except (ValueError, TypeError):
                    time_est = f"Error parsing: {row['Total Hrs']}"
            
            if 'Total' in row:
                try:
                    total_value = str(row['Total']).replace('$', '').replace(',', '') if pd.notna(row['Total']) else '0'
                    cost_est = float(total_value)
                except (ValueError, TypeError):
                    cost_est = f"Error parsing: {row['Total']}"
            
            preview_records.append({
                "job_name": job_name,
                "client_name": client_name,
                "Task_name": system,
                "time_estimate": time_est,
                "cost_estimate": cost_est
            })
    
    return preview_records

def upload_to_supabase(data, job_name, client_name):
    """
    Upload processed AccuBid data to Supabase
    """
    if not SUPABASE_CONFIGURED:
        st.error("❌ Supabase not configured. Please set your URL and API key.")
        return 0, None
    
    try:
        records = []
        
        # Process Key Indicators data (EVERYTHING record)
        if 'key_indicators' in data:
            key_data = data['key_indicators']
            
            # Find Total Labor Hours and Final Price
            labor_hours_row = key_data[key_data['Key Indicators'] == 'Total Labor Hours']
            final_price_row = key_data[key_data['Key Indicators'] == 'Final Price']
            
            if not labor_hours_row.empty and not final_price_row.empty:
                try:
                    labor_hours = float(labor_hours_row['Values'].iloc[0])
                    final_price = float(str(final_price_row['Values'].iloc[0]).replace('$', '').replace(',', ''))
                    
                    # Create "EVERYTHING" record
                    records.append({
                        "job_name": job_name,
                        "client_name": client_name,
                        "Task_name": "EVERYTHING",
                        "time_estimate": labor_hours,
                        "cost_estimate": final_price
                    })
                except (ValueError, TypeError) as e:
                    st.warning(f"⚠️ Could not parse Key Indicators values: {str(e)}")
        
        # Process Breakdown data (individual system records)
        if 'breakdown' in data:
            breakdown_data = data['breakdown']
            
            # Filter out excluded systems
            excluded_systems = ['Revised Totals', 'Remainder', 'Final Price']
            filtered_breakdown = breakdown_data[~breakdown_data['System'].isin(excluded_systems)]
            
            # Create record for each system
            for _, row in filtered_breakdown.iterrows():
                system = row['System']
                
                # Get time and cost estimates if available
                time_est = 0
                cost_est = 0
                
                if 'Total Hrs' in row:
                    try:
                        time_est = float(row['Total Hrs']) if pd.notna(row['Total Hrs']) else 0
                    except (ValueError, TypeError):
                        time_est = 0
                
                if 'Total' in row:
                    try:
                        total_value = str(row['Total']).replace('$', '').replace(',', '') if pd.notna(row['Total']) else '0'
                        cost_est = float(total_value)
                    except (ValueError, TypeError):
                        cost_est = 0
                
                records.append({
                    "job_name": job_name,
                    "client_name": client_name,
                    "Task_name": system,
                    "time_estimate": time_est,
                    "cost_estimate": cost_est
                })
        
        # Upload records to Supabase
        if records:
            result = supabase.table('accubid_breakdowns').insert(records).execute()
            return len(records), result
        else:
            st.warning("⚠️ No records to upload")
            return 0, None
            
    except Exception as e:
        st.error(f"❌ Error uploading to Supabase: {str(e)}")
        return 0, None

def display_key_indicators_table(df):
    """
    Display only specific Key Indicators: Total Labor Hours and Final Price
    """
    st.markdown('<div class="indicator-table">', unsafe_allow_html=True)
    st.subheader("📊 Key Indicators")
    
    # Filter for only the required indicators
    required_indicators = ['Total Labor Hours', 'Final Price']
    filtered_df = df[df['Key Indicators'].isin(required_indicators)].copy()
    
    if filtered_df.empty:
        st.warning("⚠️ 'Total Labor Hours' and 'Final Price' not found in Key Indicators")
        st.info("Available indicators:")
        st.write(df['Key Indicators'].tolist())
        return df
    
    # Create a styled dataframe
    styled_df = filtered_df.style.set_properties(**{
        'background-color': '#f8f9fa',
        'color': '#333333',
        'border': '1px solid #dee2e6',
        'padding': '8px',
        'text-align': 'left'
    }).set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#667eea'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('padding', '12px'),
            ('text-align', 'center')
        ]},
        {'selector': 'tr:nth-of-type(even)', 'props': [
            ('background-color', '#f8f9fa')
        ]},
        {'selector': 'tr:hover', 'props': [
            ('background-color', '#e9ecef')
        ]}
    ])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    return filtered_df

def display_breakdown_table(df):
    """
    Display filtered Breakdown data excluding specific systems
    """
    st.markdown('<div class="indicator-table">', unsafe_allow_html=True)
    st.subheader("🔧 System Breakdown")
    
    # Filter out unwanted systems
    excluded_systems = ['Revised Totals', 'Remainder', 'Final Price']
    filtered_df = df[~df['System'].isin(excluded_systems)].copy()
    
    if filtered_df.empty:
        st.warning("⚠️ No systems found after filtering")
        st.info("Available systems:")
        st.write(df['System'].tolist())
        return df
    
    # Show only System, Total Hrs, and Total columns if they exist
    display_columns = ['System']
    if 'Total Hrs' in filtered_df.columns:
        display_columns.append('Total Hrs')
    if 'Total' in filtered_df.columns:
        display_columns.append('Total')
    
    # Select only the columns we want to display
    display_df = filtered_df[display_columns].copy()
    
    # Create a styled dataframe with different colors for breakdown
    styled_df = display_df.style.set_properties(**{
        'background-color': '#f8f9fa',
        'color': '#333333',
        'border': '1px solid #dee2e6',
        'padding': '8px',
        'text-align': 'left'
    }).set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#764ba2'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('padding', '12px'),
            ('text-align', 'center')
        ]},
        {'selector': 'tr:nth-of-type(even)', 'props': [
            ('background-color', '#f8f9fa')
        ]},
        {'selector': 'tr:hover', 'props': [
            ('background-color', '#e9ecef')
        ]}
    ])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    return display_df

def main():
    """Main Accubid Excel Ingestion Page"""
    
    # Header
    st.markdown('<div class="main-header">📊 AccuBid Estimates Analysis</div>', unsafe_allow_html=True)
    st.markdown("**Upload your AccuBid Excel files to analyze Key Indicators and project estimates**")
    
    # Sidebar with information
    with st.sidebar:
        st.header("📋 AccuBid File Requirements")
        
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.markdown("**📁 Expected File Format:**")
        st.markdown("• Excel file (.xlsx, .xls)")
        st.markdown("• Must contain 'Key Indicators' sheet")
        st.markdown("• First column: 'Key Indicators'")
        st.markdown("• Second column: 'Values'")
        st.markdown("• Optional 'Breakdown' sheet")
        st.markdown("• Breakdown columns: 'System', 'Total Hrs', 'Total'")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("ℹ️ About AccuBid")
        st.markdown("""
        AccuBid is electrical estimating software that generates 
        standardized Excel reports with project cost breakdowns, 
        labor estimates, and key performance indicators.
        """)
        
        # Sample file download
        st.markdown("---")
        st.subheader("📁 Sample File")
        st.markdown("Don't have an AccuBid file? Download our sample:")
        
        sample_file_path = "temp/Sample_AccuBid_Estimate.xlsx"
        if os.path.exists(sample_file_path):
            with open(sample_file_path, "rb") as file:
                st.download_button(
                    label="📥 Download Sample AccuBid File",
                    data=file.read(),
                    file_name="Sample_AccuBid_Estimate.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.info("💡 Sample file not available. Upload your own AccuBid Excel file.")
        
        # Display current data info if available
        if 'accubid_data' in st.session_state:
            data = st.session_state['accubid_data']
            st.markdown("---")
            st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
            st.markdown("**📈 Current Dataset:**")
            
            if 'key_indicators' in data:
                st.metric("Key Indicators", len(data['key_indicators']))
            
            if 'breakdown' in data:
                st.metric("Breakdown Systems", len(data['breakdown']))
            
            st.metric("File Name", st.session_state.get('accubid_filename', 'Unknown'))
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Upload section
        st.markdown("### 📁 Upload AccuBid File")
        st.markdown("Drag and drop your Excel file here")
        
        uploaded_file = st.file_uploader(
            "Choose your AccuBid Excel file",
            type=['xlsx', 'xls'],
            help="Upload Excel files generated by AccuBid software containing 'Key Indicators' sheet"
        )
        
        # File processing
        if uploaded_file is not None:
            # Store file info
            st.session_state['accubid_filename'] = uploaded_file.name
            
            # Display file details
            st.markdown('<div class="file-info-card">', unsafe_allow_html=True)
            st.markdown("**📄 File Details**")
            st.markdown(f"**Name:** {uploaded_file.name}")
            st.markdown(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
            st.markdown(f"**Type:** {uploaded_file.type}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add project information inputs
            st.markdown("### 📝 Project Information")
            st.markdown("Please provide the following details:")
            
            # Extract default job name from filename (remove extension)
            default_job_name = os.path.splitext(uploaded_file.name)[0]
            
            # Job name input with default value from filename
            job_name = st.text_input(
                "Job Name",
                value=default_job_name,
                help="Enter the name of the project/job",
                key="job_name_input"
            )
            
            # Client name input
            client_name = st.text_input(
                "Client Name",
                help="Enter the client name for this project",
                key="client_name_input"
            )
            
            # Store in session state
            if job_name:
                st.session_state['job_name'] = job_name
            if client_name:
                st.session_state['client_name'] = client_name
                
            # Process button - only enable if client name is provided
            process_button = st.button(
                "📊 Process File",
                disabled=not client_name,
                help="Client name is required" if not client_name else None,
                type="primary"
            )
            
            if client_name and process_button:
                # Process the file
                with st.spinner("Processing AccuBid file..."):
                    processed_data, available_sheets = process_accubid_excel(uploaded_file)
                
                if processed_data:
                    # Store in session state
                    st.session_state['accubid_data'] = processed_data
                    st.session_state['available_sheets'] = available_sheets
                    
                    # Success message
                    st.markdown('<div class="success-message">', unsafe_allow_html=True)
                    st.markdown(f"✅ **Successfully processed!**")
                    
                    sheets_processed = []
                    if 'key_indicators' in processed_data:
                        sheets_processed.append(f"Key Indicators ({len(processed_data['key_indicators'])} indicators)")
                    if 'breakdown' in processed_data:
                        sheets_processed.append(f"Breakdown ({len(processed_data['breakdown'])} systems)")
                    
                    st.markdown(f"Processed: {', '.join(sheets_processed)}")
                    st.markdown(f"**Client:** {client_name}")
                    st.markdown(f"**Job:** {job_name}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Generate and display upload preview
                    st.markdown("### 📋 Database Upload Preview")
                    st.markdown("**The following records will be uploaded to Supabase:**")
                    
                    preview_records = generate_upload_preview(processed_data, job_name, client_name)
                    
                    if preview_records:
                        # Convert to DataFrame for better display
                        preview_df = pd.DataFrame(preview_records)
                        
                        # Style the preview table
                        styled_preview = preview_df.style.set_properties(**{
                            'background-color': '#f0f8ff',
                            'color': '#333333',
                            'border': '1px solid #b3d9ff',
                            'padding': '8px',
                            'text-align': 'left'
                        }).set_table_styles([
                            {'selector': 'th', 'props': [
                                ('background-color', '#4a90e2'),
                                ('color', 'white'),
                                ('font-weight', 'bold'),
                                ('padding', '12px'),
                                ('text-align', 'center')
                            ]},
                            {'selector': 'tr:nth-of-type(even)', 'props': [
                                ('background-color', '#f8f9fa')
                            ]},
                            {'selector': 'tr:hover', 'props': [
                                ('background-color', '#e6f2ff')
                            ]}
                        ])
                        
                        st.dataframe(styled_preview, use_container_width=True, hide_index=True)
                        
                        # Summary info
                        st.info(f"📊 **Total Records to Upload:** {len(preview_records)}")
                        
                        # Break down by type
                        everything_count = len([r for r in preview_records if r['Task_name'] == 'EVERYTHING'])
                        system_count = len([r for r in preview_records if r['Task_name'] != 'EVERYTHING'])
                        
                        col_preview1, col_preview2 = st.columns(2)
                        with col_preview1:
                            st.metric("Overall Project Records", everything_count)
                        with col_preview2:
                            st.metric("System Breakdown Records", system_count)
                    else:
                        st.warning("⚠️ No records found for upload preview")
                else:
                    # Error handling already done in process_accubid_excel
                    if available_sheets:
                        st.info(f"💡 Available sheets in file: {', '.join(available_sheets)}")
    
    with col2:
        # Display data if available
        if 'accubid_data' in st.session_state:
            processed_data = st.session_state['accubid_data']
            
            # Display Key Indicators if available
            if 'key_indicators' in processed_data:
                indicators_data = processed_data['key_indicators']
                display_key_indicators_table(indicators_data)
            
            # Display Breakdown if available
            if 'breakdown' in processed_data:
                breakdown_data = processed_data['breakdown']
                display_breakdown_table(breakdown_data)
            
            # Additional analysis options
            st.markdown("---")
            st.subheader("📊 Quick Analysis")
            
            # Summary metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                if 'key_indicators' in processed_data:
                    st.metric("Key Indicators", len(processed_data['key_indicators']))
                else:
                    st.metric("Key Indicators", "N/A")
            
            with col_metric2:
                if 'breakdown' in processed_data:
                    st.metric("Breakdown Systems", len(processed_data['breakdown']))
                else:
                    st.metric("Breakdown Systems", "N/A")
            
            with col_metric3:
                # Calculate total values from both sheets
                total_numeric_values = 0
                
                if 'key_indicators' in processed_data:
                    numeric_values = pd.to_numeric(processed_data['key_indicators']['Values'], errors='coerce').dropna()
                    total_numeric_values += len(numeric_values)
                
                if 'breakdown' in processed_data:
                    breakdown_df = processed_data['breakdown']
                    for col in breakdown_df.columns:
                        if col != 'System':
                            numeric_vals = pd.to_numeric(breakdown_df[col], errors='coerce').dropna()
                            total_numeric_values += len(numeric_vals)
                
                st.metric("Total Numeric Values", total_numeric_values)
            
            # Download processed data
            st.markdown("---")
            if st.button("📥 Download Processed Data", type="secondary"):
                # Create combined data for download
                download_data = {}
                
                if 'key_indicators' in processed_data:
                    download_data['Key_Indicators'] = processed_data['key_indicators']
                
                if 'breakdown' in processed_data:
                    download_data['Breakdown'] = processed_data['breakdown']
                
                # Create Excel file with multiple sheets
                import io
                output = io.BytesIO()
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for sheet_name, df in download_data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                st.download_button(
                    label="Download Excel File",
                    data=output.getvalue(),
                    file_name=f"processed_accubid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Supabase upload section
            if SUPABASE_CONFIGURED and 'job_name' in st.session_state and 'client_name' in st.session_state:
                st.markdown("---")
                st.subheader("📤 Upload to Database")
                
                # Show what will be uploaded
                st.info(f"🏢 **Client:** {st.session_state['client_name']}")
                st.info(f"🔧 **Job:** {st.session_state['job_name']}")
                
                if st.button("🚀 Upload to Supabase", type="primary"):
                    with st.spinner("Uploading data to Supabase..."):
                        records_count, result = upload_to_supabase(
                            processed_data,
                            st.session_state['job_name'],
                            st.session_state['client_name']
                        )
                    
                    if records_count > 0:
                        st.success(f"✅ Successfully uploaded {records_count} records to database!")
                        
                        # Show breakdown of what was uploaded
                        uploaded_breakdown = []
                        if 'key_indicators' in processed_data:
                            uploaded_breakdown.append("1 overall project record (EVERYTHING)")
                        if 'breakdown' in processed_data:
                            breakdown_count = len(processed_data['breakdown'][~processed_data['breakdown']['System'].isin(['Revised Totals', 'Remainder', 'Final Price'])])
                            uploaded_breakdown.append(f"{breakdown_count} system breakdown records")
                        
                        if uploaded_breakdown:
                            st.info(f"📊 Uploaded: {', '.join(uploaded_breakdown)}")
                    else:
                        st.error("❌ No records uploaded. Please check your data.")
            
            elif not SUPABASE_CONFIGURED:
                st.markdown("---")
                st.subheader("📤 Database Upload")
                st.warning("⚠️ Supabase not configured. Please set your URL and API key in the code.")
            
            elif 'job_name' not in st.session_state or 'client_name' not in st.session_state:
                st.markdown("---")
                st.subheader("📤 Database Upload")
                st.info("💡 Process a file with client and job information to enable database upload.")
        
        else:
            # Welcome message when no data is loaded
            st.markdown("### 👋 Welcome to AccuBid Analysis")
            st.markdown("""
            Upload your AccuBid Excel file to get started with analyzing key project indicators.
            
            **What you can do:**
            - 📊 View Key Indicators in a formatted table
            - 📈 Analyze numeric values and totals  
            - 📥 Download processed data as CSV
            - 🔍 Validate AccuBid file structure
            
            **Getting Started:**
            1. Select your AccuBid Excel file using the upload area
            2. Ensure it contains a 'Key Indicators' sheet
            3. Review the processed data in the table
            4. Download or analyze the results
            """)

if __name__ == "__main__":
    main()
