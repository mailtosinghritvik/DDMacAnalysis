import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# Set page configuration
st.set_page_config(
    page_title="Foreman Analysis - DDMac",
    page_icon="👷",
    layout="wide"
)

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom CSS
st.markdown("""
<style>
    .foreman-header {
        background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .insert-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #ff6b35;
        margin: 1rem 0;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_jobcodes_data():
    """Fetch jobcodes data from Supabase"""
    try:
        result = supabase.table('jobcodes').select('id, name').execute()
        if result.data:
            return pd.DataFrame(result.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching jobcodes: {str(e)}")
        return pd.DataFrame()

def get_projects_data():
    """Fetch projects data from Supabase"""
    try:
        result = supabase.table('projects').select('id, name').execute()
        if result.data:
            return pd.DataFrame(result.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching projects: {str(e)}")
        return pd.DataFrame()

def get_tasks_data():
    """Fetch tasks data from accubid_breakdowns table"""
    try:
        result = supabase.table('accubid_breakdowns').select('id, task_name, job_name').execute()
        if result.data:
            return pd.DataFrame(result.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
        return pd.DataFrame()

def insert_jobcode_progress(project_id, jobcode_id, progress):
    """Insert jobcode progress into project_progress table"""
    try:
        # Validate progress value (0-100)
        if not (0 <= progress <= 100):
            st.error("Progress must be between 0 and 100")
            return False

        # Check if progress is going backward
        last_progress = get_last_jobcode_progress(project_id, jobcode_id)
        if progress < last_progress:
            st.error(f"❌ Cannot go backward! Last progress was {last_progress}%. You can only move forward.")
            return False
        
        # At least one ID must be provided
        if not project_id and not jobcode_id:
            st.error("Please select either a project or jobcode")
            return False
        
        # Insert data
        data = {
            'progress': progress,
            'created_at': datetime.now().isoformat()
        }
        
        # Add project_id if provided
        if project_id:
            data['project_id'] = project_id
        
        # Add jobcode_id if provided
        if jobcode_id:
            data['jobcode_id'] = jobcode_id
        
        result = supabase.table('project_progress').insert(data).execute()
        
        if result.data:
            st.success(f"✅ Progress inserted successfully!")
            if project_id and jobcode_id:
                st.success(f"Project ID: {project_id}, Jobcode ID: {jobcode_id}, Progress: {progress}%")
            elif project_id:
                st.success(f"Project ID: {project_id}, Progress: {progress}%")
            elif jobcode_id:
                st.success(f"Jobcode ID: {jobcode_id}, Progress: {progress}%")
            return True
        else:
            st.error("❌ Failed to insert progress")
            return False
            
    except Exception as e:
        st.error(f"❌ Error inserting progress: {str(e)}")
        return False

def insert_task_progress(task_id, progress):
    """Insert task progress into task_progress table"""
    try:
        # Validate progress value (0-100)
        if not (0 <= progress <= 100):
            st.error("Progress must be between 0 and 100")
            return False
        
        # Check if progress is going backward
        last_progress = get_last_task_progress(task_id)
        if progress < last_progress:
            st.error(f"❌ Cannot go backward! Last progress was {last_progress}%. You can only move forward.")
            return False
        
        # Insert data
        data = {
            'task_id': task_id,
            'progress': progress,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('task_progress').insert(data).execute()
        
        if result.data:
            st.success(f"✅ Task progress inserted successfully!")
            st.success(f"Task ID: {task_id}, Progress: {progress}%")
            return True
        else:
            st.error("❌ Failed to insert task progress")
            return False
            
    except Exception as e:
        st.error(f"❌ Error inserting task progress: {str(e)}")
        return False

def get_last_jobcode_progress(project_id=None, jobcode_id=None):
    """Get the last inserted progress value for project/jobcode"""
    try:
        query = supabase.table('project_progress').select('progress, created_at')
        
        # Add filters based on provided IDs
        if project_id and jobcode_id:
            query = query.eq('project_id', project_id).eq('jobcode_id', jobcode_id)
        elif project_id:
            query = query.eq('project_id', project_id).is_('jobcode_id', 'null')
        elif jobcode_id:
            query = query.is_('project_id', 'null').eq('jobcode_id', jobcode_id)
        else:
            return 0  # No IDs provided, return 0 as default
        
        # Order by created_at descending and limit to 1
        result = query.order('created_at', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['progress']
        else:
            return 0  # No previous progress found
            
    except Exception as e:
        st.warning(f"Could not fetch last progress: {str(e)}")
        return 0

def get_last_task_progress(task_id):
    """Get the last inserted progress value for a task"""
    try:
        if not task_id:
            return 0
            
        result = supabase.table('task_progress').select('progress, created_at').eq('task_id', task_id).order('created_at', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['progress']
        else:
            return 0  # No previous progress found
            
    except Exception as e:
        st.warning(f"Could not fetch last task progress: {str(e)}")
        return 0

def main():
    """Main Foreman Analysis Dashboard"""
    
    # Header
    st.markdown("""
    <div class="foreman-header">
        <h1>👷 Foreman Analysis - Progress Tracking</h1>
        <p>Insert Progress Data - Project ID OR Jobcode ID (Optional)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2 = st.tabs([
        "🏗️ Jobcode Progress Insert",
        "📋 Task Progress Insert"
    ])
    
    with tab1:
        st.markdown('<div class="insert-card">', unsafe_allow_html=True)
        st.subheader("🏗️ Insert Progress Data")
        st.write("Insert progress data into the project_progress table. You can select either a Project ID, Jobcode ID, or both.")
        
        # Load data
        with st.spinner("Loading jobcodes and projects..."):
            jobcodes_df = get_jobcodes_data()
            projects_df = get_projects_data()
        
        if jobcodes_df.empty and projects_df.empty:
            st.error("No jobcodes or projects found. Please check your database.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                # Project selection (optional)
                if not projects_df.empty:
                    project_options = {"None": None}
                    project_options.update({f"{row['name']} (ID: {row['id']})": row['id'] for _, row in projects_df.iterrows()})
                    selected_project = st.selectbox(
                        "Select Project (Optional):",
                        options=list(project_options.keys()),
                        key="project_selector"
                    )
                    project_id = project_options[selected_project] if selected_project else None
                else:
                    st.info("No projects available")
                    project_id = None
            
            with col2:
                # Jobcode selection (optional)
                if not jobcodes_df.empty:
                    jobcode_options = {"None": None}
                    jobcode_options.update({f"{row['name']} (ID: {row['id']})": row['id'] for _, row in jobcodes_df.iterrows()})
                    selected_jobcode = st.selectbox(
                        "Select Jobcode (Optional):",
                        options=list(jobcode_options.keys()),
                        key="jobcode_selector"
                    )
                    jobcode_id = jobcode_options[selected_jobcode] if selected_jobcode else None
                else:
                    st.info("No jobcodes available")
                    jobcode_id = None
            
            # Progress input
            st.subheader("Progress Input")
            
            # Get last progress value to set as minimum
            last_progress = int(get_last_jobcode_progress(project_id, jobcode_id) or 0)
            
            # Ensure slider value updates when project/jobcode selection changes
            current_jobcode_context = (project_id, jobcode_id)
            prev_jobcode_context = st.session_state.get("jobcode_prev_context")
            if prev_jobcode_context != current_jobcode_context:
                st.session_state["jobcode_prev_context"] = current_jobcode_context
                st.session_state["jobcode_progress_slider"] = last_progress
            elif "jobcode_progress_slider" not in st.session_state:
                st.session_state["jobcode_progress_slider"] = last_progress
            
            progress = st.slider(
                "Progress Percentage:",
                min_value=last_progress,
                max_value=100,
                value=st.session_state.get("jobcode_progress_slider", last_progress),
                key="jobcode_progress_slider"
            )
            
            # Insert button
            if st.button("Insert Progress", type="primary", key="insert_jobcode_btn"):
                insert_jobcode_progress(project_id, jobcode_id, progress)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="insert-card">', unsafe_allow_html=True)
        st.subheader("📋 Insert Task Progress")
        st.write("Insert progress data for tasks into the task_progress table. Select a job name first, then choose a task from that job.")
        
        # Load data
        with st.spinner("Loading tasks..."):
            tasks_df = get_tasks_data()
        
        if tasks_df.empty:
            st.error("No tasks found. Please check your database.")
        else:
            # Group tasks by job name
            if 'job_name' in tasks_df.columns:
                # Create job name selection first
                job_names = tasks_df['job_name'].dropna().unique()
                if len(job_names) > 0:
                    selected_job = st.selectbox(
                        "Select Job Name:",
                        options=job_names,
                        key="job_selector"
                    )
                    
                    # Filter tasks by selected job
                    filtered_tasks = tasks_df[tasks_df['job_name'] == selected_job]
                    
                    if not filtered_tasks.empty:
                        # Task selection for the selected job
                        task_options = {f"{row['task_name']} (ID: {row['id']})": row['id'] for _, row in filtered_tasks.iterrows()}
                        selected_task = st.selectbox(
                            f"Select Task for '{selected_job}':",
                            options=list(task_options.keys()),
                            key="task_selector"
                        )
                        task_id = task_options[selected_task] if selected_task else None
                    else:
                        st.warning(f"No tasks found for job: {selected_job}")
                        task_id = None
                else:
                    st.warning("No job names found in the data")
                    # Fallback to original task selection
                    task_options = {f"{row['task_name']} (ID: {row['id']})": row['id'] for _, row in tasks_df.iterrows()}
                    selected_task = st.selectbox(
                        "Select Task:",
                        options=list(task_options.keys()),
                        key="task_selector"
                    )
                    task_id = task_options[selected_task] if selected_task else None
            else:
                st.warning("No job_name column found. Showing all tasks.")
                # Fallback to original task selection
                task_options = {f"{row['task_name']} (ID: {row['id']})": row['id'] for _, row in tasks_df.iterrows()}
                selected_task = st.selectbox(
                    "Select Task:",
                    options=list(task_options.keys()),
                    key="task_selector"
                )
                task_id = task_options[selected_task] if selected_task else None
            
            # Progress input
            st.subheader("Progress Input")
            
            # Get last progress value to set as minimum
            last_task_progress = int(get_last_task_progress(task_id) or 0)
            
            # Ensure slider value updates when task selection changes
            prev_task_id = st.session_state.get("task_prev_id")
            if prev_task_id != task_id:
                st.session_state["task_prev_id"] = task_id
                st.session_state["task_progress_slider"] = last_task_progress
            elif "task_progress_slider" not in st.session_state:
                st.session_state["task_progress_slider"] = last_task_progress
            
            progress = st.slider(
                "Progress Percentage:",
                min_value=last_task_progress,
                max_value=100,
                value=st.session_state.get("task_progress_slider", last_task_progress),
                key="task_progress_slider"
            )
            
            # Insert button
            if st.button("Insert Task Progress", type="primary", key="insert_task_btn"):
                if task_id is not None:
                    insert_task_progress(task_id, progress)
                else:
                    st.error("Please select a task")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.caption("**Foreman Analysis** | Progress Insert Tool | DDMac Analytics")

if __name__ == "__main__":
    main()