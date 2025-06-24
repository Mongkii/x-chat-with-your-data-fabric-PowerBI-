import os
from typing import Optional
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        # Simple initialization without proxies
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def get_response(self, message: str, context: Optional[str] = None) -> str:
        """Get response from Claude"""
        try:
            # Build the prompt
            prompt = message
            if context:
                prompt = f"Context: {context}\n\nUser Question: {message}"
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the text response
            return response.content[0].text
            
        except Exception as e:
            return f"Error: {str(e)}"

# Try to create instance
try:
    claude_service = ClaudeService()
except Exception as e:
    print(f"Could not initialize Claude service: {e}")
    claude_service = None