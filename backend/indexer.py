import os
import sys
import tempfile

# Add current dir to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.price_db import PriceDatabase
from backend.processors.excel_processor import ExcelProcessor
from backend.processors.pdf_processor import PDFProcessor

def safe_process_excel(proc, path, is_internal):
    # Try reading directly first
    try:
        return proc.extract_data(path, is_internal=is_internal)
    except Exception:
        print(f"  Direct read failed for {os.path.basename(path)}, trying copy helper...")
    
    # If direct read fails, try copying to temp
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, "ai_price_tmp_" + os.path.basename(path))
    try:
        # Use simple copy, sometimes better than copy2
        with open(path, 'rb') as f_src:
            with open(tmp_path, 'wb') as f_dst:
                f_dst.write(f_src.read())
        
        items = proc.extract_data(tmp_path, is_internal=is_internal)
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return items
    except Exception as e:
        print(f"  Complete failure for {os.path.basename(path)}: {e}")
        return []

def run_indexer():
    db = PriceDatabase()
    db.clear_db() 
    
    pdf_proc = PDFProcessor()
    xl_proc = ExcelProcessor()
    
    # 1. Process Supplier PDF/Excel
    supplier_folder = r"Input\01_Nabidky_PDF"
    print(f"Indexing supplier folder: {supplier_folder}")
    if os.path.exists(supplier_folder):
        for f in os.listdir(supplier_folder):
            path = os.path.join(supplier_folder, f)
            if f.lower().endswith('.pdf'):
                try:
                    items = pdf_proc.extract_prices(path)
                    db.add_prices(items, 'supplier')
                    print(f"  Indexed {len(items)} items from {f}")
                except Exception as e:
                    print(f"  Error processing {f}: {e}")
            elif f.lower().endswith('.xlsx') and not f.startswith('~$'):
                items = safe_process_excel(xl_proc, path, is_internal=False)
                if items:
                    db.add_prices(items, 'supplier')
                    print(f"  Indexed {len(items)} items from {f}")

    # 2. Process History Excel
    history_folder = r"Input\02_Historie_Excel"
    print(f"\nIndexing history folder: {history_folder}")
    if os.path.exists(history_folder):
        for f in os.listdir(history_folder):
            path = os.path.join(history_folder, f)
            if f.lower().endswith('.xlsx') and not f.startswith('~$'):
                items = safe_process_excel(xl_proc, path, is_internal=True)
                if items:
                    db.add_prices(items, 'history')
                    print(f"  Indexed {len(items)} items from {f}")

    print("\nIndexing complete.")

if __name__ == "__main__":
    run_indexer()
