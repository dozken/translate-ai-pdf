"""
Quick test script to validate Google API key.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GOOGLE_API_KEY', '').strip()

print(f'API Key found: {len(api_key) > 0}')
print(f'API Key length: {len(api_key)}')
if api_key:
    preview = f"****...{api_key[-4:]}" if len(api_key) > 4 else "****"
    print(f'API Key preview: {preview}')
else:
    print('❌ No API key found in environment')
    sys.exit(1)

# Test the API key
if api_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try to find an available model
        print('Checking available models...')
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name.replace('models/', '')
                    available_models.append(model_name)
                    print(f'  Found: {model_name}')
        except Exception as e:
            print(f'  Could not list models: {e}')
        
        # Try common model names in order of preference
        model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
        if available_models:
            # Use the first available model from our list
            model_name = None
            for name in model_names:
                if name in available_models:
                    model_name = name
                    break
            if not model_name and available_models:
                model_name = available_models[0]
        else:
            # Fallback to trying common names
            model_name = 'gemini-1.5-flash'
        
        if not model_name:
            print('❌ No suitable model found')
            sys.exit(1)
        
        print(f'\nUsing model: {model_name}')
        model = genai.GenerativeModel(model_name)
        
        # Try a simple test call
        response = model.generate_content('Say hello')
        
        if response and response.text:
            print('✅ API Key is VALID - Test successful!')
            print(f'Response: {response.text[:50]}...')
            sys.exit(0)
        else:
            print('❌ API Key test failed - Empty response')
            sys.exit(1)
            
    except ImportError as e:
        print(f'❌ Missing package: {str(e)}')
        print('💡 Install with: pip install google-generativeai')
        sys.exit(1)
    except Exception as e:
        print(f'❌ API Key test FAILED: {str(e)}')
        sys.exit(1)
