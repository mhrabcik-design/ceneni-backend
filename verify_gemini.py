import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ API Key not found in .env")
    exit(1)

print(f"🔑 Key found: {api_key[:5]}...{api_key[-3:]}")
genai.configure(api_key=api_key)

print("📡 Connecting to Google AI...")
try:
    models = genai.list_models()
    print("✅ Connection Successful! Available models:")
    found = False
    for m in models:
        if 'gemini' in m.name:
            print(f"   - {m.name}")
            found = True
    if not found:
        print("   (No 'gemini' models found in list)")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
