import streamlit as st
import os
from openai import OpenAI
import pandas as pd
from datetime import datetime
import time

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page configuration
st.set_page_config(
    page_title="Chat - DDMac Analysis",
    page_icon="💬",
    layout="wide"
)

def initialize_chat():
    """Initialize chat session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = None
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

def create_assistant():
    """Create OpenAI assistant for data analysis"""
    try:
        assistant = client.beta.assistants.create(
            name="DDMac Data Analysis Assistant",
            instructions="""You are a helpful data analysis assistant. You help users understand their data, 
            perform analysis, and provide insights. You can help with:
            - Data exploration and summary statistics
            - Trend analysis and pattern recognition
            - Data visualization recommendations
            - Statistical analysis explanations
            - Business insights from data
            
            Always be helpful, clear, and provide actionable insights.""",
            model="gpt-4o-mini",
            tools=[{"type": "code_interpreter"}]
        )
        return assistant.id
    except Exception as e:
        st.error(f"Error creating assistant: {str(e)}")
        return None

def create_thread():
    """Create a new conversation thread"""
    try:
        thread = client.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"Error creating thread: {str(e)}")
        return None

def send_message(thread_id, message):
    """Send message to the assistant"""
    try:
        # Add message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=st.session_state.assistant_id
        )
        
        # Wait for completion
        while run.status in ['queued', 'in_progress']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            # Get messages
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            return messages.data[0].content[0].text.value
        else:
            return f"Error: Run completed with status {run.status}"
            
    except Exception as e:
        return f"Error sending message: {str(e)}"

def main():
    """Main chat function"""
    st.title("💬 AI Data Analysis Chat")
    st.markdown("Chat with AI to get insights about your data")
    
    # Initialize chat
    initialize_chat()
    
    # Sidebar for chat controls
    with st.sidebar:
        st.header("Chat Controls")
        
        # Create new assistant/thread
        if st.button("🚀 Start New Conversation"):
            with st.spinner("Creating AI assistant..."):
                assistant_id = create_assistant()
                if assistant_id:
                    st.session_state.assistant_id = assistant_id
                    thread_id = create_thread()
                    if thread_id:
                        st.session_state.thread_id = thread_id
                        st.session_state.messages = []
                        st.success("New conversation started!")
                        st.rerun()
        
        # Show current status
        if st.session_state.assistant_id and st.session_state.thread_id:
            st.success("✅ AI Assistant Ready")
        else:
            st.warning("⚠️ Please start a new conversation")
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.rerun()
        
        # Data info
        if 'uploaded_data' in st.session_state:
            st.header("📊 Current Data")
            df = st.session_state['uploaded_data']
            st.info(f"**File:** {st.session_state.get('file_name', 'Unknown')}")
            st.info(f"**Rows:** {len(df):,}")
            st.info(f"**Columns:** {len(df.columns)}")
        else:
            st.warning("No data uploaded. Upload data on the Home page to get data-specific insights.")
    
    # Main chat interface
    if not st.session_state.assistant_id or not st.session_state.thread_id:
        st.info("👆 Please start a new conversation using the sidebar to begin chatting with the AI assistant.")
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                # Add context about uploaded data if available
                context_prompt = prompt
                if 'uploaded_data' in st.session_state:
                    df = st.session_state['uploaded_data']
                    data_summary = f"""
                    Context: User has uploaded a dataset with {len(df)} rows and {len(df.columns)} columns.
                    Column names: {', '.join(df.columns.tolist())}
                    Data types: {df.dtypes.to_dict()}
                    
                    User question: {prompt}
                    """
                    context_prompt = data_summary
                
                response = send_message(st.session_state.thread_id, context_prompt)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Quick action buttons
    if 'uploaded_data' in st.session_state:
        st.subheader("🚀 Quick Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Summarize Data"):
                prompt = "Please provide a comprehensive summary of the uploaded dataset including key statistics, data types, and any notable patterns or insights."
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Analyzing data..."):
                    response = send_message(st.session_state.thread_id, prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col2:
            if st.button("🔍 Find Patterns"):
                prompt = "Analyze the data for patterns, trends, correlations, and anomalies. Provide actionable insights."
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Finding patterns..."):
                    response = send_message(st.session_state.thread_id, prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col3:
            if st.button("📈 Suggest Visualizations"):
                prompt = "Based on the data structure and content, suggest the most appropriate data visualizations and explain why they would be effective."
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Generating suggestions..."):
                    response = send_message(st.session_state.thread_id, prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

if __name__ == "__main__":
    main()
