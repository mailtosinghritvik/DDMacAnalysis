#!/usr/bin/env python3
"""
Diagnostic script to test assistant creation and identify issues
"""
def create_perplexity_assistant(name, description, model="llama-3.1-sonar-large-128k-online", tools=None):
    """Create a Perplexity assistant"""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": name,
        "description": description,
        "model": model,
        "tools": tools or []
    }
    
    response = requests.post(f"{PERPLEXITY_BASE_URL}/assistants", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to create assistant: {response.text}")

def create_perplexity_thread():
    """Create a Perplexity thread"""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {"messages": []}
    
    response = requests.post(f"{PERPLEXITY_BASE_URL}/threads", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to create thread: {response.text}")

def upload_file_to_perplexity(file_path, purpose="assistants"):
    """Upload file to Perplexity"""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}"
    }
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"purpose": purpose}
        
        response = requests.post(f"{PERPLEXITY_BASE_URL}/files", headers=headers, files=files, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to upload file: {response.text}")

def send_perplexity_message(thread_id, message, file_ids=None):
    """Send message to Perplexity thread"""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "role": "user",
        "content": message
    }
    
    if file_ids:
        data["file_ids"] = file_ids
    
    response = requests.post(f"{PERPLEXITY_BASE_URL}/threads/{thread_id}/messages", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to send message: {response.text}")

def run_perplexity_thread(thread_id, assistant_id):
    """Run Perplexity thread"""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "assistant_id": assistant_id,
        "thread_id": thread_id
    }
    
    response = requests.post(f"{PERPLEXITY_BASE_URL}/threads/{thread_id}/runs", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to run thread: {response.text}")



import os
import tempfile
import requests
import json
import time

# Initialize OpenAI client
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

def test_assistant_creation_home_style():
    """Test assistant creation using Home.py style (with Excel file)"""
    print("\n=== Testing Home.py Style Assistant Creation ===")
    
    try:
        # Create a dummy Excel-like file
        test_content = "Test,Data\n1,2\n3,4"
        temp_path = os.path.join(tempfile.gettempdir(), "test_excel.csv")
        
        with open(temp_path, "w") as f:
            f.write(test_content)
        
        print(f"✅ Created test file: {temp_path}")
        
        # Upload file to Perplexity
        file_obj = upload_file_to_perplexity(
            file_path=temp_path,
            purpose='assistants'
        )
        
        print(f"✅ File uploaded to Perplexity: {file_obj['id']}")
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Create assistant (Home.py style)
        assistant_name = "Test DDMac Bot - Debug Assistant"
        assistant_description = """DDMac Bot expert for electrical estimation analysis.

Project: Test Project | Company: Test Company | Type: Commercial

Analyzes Excel data for costs, materials, labor, timelines. Uses code interpreter for calculations and data analysis."""
        
        assistant = create_perplexity_assistant(
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
        
        print(f"✅ Assistant created successfully: {assistant.id}")
        
        # Create thread
        thread = create_perplexity_thread()
        print(f"✅ Thread created successfully: {thread.id}")
        
        # Test a simple message
        print("\n--- Testing simple message ---")
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Hello, can you analyze the uploaded file?"
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        print(f"✅ Run created: {run.id}")
        print(f"Initial status: {run.status}")
        
        # Wait for completion
        wait_count = 0
        while run.status in ['queued', 'in_progress'] and wait_count < 60:
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            wait_count += 1
            print(f"Status after {wait_count*2}s: {run.status}")
        
        print(f"Final status: {run.status}")
        
        if run.status == 'failed':
            print(f"❌ Run failed. Last error: {getattr(run, 'last_error', 'No error details')}")
            return False
        elif run.status == 'completed':
            print("✅ Home.py style assistant works perfectly!")
            return True
        else:
            print(f"⚠️ Unexpected status: {run.status}")
            return False
            
    except Exception as e:
        print(f"❌ Error in Home.py style test: {str(e)}")
        return False

def test_assistant_creation_email_style():
    """Test assistant creation using EmailReportWriter.py style (with markdown file)"""
    print("\n=== Testing EmailReportWriter.py Style Assistant Creation ===")
    
    try:
        # Create a markdown file (as our code does)
        markdown_content = """# Test Report

## Summary
This is a test analytics report with some data.

### Key Metrics
- Total users: 100
- Revenue: $50,000
- Growth: 25%

## Analysis
The data shows positive trends across all metrics.
"""
        
        temp_path = os.path.join(tempfile.gettempdir(), "test_report.md")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"✅ Created test markdown file: {temp_path}")
        
        # Upload markdown file to Perplexity
        file_obj = upload_file_to_perplexity(
            file_path=temp_path,
            purpose='assistants'
        )
        
        print(f"✅ Markdown file uploaded to Perplexity: {file_obj['id']}")
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Create Assistant with comprehensive system prompt (our style)
        system_prompt = """You are a professional report analyst and PDF generator specializing in analytics reports.

Your primary task is to:
1. Analyze the provided markdown report data thoroughly
2. Create a comprehensive, professional PDF report with:
   - Executive summary
   - Key insights and trends
   - Data visualizations (charts, graphs) where applicable
   - Detailed analysis sections
   - Recommendations and conclusions
   - Professional formatting with headers, tables, and visual elements

3. Generate Python code to create the PDF using libraries like matplotlib, reportlab, or similar
4. Ensure the PDF is well-structured, visually appealing, and business-ready
5. Save the PDF file for download

Report Type: User Report
Report Name: Test Analytics Report

Use your code interpreter to analyze the data and create a professional PDF report. Focus on making it comprehensive and visually appealing for business stakeholders."""

        assistant = create_perplexity_assistant(
            name="AI Report Generator - Test Analytics Report",
            description="Dedicated assistant for generating comprehensive PDF reports from analytics data",
            model="gpt-4o",
            instructions=system_prompt,
            tools=[{"type": "code_interpreter"}],
            tool_resources={
                "code_interpreter": {
                    "file_ids": [file_obj.id]
                }
            }
        )
        
        print(f"✅ Assistant created successfully: {assistant.id}")
        
        # Create thread
        thread = create_perplexity_thread()
        print(f"✅ Thread created successfully: {thread.id}")
        
        # Test the complex message that fails
        print("\n--- Testing complex PDF generation message ---")
        complex_message = "Please analyze the user report data provided and create a comprehensive, professional PDF report. Include executive summary, key insights, data visualizations, detailed analysis, and recommendations. Make it business-ready and visually appealing."
        
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=complex_message
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        print(f"✅ Run created: {run.id}")
        print(f"Initial status: {run.status}")
        
        # Wait for completion
        wait_count = 0
        while run.status in ['queued', 'in_progress'] and wait_count < 60:
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            wait_count += 1
            print(f"Status after {wait_count*2}s: {run.status}")
        
        print(f"Final status: {run.status}")
        
        if run.status == 'failed':
            print(f"❌ Run failed. Last error: {getattr(run, 'last_error', 'No error details')}")
            
            # Try to get more details
            try:
                run_details = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if hasattr(run_details, 'last_error') and run_details.last_error:
                    print(f"Error code: {run_details.last_error.code}")
                    print(f"Error message: {run_details.last_error.message}")
            except Exception as e:
                print(f"Could not get error details: {e}")
            
            return False
        elif run.status == 'completed':
            print("✅ EmailReportWriter.py style assistant works!")
            return True
        else:
            print(f"⚠️ Unexpected status: {run.status}")
            return False
            
    except Exception as e:
        print(f"❌ Error in EmailReportWriter.py style test: {str(e)}")
        return False

def test_simple_assistant():
    """Test a very simple assistant without complex instructions"""
    print("\n=== Testing Simple Assistant (Baseline) ===")
    
    try:
        # Create simple assistant
        assistant = create_perplexity_assistant(
            name="Simple Test Assistant",
            description="A simple test assistant",
            model="gpt-4o",
            tools=[{"type": "code_interpreter"}]
        )
        
        print(f"✅ Simple assistant created: {assistant.id}")
        
        # Create thread
        thread = create_perplexity_thread()
        print(f"✅ Thread created: {thread.id}")
        
        # Test simple message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Hello, can you help me with a simple calculation? What is 2+2?"
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        print(f"✅ Run created: {run.id}")
        
        # Wait for completion
        wait_count = 0
        while run.status in ['queued', 'in_progress'] and wait_count < 30:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            wait_count += 1
            print(f"Status after {wait_count}s: {run.status}")
        
        print(f"Final status: {run.status}")
        
        if run.status == 'completed':
            print("✅ Simple assistant works perfectly!")
            return True
        else:
            print(f"❌ Simple assistant failed with status: {run.status}")
            return False
            
    except Exception as e:
        print(f"❌ Error in simple assistant test: {str(e)}")
        return False

def main():
    print("🔍 OpenAI Assistant Diagnostic Script")
    print("=====================================")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found!")
        return
    
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    # Run tests
    results = {}
    
    results['simple'] = test_simple_assistant()
    results['home_style'] = test_assistant_creation_home_style()
    results['email_style'] = test_assistant_creation_email_style()
    
    # Summary
    print("\n🏁 DIAGNOSTIC SUMMARY")
    print("====================")
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    if not results['email_style'] and results['home_style']:
        print("\n💡 RECOMMENDATION: Use Home.py assistant creation pattern")
    elif not results['email_style'] and not results['home_style'] and results['simple']:
        print("\n💡 RECOMMENDATION: Issue with complex instructions or file handling")
    elif not any(results.values()):
        print("\n💡 RECOMMENDATION: Check OpenAI API permissions and quota")

if __name__ == "__main__":
    main()