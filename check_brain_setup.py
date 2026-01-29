
import os
from dotenv import load_dotenv
# 라이브러리 임포트 시도
try:
    import google.genai as genai
    print("✅ Library [google.genai] imported.")
except ImportError:
    print("❌ Library [google.genai] NOT found.")
    exit()

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("-" * 30)
if not api_key or "your_api_key" in api_key:
    print("❌ API Key is MISSING or Default.")
    exit()

print(f"🔑 Key found: {api_key[:10]}... (Looks Good)")
print("🧠 Sending signal to Google Brain...")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp", 
        contents="Are you alive?"
    )
    print(f"🎉 SUCCESS! Response: {response.text}")
except Exception as e:
    print(f"💀 Connection FAILED. Error:\n{e}")

