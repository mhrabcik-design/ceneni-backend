import hashlib
import os
import re
import pandas as pd
from datetime import datetime
from database.price_db import PriceDatabase
from services.ai_extractor import AIExtractor
from services.cache_manager import CacheManager

class DataManager:
    def __init__(self, db_url=None):
        # We pass just the path, PriceDatabase handles connection
        self.db = PriceDatabase(db_url)
        self.cache = CacheManager()
        # Initialize AI intentionally lazy or if key exists
        try:
            self.ai = AIExtractor()
        except Exception:
            print("Warning: AI Extractor not initialized (Missing Key?)")
            self.ai = None

    def process_file(self, filepath: str, file_type_override: str = None):
        """
        Main entry point. Reads file, sends to AI, saves to DB.
        For Excel files, processes sheet by sheet to ensure all data is captured.
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

            ext = os.path.splitext(filepath)[1].lower()
            is_excel = ext in ['.xlsx', '.xls']

            # 3. Read & Process (Sheet-by-sheet for Excel)
            all_items = []
            final_data = {"vendor": "Unknown", "date": None, "offer_number": None}

            if is_excel:
                sheets = pd.read_excel(filepath, sheet_name=None)
                sheet_stats = []
                for sheet_name, df in sheets.items():
                    if df.empty or len(df.columns) < 2:
                        continue
                    
                    # Split sheet into chunks of 50 rows to prevent AI truncation/summarization
                    chunk_size = 50
                    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
                    sheet_item_count = 0
                    
                    print(f"📄 Processing sheet '{sheet_name}' ({len(df)} rows, {len(chunks)} chunks) from {os.path.basename(filepath)}")
                    
                    for idx, chunk in enumerate(chunks):
                        print(f"  - Chunk {idx+1}/{len(chunks)} for sheet '{sheet_name}'")
                        content = f"--- LIST: {sheet_name} (Chunk {idx+1}/{len(chunks)}) ---\n{chunk.to_csv(index=False)}"
                        
                        data = self.ai.extract_from_text(content, f"{os.path.basename(filepath)} [{sheet_name} ch{idx+1}]", file_type=file_type)
                        if data and data.get('items'):
                            all_items.extend(data['items'])
                            sheet_item_count += len(data['items'])
                            
                            # Keep metadata from the first valid chunk result
                            if final_data["vendor"] == "Unknown":
                                if data.get('vendor'):
                                    final_data["vendor"] = data.get('vendor')
                                if data.get('date'):
                                    final_data["date"] = data.get('date')
                                if data.get('offer_number'):
                                    final_data["offer_number"] = data.get('offer_number')
                    
                    sheet_stats.append(f"{sheet_name}: {sheet_item_count}")
                    print(f"✅ Extracted total {sheet_item_count} items from sheet '{sheet_name}'")
                
                if sheet_stats:
                    print(f"📊 Summary for {os.path.basename(filepath)}: " + ", ".join(sheet_stats))
            else:
                # Standard single-shot process for PDF/TXT
                content = self._read_file_content(filepath)
                data = self.ai.extract_from_text(content, os.path.basename(filepath), file_type=file_type)
                if data:
                    all_items = data.get('items', [])
                    final_data = data

            if not all_items:
                return {"status": "skipped", "reason": "No data found by AI in any sheet"}

            offer_number = final_data.get('offer_number')
            
            # 4. Final Duplicate Check (Hash + Offer Number)
            existing = self.db.check_file_exists(file_hash=file_hash, offer_number=offer_number)
            
            if existing:
                existing_ext = os.path.splitext(existing['filename'])[1].lower()
                existing_is_excel = existing_ext in ['.xlsx', '.xls']

                if is_excel and not existing_is_excel:
                    print(f"Upgrading existing PDF offer {offer_number} with new Excel data.")
                    self.db.delete_source(existing['id']) 
                else:
                    return {
                        "status": "duplicate", 
                        "reason": f"File already exists (Matched by {existing['type']}). Original: {existing['filename']} by {existing['vendor']}",
                        "details": existing
                    }

            # 5. Validate & Normalize Date
            offer_date = self._determine_date(final_data.get('date'), filepath)
            
            # Map file_type to source_type
            source_type = 'INTERNAL' if file_type == 'internal' else 'SUPPLIER'

            # Strict Logic: If internal, wipe material prices to prevent chaos
            if source_type == 'INTERNAL':
                for it in all_items:
                    it['price_material'] = 0.0

            # 6. Save
            source_id = self.db.add_processed_file(
                filename=os.path.basename(filepath),
                vendor=final_data.get('vendor', 'Unknown'),
                date_offer=offer_date,
                items=all_items,
                file_hash=file_hash,
                offer_number=offer_number,
                source_type=source_type
            )
            
            return {"status": "success", "type": file_type, "items_count": len(all_items), "source_id": source_id}
            
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
                # Read all sheets into a dictionary of DataFrames
                sheets = pd.read_excel(filepath, sheet_name=None)
                all_content = []
                for sheet_name, df in sheets.items():
                    if not df.empty:
                        all_content.append(f"--- LIST: {sheet_name} ---\n{df.to_string()}")
                return "\n\n".join(all_content)
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
            except Exception:
                pass
            
        # 2. Try Filename (Regex for YYYY-MM-DD or DD.MM.YYYY)
        fname = os.path.basename(filepath)
        # Match 2024-01-01
        m = re.search(r'20\d{2}-\d{2}-\d{2}', fname)
        if m:
            try:
                return datetime.strptime(m.group(0), "%Y-%m-%d").date()
            except Exception:
                pass
            
        # Match 15.01.2024
        m = re.search(r'(\d{1,2})\.(\d{1,2})\.(20\d{2})', fname)
        if m:
            try:
                return datetime.strptime(f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "%Y-%m-%d").date()
            except Exception:
                pass

        # 3. Fallback to File Modification Time
        try:
            timestamp = os.path.getmtime(filepath)
            return datetime.fromtimestamp(timestamp).date()
        except Exception:
            return datetime.now().date()

    def check_outliers(self, item_id):
        """
        Simple outlier detection logic.
        Returns entries that are > 2x standard deviation from mean?
        Or simple Min/Max check for now.
        """
        pass # To be implemented
