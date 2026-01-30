import google.generativeai as genai
import os
import json
import re
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
            prompt = f"""Jsi Data Extractor pro interní stavební rozpočty (Excel).

ÚKOL: Extrahuj položky s cenami 'Montáž A' (práce) a 'Dodávka A' (materiál).

VÝSTUP - POUZE PLATNÝ JSON (nic jiného!):
{{
    "vendor": "Internal",
    "date": null,
    "items": [
        {{"raw_name": "Popis položky", "price_material": 123.45, "price_labor": 67.89, "unit": "ks", "quantity": 1.0}}
    ]
}}

PRAVIDLA:
1. Každá položka MUSÍ mít raw_name (text popisu).
2. price_material = cena materiálu BEZ DPH (Dodávka A).
3. price_labor = cena práce BEZ DPH (Montáž A).
4. Ignoruj řádky: Celkem, Součet, DPH, Mezisoučet, Total.

SOUBOR: {filename}
OBSAH:
{text_content[:25000]}

ODPOVĚZ POUZE PLATNÝM JSON OBJEKTEM:"""
        else:
            prompt = f"""Jsi Data Extractor pro nabídky dodavatelů stavebního materiálu.

ÚKOL: Extrahuj VŠECHNY položky s cenami z nabídky. Hledej tabulky s položkami.

VÝSTUP - POUZE PLATNÝ JSON (nic jiného, žádný text před ani za!):
    "vendor": "Název firmy",
    "date": "YYYY-MM-DD",
    "offer_number": "Číslo nabídky/zakázky",
    "items": [
        {{"raw_name": "Přesný popis položky z dokumentu", "price_material": 123.45, "price_labor": 0.0, "unit": "ks", "quantity": 1.0}}
    ]
}}

PRAVIDLA:
1. raw_name = PŘESNÝ text popisu z dokumentu (např. "Krabice KO 68 pod omítku").
2. price_material = jednotková cena BEZ DPH (hledej sloupec "cena MJ bez DPH" nebo "po slevě bez DPH").
3. price_labor = obvykle 0 pro dodavatelské nabídky.
4. unit = měrná jednotka (ks, m, m2, kpl, sada...).
5. quantity = množství.
6. offer_number = najdi číslo nabídky/zakázky (např. "Nabídka č. 202401").
7. IGNORUJ řádky: Celkem, Součet, DPH, Základ daně, Mezisoučet, Total, Recyklační.
8. IGNORUJ řádky bez jednotkové ceny (hlavičky kapitol).
9. Extrahuj i krabice, svorky, trubky, kabely - VŠECHNY položky!

SOUBOR: {filename}
OBSAH:
{text_content[:25000]}

ODPOVĚZ POUZE PLATNÝM JSON OBJEKTEM (začni {{ a skonči }}):"""

        try:
            response = self.model.generate_content(prompt)
            raw = response.text
            # Debug: print first 500 chars of response
            print(f"DEBUG AI Response (first 500 chars): {raw[:500]}")
            return self._parse_json(raw)
        except Exception as e:
            print(f"Detail AI Error: {e}")
            return None

    def _parse_json(self, text):
        # Remove markdown code blocks if present
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Attempted to parse: {json_match.group()[:300]}...")
        
        # Fallback: try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Raw text: {text[:500]}...")
            return None
