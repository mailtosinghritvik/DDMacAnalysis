"""
Perplexity AI Client for DDMac Analytics
Provides a clean interface for Perplexity AI API integration
"""

import os
import requests
import json
import tempfile
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class PerplexityClient:
    """Client for Perplexity AI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Perplexity client"""
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        
        # Allow client to work without API key for testing
        if not self.api_key:
            logger.warning("Perplexity API key not found. Running in test mode.")
            self.api_key = "test_key"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def is_configured(self) -> bool:
        """Return True if a real API key is configured (not test mode)."""
        return bool(self.api_key and self.api_key != "test_key")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = None,
                       max_tokens: int = 4000,
                       temperature: float = 0.7) -> Dict[str, Any]:
        """Send chat completion request to Perplexity"""
        
        # If in test mode, return mock response
        if self.api_key == "test_key":
            return {
                "choices": [{
                    "message": {
                        "content": "This is a test response from Perplexity AI. The actual API key is not configured."
                    }
                }]
            }
        
        url = f"{self.base_url}/chat/completions"

        # Choose model from env/arg with a simple default known to work on /chat/completions
        model_to_use = os.getenv("PERPLEXITY_MODEL") or model or "sonar"
        # Cap max tokens to a safe default to avoid 400s
        safe_max_tokens = min(max_tokens, 1024)

        payload = {
            "model": model_to_use,
            "messages": messages,
            "max_tokens": safe_max_tokens,
            "temperature": temperature,
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=60)
            if not response.ok:
                logger.error(f"Perplexity API error {response.status_code}: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            err_text = getattr(getattr(e, 'response', None), 'text', '') or ''
            logger.error(f"Perplexity API error: {e} {err_text}")
            raise
       
    def analyze_report_data(self, 
                           report_data: str, 
                           report_type: str = "analytics",
                           user_name: str = "User") -> str:
        """Analyze report data using Perplexity AI"""
        
        system_prompt = f"""You are a DDMac Analytics AI assistant specializing in {report_type} reports.

Your role:
- Analyze timesheet and project data
- Provide insights on productivity, efficiency, and performance
- Generate professional reports with actionable recommendations
- Focus on electrical estimation and construction project analytics

User: {user_name}
Report Type: {report_type}

Please analyze the following data and provide insights:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": report_data}
        ]
        
        try:
            response = self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error analyzing report data: {str(e)}")
            return f"Error analyzing data: {str(e)}"
    
    def generate_pdf_content(self, 
                           markdown_content: str, 
                           report_type: str = "analytics") -> str:
        """Generate enhanced PDF content using Perplexity AI"""
        
        system_prompt = f"""You are a DDMac Analytics AI assistant that creates professional PDF reports.

Your task:
- Take the provided markdown report content
- Enhance it with additional insights and analysis
- Format it for professional PDF generation
- Add executive summary and recommendations
- Maintain the original data integrity while improving presentation

Report Type: {report_type}

Please enhance the following markdown content for PDF generation:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": markdown_content}
        ]
        
        try:
            response = self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating PDF content: {str(e)}")
            return markdown_content  # Return original content if AI fails
    
    def chat_with_data(self, 
                      user_message: str, 
                      context_data: str = "",
                      conversation_history: List[Dict[str, str]] = None) -> str:
        """Chat with Perplexity AI about your data"""
        
        system_prompt = """You are a DDMac Analytics AI assistant. You help users understand their timesheet data, project analytics, and provide insights on:

- Employee productivity and performance
- Project progress and budget analysis
- Client time distribution and efficiency
- Team comparisons and rankings
- Data visualization recommendations
- Business intelligence insights

Be helpful, accurate, and provide actionable recommendations based on the data provided."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add context data if provided (truncate to avoid payload size errors)
        if context_data:
            # Limit context to a safe length to reduce 400 errors from oversized payloads
            max_context_chars = 12000
            trimmed_context = context_data if len(context_data) <= max_context_chars else context_data[:max_context_chars]
            messages.append({
                "role": "user", 
                "content": f"Context data:\n{trimmed_context}\n\nUser question: {user_message}"
            })
        else:
            messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def create_assistant(self, 
                        name: str, 
                        description: str, 
                        model: str = "sonar") -> Dict[str, Any]:
        """Create a Perplexity assistant (simplified for chat)"""
        
        # Perplexity doesn't have assistants like OpenAI, so we'll simulate it
        return {
            "id": f"perplexity_assistant_{hash(name)}",
            "name": name,
            "description": description,
            "model": model,
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    def create_thread(self) -> Dict[str, Any]:
        """Create a conversation thread (simplified)"""
        return {
            "id": f"thread_{hash(str(os.urandom(16)))}",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    def upload_file(self, file_path: str, purpose: str = "assistants") -> Dict[str, Any]:
        """Upload file to Perplexity (simplified - no actual upload needed)"""
        # Perplexity doesn't require file uploads like OpenAI
        # We'll just read the file content and return a mock file object
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Store the file content for later use in chat
            file_id = f"file_{hash(file_path)}_{hash(content)}"
            
            return {
                "id": file_id,
                "filename": os.path.basename(file_path),
                "purpose": purpose,
                "size": len(content),
                "created_at": "2024-01-01T00:00:00Z",
                "content": content  # Store content for later use
            }
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise

# Convenience functions for backward compatibility
def get_perplexity_client() -> PerplexityClient:
    """Get a Perplexity client instance"""
    return PerplexityClient()

def create_perplexity_assistant(name: str, description: str, model: str = "llama-3.1-sonar-large-128k-online") -> Dict[str, Any]:
    """Create a Perplexity assistant"""
    client = get_perplexity_client()
    return client.create_assistant(name, description, model)

def create_perplexity_thread() -> Dict[str, Any]:
    """Create a Perplexity thread"""
    client = get_perplexity_client()
    return client.create_thread()

def upload_file_to_perplexity(file_path: str, purpose: str = "assistants") -> Dict[str, Any]:
    """Upload file to Perplexity"""
    client = get_perplexity_client()
    return client.upload_file(file_path, purpose)

def send_perplexity_message(thread_id: str, message: str, file_ids: List[str] = None) -> Dict[str, Any]:
    """Send message to Perplexity thread"""
    client = get_perplexity_client()
    return client.chat_with_data(message)

def run_perplexity_thread(thread_id: str, assistant_id: str) -> Dict[str, Any]:
    """Run Perplexity thread"""
    # For Perplexity, this is just a pass-through since we don't have threads
    return {"status": "completed", "thread_id": thread_id, "assistant_id": assistant_id}
