import google.generativeai as genai
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

class AIExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def extract_from_text(self, text_content: str, filename: str, file_type: str = 'supplier'):
        """
        Extracts structured pricing data from raw text using Gemini.
        file_type: 'supplier' (PDFs) or 'internal' (Excel History)
        """
        
        if file_type == 'internal':
            prompt = f"""
            You are a Specific Data Extractor for Internal construction budgets (Excel).
            
            GOAL: Extract 'Montáž A' (Labor Cost) and 'Dodávka A' (Material Cost) for items.
            The input comes from an Excel where columns often are: "Dodávka A", "Koef", "Dodávka C", "Montáž A", "Koef", "Montáž C".
            
            EXTRACT FORMAT (JSON ONLY):
            {{
                "vendor": "Internal History",
                "date": "2024-01-01 (approx, or found in text)",
                "items": [
                    {{
                        "raw_name": "Item Description",
                        "price_material": 0.0 (Value from 'Dodávka A'),
                        "price_labor": 0.0 (Value from 'Montáž A'),
                        "unit": "m2/ks...",
                         "quantity": 1.0
                    }}
                ]
            }}
            
            RULES:
            1. Focus heavily on finding the "Montáž A" value. 
            2. If you see value 0 for material but valid for labor, that's fine.
            3. Ignore rows that are just headers or sums.
            
            SOURCE FILE: {filename}
            CONTENT:
            {text_content[:30000]}
            """
        else:
            # Supplier Quote Logic (Default)
            prompt = f"""
            You are a Data Extraction Assistant. I will provide text from a construction offer (PDF/Excel).
            
            EXTRACT FORMAT (JSON ONLY):
            {{
                "vendor": "Name of the company (or Unknown)",
                "date": "YYYY-MM-DD (or null if not found)",
                "items": [
                    {{
                        "raw_name": "Exact text description from the line",
                        "price_material": 0.0 (float, 0 if missing),
                        "price_labor": 0.0 (float, 0 if missing),
                        "unit": "m2/ks/kpl...",
                        "quantity": 1.0 (float, or null)
                    }}
                ]
            }}

            RULES:
            1. STRICTLY IGNORE rows containing: "Celkem", "Součet", "DPH", "Mezisoučet", "Total", "Recyklační", "Autorský", "Základ daně".
            2. Header rows (chapter names) usually lack a unit price -> Ignore them.
            3. Focus on line items that have a QUANTITY, UNIT, and UNIT PRICE.
            4. If a line splits material and labor, extract both. If only one price, put it in 'price_material'.
            5. Do NOT extract the total project price as an item.
            
            SOURCE FILE: {filename}
            CONTENT:
            {text_content[:30000]} 
            """

        try:
            response = self.model.generate_content(prompt)
            return self._parse_json(response.text)
        except Exception as e:
            print(f"Detail AI Error: {e}")
            return None

    def _parse_json(self, text):
        clean_text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            print("Failed to parse JSON from AI response")
            return None
