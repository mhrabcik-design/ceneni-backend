import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Fix imports: Add 'backend' to sys.path so 'database' and 'services' modules are found
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from services.data_manager import DataManager

# Setup
INPUT_DIRS = [
    r"Input\01_Nabidky_PDF",
    r"Input\02_Historie_Excel"
]

def main():
    print("🚀 Starting Batch Import...")
    
    # Check for API Key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERROR: GEMINI_API_KEY environment variable is not set.")
        print("   Please open the '.env' file in the root directory and paste your API Key there.")
        print("   Example: GEMINI_API_KEY=AIzaSy...")
        return

    manager = DataManager()
    total_files = 0
    success_count = 0
    
    for folder in INPUT_DIRS:
        if not os.path.exists(folder):
            print(f"⚠️ Folder not found: {folder}. Skipping.")
            continue
            
        print(f"\n📂 Scanning folder: {folder}")
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.pdf', '.xlsx', '.xls'))]
        
        if not files:
            print("   No supported files found.")
            continue

        for filename in files:
            filepath = os.path.join(folder, filename)
            print(f"   Processing: {filename}...", end=" ", flush=True)
            
            try:
                result = manager.process_file(filepath)
                if result.get("status") == "success":
                    print(f"✅ OK ({result.get('items_count')} items)")
                    success_count += 1
                else:
                    print(f"⚠️ Skipped ({result.get('reason') or result.get('message')})")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            total_files += 1
            import time
            time.sleep(4) # Rate limit protection

    print(f"\n🏁 Batch Import Complete.")
    print(f"   Processed: {success_count}/{total_files} files successfully.")
    print("   Now restart the backend (python backend/main.py) and check the Google Sheet!")

if __name__ == "__main__":
    main()
