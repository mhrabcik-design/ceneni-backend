"""
Diagnostický skript pro testování AI extrakce z PDF souboru.
Zobrazí, co AI vrátí pro jeden konkrétní soubor.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from services.ai_extractor import AIExtractor

def test_pdf_extraction(filepath):
    print(f"📄 Testování souboru: {os.path.basename(filepath)}")
    print("-" * 60)
    
    # Read PDF content
    try:
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
        print(f"📝 Extrahováno {len(text)} znaků textu z PDF")
        print(f"\n--- Prvních 500 znaků ---\n{text[:500]}\n")
    except Exception as e:
        print(f"❌ Chyba čtení PDF: {e}")
        return
    
    # Run AI extraction
    print("🤖 Spouštím AI extrakci...")
    ai = AIExtractor()
    
    try:
        result = ai.extract_from_text(text, os.path.basename(filepath), file_type='offer')
        
        print(f"\n--- AI Výsledek ---")
        print(f"Vendor: {result.get('vendor', 'N/A')}")
        print(f"Date: {result.get('date', 'N/A')}")
        print(f"Počet položek: {len(result.get('items', []))}")
        
        if result.get('items'):
            print(f"\n--- Prvních 10 položek ---")
            for i, item in enumerate(result['items'][:10]):
                name = item.get('raw_name') or item.get('item', 'N/A')
                price = item.get('price_material', 0)
                print(f"  {i+1}. {name[:60]}... | Cena: {price}")
        else:
            print("\n⚠️ AI nevrátila žádné položky!")
            print(f"Raw response: {result}")
            
    except Exception as e:
        print(f"❌ Chyba AI extrakce: {e}")

if __name__ == "__main__":
    # Test first PDF
    test_file = r"Input\01_Nabidky_PDF\01_NAB-170-25-00450.pdf"
    if os.path.exists(test_file):
        test_pdf_extraction(test_file)
    else:
        print(f"Soubor nenalezen: {test_file}")
