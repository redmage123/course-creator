#!/usr/bin/env python3
"""
Test script to verify the Anthropic API key from .cc_env file
"""
import os
import sys
import anthropic
from dotenv import load_dotenv

def test_api_key():
    """Test the Anthropic API key with a simple call"""
    
    # Load environment variables from .cc_env file in current directory
    env_file = os.path.join(os.getcwd(), '.cc_env')
    print(f"Looking for .cc_env file at: {env_file}")
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print("✅ .cc_env file found and loaded")
        
        # Debug: Check what's in the file
        with open(env_file, 'r') as f:
            lines = f.readlines()
            print("File lines:")
            for i, line in enumerate(lines):
                if 'ANTHROPIC' in line:
                    print(f"  Line {i+1}: {line.strip()}")
                    # Extract API key directly from the line
                    if '=' in line and 'ANTHROPIC_API_KEY' in line:
                        key_value = line.split('=', 1)[1].strip()
                        # Remove quotes if present
                        key_value = key_value.strip('"\'')
                        print(f"  Extracted key: {key_value[:20]}...")
            
    else:
        print("❌ .cc_env file not found")
        return False
    
    # Get API key from environment or extract directly from file
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # If not found in environment, extract directly from file
    if not api_key:
        print("Environment variable not set, extracting from file...")
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip().startswith('ANTHROPIC_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    # Remove quotes if present
                    api_key = api_key.strip('"\'')
                    print(f"✅ API key extracted from file: {api_key[:20]}...")
                    break
    
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Make sure the .cc_env file exists and contains the API key")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    try:
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)
        
        print("🔄 Testing API connection...")
        
        # Make a simple test call
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hello! Please respond with 'API test successful' to confirm the connection is working."}
            ]
        )
        
        # Get response text
        response_text = response.content[0].text
        
        print(f"✅ API Response: {response_text}")
        
        if "API test successful" in response_text or "successful" in response_text.lower():
            print("🎉 API KEY TEST PASSED - Connection is working!")
            return True
        else:
            print("⚠️  API responded but with unexpected content")
            return True  # Still a successful connection
            
    except anthropic.AuthenticationError as e:
        print(f"❌ AUTHENTICATION ERROR: {e}")
        print("The API key is invalid or expired")
        return False
        
    except anthropic.APIError as e:
        print(f"❌ API ERROR: {e}")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Anthropic API Key from .cc_env file")
    print("=" * 50)
    
    success = test_api_key()
    
    if success:
        print("\n✅ API key test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ API key test failed!")
        sys.exit(1)