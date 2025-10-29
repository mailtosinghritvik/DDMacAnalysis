#!/usr/bin/env python3
"""
Debug script to examine file annotation structures from OpenAI Assistant API
This will help identify the correct way to extract file IDs for downloads.
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
import json
import requests
import json

# Initialize OpenAI client
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

def debug_message_annotations(thread_id, message_id):
    """Debug a specific message to see its annotation structure"""
    try:
        # Get the message
        message = client.beta.threads.messages.retrieve(
            thread_id=thread_id,
            message_id=message_id
        )
        
        print(f"=== MESSAGE DEBUG ===")
        print(f"Message ID: {message_id}")
        print(f"Role: {message.role}")
        print(f"Content length: {len(message.content)}")
        
        # Check annotations in content
        for i, content_block in enumerate(message.content):
            print(f"\n--- Content Block {i} ---")
            print(f"Type: {content_block.type}")
            
            if hasattr(content_block, 'text'):
                text = content_block.text
                print(f"Text length: {len(text.value)}")
                print(f"Annotations count: {len(text.annotations)}")
                
                # Debug each annotation
                for j, annotation in enumerate(text.annotations):
                    print(f"\n  Annotation {j}:")
                    print(f"  Type: {annotation.type}")
                    print(f"  Text: {annotation.text}")
                    
                    if hasattr(annotation, 'file_path'):
                        file_path = annotation.file_path
                        print(f"  File Path ID: {file_path.file_id}")
                        
                        # Try to get file info
                        try:
                            file_obj = client.files.retrieve(file_path.file_id)
                            print(f"  File Name: {file_obj.filename}")
                            print(f"  File Size: {file_obj.bytes}")
                            print(f"  File Purpose: {file_obj.purpose}")
                        except Exception as e:
                            print(f"  Error getting file info: {e}")
                    
                    # Print full annotation structure
                    print(f"  Full annotation dict: {annotation.__dict__}")
        
        return True
        
    except Exception as e:
        print(f"Error debugging message: {e}")
        return False

def examine_file_structure():
    """Create a simple test to see how files are structured in annotations"""
    try:
        # Create a simple assistant with code interpreter
        assistant = create_perplexity_assistant(
            name="File Debug Assistant",
            description="Assistant for debugging file annotations",
            model="gpt-4o",
            tools=[{"type": "code_interpreter"}]
        )
        
        # Create a thread
        thread = create_perplexity_thread()
        
        # Add a message asking for a simple file
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Create a simple text file with the content 'Hello World' and save it as test.txt"
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        # Wait for completion (simple polling)
        import time
        max_wait = 30
        waited = 0
        while waited < max_wait:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                print(f"Run failed with status: {run_status.status}")
                return False
            
            time.sleep(2)
            waited += 2
        
        # Get all messages to find the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        print(f"=== THREAD ANALYSIS ===")
        print(f"Thread ID: {thread.id}")
        print(f"Assistant ID: {assistant.id}")
        print(f"Run ID: {run.id}")
        print(f"Run Status: {run_status.status}")
        print(f"Total messages: {len(messages.data)}")
        
        # Examine each message
        for i, msg in enumerate(messages.data):
            print(f"\n--- Message {i} ---")
            print(f"ID: {msg.id}")
            print(f"Role: {msg.role}")
            print(f"Created: {msg.created_at}")
            
            if msg.role == 'assistant':
                # This should be the response with potential file
                debug_message_annotations(thread.id, msg.id)
        
        # Clean up
        try:
            client.beta.assistants.delete(assistant.id)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"Error in file structure examination: {e}")
        return False

def compare_processing_methods():
    """Compare the two different ways of processing files"""
    
    # Simulate different file annotation structures
    test_structures = [
        # Structure 1: Home.py style (file_info with file_id key)
        {
            "name": "Home.py style",
            "files": [
                {"file_id": "file-123abc", "filename": "test.pdf"},
                {"file_id": "file-456def", "filename": "report.pdf"}
            ]
        },
        
        # Structure 2: EmailReportWriter.py style (direct file_id)
        {
            "name": "EmailReportWriter.py style",
            "files": ["file-123abc", "file-456def"]
        },
        
        # Structure 3: Mixed/Complex
        {
            "name": "Complex structure",
            "files": [
                {"file_id": "file-789ghi", "filename": "complex.pdf", "type": "pdf"},
                "file-101jkl"  # Mixed structure
            ]
        }
    ]
    
    print("=== PROCESSING METHOD COMPARISON ===")
    
    for structure in test_structures:
        print(f"\n--- Testing {structure['name']} ---")
        files = structure['files']
        print(f"Raw files data: {files}")
        
        # Try Home.py method
        print("\nHome.py method:")
        try:
            for file_info in files:
                if isinstance(file_info, dict) and 'file_id' in file_info:
                    file_id = file_info['file_id']
                    print(f"  Extracted file_id: {file_id}")
                else:
                    print(f"  Error: Expected dict with file_id, got: {type(file_info)} -> {file_info}")
        except Exception as e:
            print(f"  Home.py method failed: {e}")
        
        # Try EmailReportWriter.py method
        print("\nEmailReportWriter.py method:")
        try:
            for file_id in files:
                if isinstance(file_id, str):
                    print(f"  Using file_id: {file_id}")
                else:
                    print(f"  Error: Expected string file_id, got: {type(file_id)} -> {file_id}")
        except Exception as e:
            print(f"  EmailReportWriter.py method failed: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    print("🔍 DEBUG: File Annotation Structure Analysis")
    print("=" * 60)
    
    # Test 1: Compare processing methods
    print("\n1. Testing processing methods with sample data:")
    compare_processing_methods()
    
    # Test 2: Real API test (if OpenAI key is available)
    if os.getenv("OPENAI_API_KEY"):
        print("\n2. Testing with real OpenAI API:")
        examine_file_structure()
    else:
        print("\n2. Skipping real API test (no OpenAI key)")
    
    print("\n" + "=" * 60)
    print("✅ Debug analysis complete!")