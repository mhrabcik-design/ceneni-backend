import os
from datetime import datetime
from database.price_db import PriceDatabase
from services.ai_extractor import AIExtractor
import pandas as pd
import hashlib

class DataManager:
    def __init__(self, db_url=None):
        # We pass just the path, PriceDatabase handles connection
        self.db = PriceDatabase(db_url)
        # Initialize AI intentionally lazy or if key exists
        try:
            self.ai = AIExtractor()
        except:
            print("Warning: AI Extractor not initialized (Missing Key?)")
            self.ai = None

    def process_file(self, filepath: str, file_type_override: str = None):
        """
        Main entry point. Reads file, sends to AI, saves to DB.
        """
        if not self.ai:
            return {"error": "AI not ready"}

        try:
            # 1. Calculate Hash & Check Duplicates
            file_hash = self._calculate_file_hash(filepath)
            
            # 2. Determine Type
            file_type = file_type_override
            if not file_type:
                file_type = 'supplier'
                if '02_Historie' in filepath or 'internal' in filepath.lower():
                    file_type = 'internal'

            # 3. Read Content
            content = self._read_file_content(filepath)
            
            # 4. Extract with AI
            data = self.ai.extract_from_text(content, os.path.basename(filepath), file_type=file_type)
            
            if not data or not data.get('items'):
                return {"status": "skipped", "reason": "No data found by AI"}

            offer_number = data.get('offer_number')
            
            # 5. Final Duplicate Check (Hash + Offer Number)
            existing = self.db.check_file_exists(file_hash=file_hash, offer_number=offer_number)
            
            ext = os.path.splitext(filepath)[1].lower()
            is_excel = ext in ['.xlsx', '.xls']

            if existing:
                existing_ext = os.path.splitext(existing['filename'])[1].lower()
                existing_is_excel = existing_ext in ['.xlsx', '.xls']

                # Hierarchy Logic:
                # 1. New is Excel, Existing is PDF -> UPDATE/OVERWRITE (Upgrade to better data)
                if is_excel and not existing_is_excel:
                    print(f"Upgrading existing PDF offer {offer_number} with new Excel data.")
                    # We continue to saving - add_processed_file will need to handle updates or we delete old one
                    self.db.delete_source(existing['id']) 
                else:
                    # 2. Any other case (Same format or New is PDF/Existing is Excel) -> SKIP
                    return {
                        "status": "duplicate", 
                        "reason": f"File already exists (Matched by {existing['type']}). Original: {existing['filename']} by {existing['vendor']}",
                        "details": existing
                    }

            # 6. Validate & Normalize Date
            offer_date = self._determine_date(data.get('date'), filepath)
            
            # 7. Save
            source_id = self.db.add_processed_file(
                filename=os.path.basename(filepath),
                vendor=data.get('vendor', 'Unknown'),
                date_offer=offer_date,
                items=data['items'],
                file_hash=file_hash,
                offer_number=offer_number
            )
            
            return {"status": "success", "type": file_type, "items_count": len(data['items']), "source_id": source_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_file_hash(self, filepath):
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _read_file_content(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
                return df.to_string()
            elif ext == '.pdf':
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(filepath)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    return text
                except ImportError:
                    return "Error: PyMuPDF (fitz) not installed."
            elif ext == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return ""

    def _determine_date(self, date_str, filepath):
        # 1. Try AI-detected date
        if date_str and len(date_str) > 5:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except: pass
            
        # 2. Try Filename (Regex for YYYY-MM-DD or DD.MM.YYYY)
        import re
        fname = os.path.basename(filepath)
        # Match 2024-01-01
        m = re.search(r'20\d{2}-\d{2}-\d{2}', fname)
        if m:
            try: return datetime.strptime(m.group(0), "%Y-%m-%d").date()
            except: pass
            
        # Match 15.01.2024
        m = re.search(r'(\d{1,2})\.(\d{1,2})\.(20\d{2})', fname)
        if m:
            try: return datetime.strptime(f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "%Y-%m-%d").date()
            except: pass

        # 3. Fallback to File Modification Time
        try:
            timestamp = os.path.getmtime(filepath)
            return datetime.fromtimestamp(timestamp).date()
        except:
            return datetime.now().date()

    def check_outliers(self, item_id):
        """
        Simple outlier detection logic.
        Returns entries that are > 2x standard deviation from mean?
        Or simple Min/Max check for now.
        """
        pass # To be implemented
