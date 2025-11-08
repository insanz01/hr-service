#!/usr/bin/env python3
"""
Direct test of Gemini API without instructor to isolate the issue
"""
import os
import json

# Set environment variable
os.environ.setdefault("GEMINI_API_KEY", "AIzaSyCRtkNwIKFirwnxziwijEx-3lVUOVknjaY")

def test_direct_gemini():
    """Test Gemini API directly without instructor"""
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found")
            return False

        print(f"🔑 Using API key: {api_key[:20]}...")

        # Configure with API key
        genai.configure(api_key=api_key)

        # List available models
        print("\n📋 Available models:")
        try:
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"  ✅ {model.name}")
        except Exception as e:
            print(f"❌ Failed to list models: {e}")

        # Test with different models
        models_to_test = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
            "models/gemini-flash-latest",
            "models/gemini-1.5-flash-latest"
        ]

        for model_name in models_to_test:
            print(f"\n🧪 Testing model: {model_name}")
            try:
                model = genai.GenerativeModel(model_name)

                # Simple test
                response = model.generate_content("Hello, respond with 'OK'")
                print(f"✅ {model_name}: {response.text}")

                # JSON test
                json_response = model.generate_content(
                    'Respond with valid JSON: {"score": 0.8, "feedback": "test"}'
                )
                print(f"✅ {model_name} JSON: {json_response.text}")

                return True  # Success with first working model

            except Exception as e:
                print(f"❌ {model_name} failed: {e}")

    except ImportError as e:
        print(f"❌ Failed to import google.generativeai: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return False

if __name__ == "__main__":
    print("🔍 Testing Gemini API directly...")
    success = test_direct_gemini()
    print(f"\n📊 Test result: {'SUCCESS' if success else 'FAILED'}")