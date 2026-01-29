import fitz  # PyMuPDF
import re
import os

class PDFProcessor:
    def __init__(self):
        pass

    def extract_prices(self, file_path):
        """
        Extracts items and prices from a PDF supplier quote.
        Returns a list of dicts: [{'item': ..., 'price': ..., 'unit': ..., 'date': ...}]
        """
        items = []
        try:
            doc = fitz.open(file_path)
            file_date = self._extract_date(file_path) # Fallback to filename date if not found in text
            
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            
            # Simple heuristic for this specific format
            # Look for patterns like "množství MJ cena MJ bez DPH"
            # We will use regex to find items
            # Pattern: [code]? [description] [quantity] [unit] [price]
            
            # For now, let's extract by lines
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                # Ignore lines that look like percentages or have '%'
                if '%' in line or ' slev' in line.lower():
                    continue

                # Look for price-like numbers (e.g., "16 175,00")
                # Must be at the end of line or followed by MJ
                price_match = re.search(r'(\d{1,3}(?:\s\d{3})*,\d{2})', line)
                if price_match:
                    # Potential price line
                    price_str = price_match.group(1).replace(' ', '').replace(',', '.')
                    try:
                        price = float(price_str)
                        if price < 0.01: continue # Ignore zero prices

                        # We need to find the description which is usually 1-2 lines above
                        # OR on the same line if it's a table row
                        description = ""
                        if len(line) > 20: # Likely the line contains both desc and price
                             description = line.replace(price_match.group(1), '').strip()
                        
                        if not description and i > 0:
                            description = lines[i-1]
                        
                        # Clean description
                        description = re.sub(r'^\d+[\s\.]+', '', description) # remove leading numbers
                        
                        if len(description) < 5 or not re.search('[a-zA-Zá-žÁ-Ž]', description):
                            continue

                        # Avoid repeating the same price/item if multiple matches found
                        items.append({
                            'item': description,
                            'price': price,
                            'unit': "ks", 
                            'date': file_date,
                            'source': os.path.basename(file_path)
                        })
                    except:
                        continue
            
            # De-duplicate items from the same PDF (simple check)
            unique_items = []
            seen = set()
            for it in items:
                key = (it['item'], it['price'])
                if key not in seen:
                    unique_items.append(it)
                    seen.add(key)

            return unique_items
        except Exception as e:
            print(f"Error processing PDF {file_path}: {e}")
            return []

    def _extract_date(self, file_path):
        # Extract date from filename or text
        # Example: 17.3.2025
        match = re.search(r'(\d{1,2})\.(\d{1,2})\.\s?(\d{4})', file_path)
        if match:
            return f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
        return "2025-01-01" # Default

if __name__ == "__main__":
    # Test
    proc = PDFProcessor()
    test_pdf = r"Input\01_Nabidky_PDF\NAB-170-25-02037_1.pdf"
    if os.path.exists(test_pdf):
        results = proc.extract_prices(test_pdf)
        print(f"Extracted {len(results)} items.")
        for item in results[:5]:
            print(item)
