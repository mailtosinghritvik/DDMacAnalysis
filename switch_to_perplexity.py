#!/usr/bin/env python3
"""
Switch from OpenAI to Perplexity AI
This script updates all OpenAI references to use Perplexity AI instead
"""

import os
import re
from pathlib import Path

def update_file_for_perplexity(file_path):
    """Update a file to use Perplexity AI instead of OpenAI"""
    
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace OpenAI imports
        content = re.sub(
            r'from openai import OpenAI',
            'import requests\nimport json',
            content
        )
        
        # Replace OpenAI client initialization
        content = re.sub(
            r'client = OpenAI\(api_key=os\.getenv\("OPENAI_API_KEY"\)\)',
            'PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")\nPERPLEXITY_BASE_URL = "https://api.perplexity.ai"',
            content
        )
        
        # Replace OpenAI API calls with Perplexity API calls
        content = re.sub(
            r'client\.beta\.assistants\.create\(',
            'create_perplexity_assistant(',
            content
        )
        
        content = re.sub(
            r'client\.beta\.threads\.create\(',
            'create_perplexity_thread(',
            content
        )
        
        content = re.sub(
            r'client\.files\.create\(',
            'upload_file_to_perplexity(',
            content
        )
        
        # Add Perplexity helper functions at the top
        if 'def create_perplexity_assistant(' not in content:
            perplexity_helpers = '''
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

'''
            
            # Insert the helper functions after imports
            import_end = content.find('\n\n')
            if import_end == -1:
                import_end = content.find('\n')
            if import_end != -1:
                content = content[:import_end] + perplexity_helpers + content[import_end:]
        
        # Update return statements to work with Perplexity response format
        content = re.sub(
            r'return assistant\.id, thread\.id, file_obj\.id',
            'return assistant["id"], thread["id"], file_obj["id"]',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed: {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {str(e)}")
        return False

def update_requirements():
    """Update requirements.txt to include Perplexity dependencies"""
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"⚠️  Requirements file not found: {requirements_file}")
        return False
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove OpenAI if present
        content = re.sub(r'openai==.*\n', '', content)
        
        # Add Perplexity dependencies
        if 'requests' not in content:
            content += '\n# AI API integration\nrequests==2.32.3\n'
        
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated requirements.txt")
        return True
        
    except Exception as e:
        print(f"❌ Error updating requirements.txt: {str(e)}")
        return False

def update_secrets():
    """Update secrets.toml to use Perplexity API key"""
    
    secrets_file = ".streamlit/secrets.toml"
    
    try:
        if os.path.exists(secrets_file):
            with open(secrets_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""
        
        # Replace OpenAI section with Perplexity
        content = re.sub(
            r'\[openai\].*?api_key = ".*?"',
            '[perplexity]\napi_key = "your-perplexity-api-key-here"',
            content,
            flags=re.DOTALL
        )
        
        if '[perplexity]' not in content:
            content += '\n[perplexity]\napi_key = "your-perplexity-api-key-here"\n'
        
        with open(secrets_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated .streamlit/secrets.toml")
        return True
        
    except Exception as e:
        print(f"❌ Error updating secrets.toml: {str(e)}")
        return False

def main():
    """Main function to switch to Perplexity AI"""
    
    print("🚀 Switching from OpenAI to Perplexity AI")
    print("=" * 50)
    
    # Files to update
    files_to_update = [
        "pages/Chat.py",
        "pages/EmailReportWriter.py",
        "debug_assistant.py",
        "debug_file_annotations.py"
    ]
    
    success_count = 0
    
    # Update each file
    for file_path in files_to_update:
        if update_file_for_perplexity(file_path):
            success_count += 1
    
    # Update requirements and secrets
    if update_requirements():
        success_count += 1
    
    if update_secrets():
        success_count += 1
    
    print(f"\n📊 Results: {success_count}/{len(files_to_update) + 2} files updated successfully")
    
    if success_count == len(files_to_update) + 2:
        print("\n🎉 Successfully switched to Perplexity AI!")
        print("\n📋 Next Steps:")
        print("1. Get your Perplexity API key from https://www.perplexity.ai/settings/api")
        print("2. Update .streamlit/secrets.toml with your actual API key")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Test the application")
    else:
        print("\n⚠️  Some files may need manual updates")

if __name__ == "__main__":
    main()
