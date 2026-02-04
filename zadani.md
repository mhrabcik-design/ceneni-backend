# Project Plan: AI-Powered Construction Pricing Assistant

> **Goal:** An intelligent system that autonomously "mines" pricing data from hundreds of PDF/Excel supplier quotes using **Generative AI**, tracks price history over time, and integrates this intelligence into Google Sheets for automated budget pricing.

---

## 📋 1. Requirements & Solution

### A. The Challenge
- **Legacy Issue:** Previous system relied on Regex, which broke with every format change.
- **Data Volume:** 100+ initial files, then monthly updates.
- **Complexity:** Need to combine market material prices with internal labor standards.
- **Transparency:** User needs to verify AI matches and see original source data.

### B. The Solution: AI-First Architecture & Split Data Strategy
We treat data sources differently based on their origin:

1.  **Nabídky dodavatelů (PDF)**
    - **Cíl:** **Ceny materiálů** (Dodávka).
    - **Metoda:** AI extrahuje popis položky + jednotkovou cenu.
    - **Logika:** Reprezentuje aktuální tržní sazby.

2.  **Historické rozpočty (Excel)**
    - **Cíl:** **Ceny montáže** (Montáž "A").
    - **Metoda:** AI/Pandas hledá konkrétně sloupec "Montáž A" (nákladová cena).
    - **Logika:** Reprezentuje naše vnitřní standardy pro instalaci.

3.  **Visualization & Merging**
    - The database stores `PriceEntry` with `price_material` and `price_labor`.
    - When pricing an item, the system can combine the freshest **Material Price** (from Supplier) with the freshest **Labor Price** (from Internal History) to form a complete unit price.

---

## 🏗️ 2. Technical Architecture

### Backend (Python/FastAPI)
- **Service:** `AIExtractor` (wraps Google Gemini 1.5 Flash API).
    - Czech prompts for better extraction accuracy.
    - Explicit "cena bez DPH" instruction.
    - Regex fallback for JSON parsing when AI returns malformed responses.
- **Service:** `DataManager` (orchestrates ingestion).
- **Database:** PostgreSQL (Supabase cloud).
    - Tables: `sources`, `items`, `prices`.
    - ORM: SQLAlchemy for cross-database compatibility.
- **Hosting:** Render.com (auto-deploy from GitHub).

### Frontend (Google Sheets Sidebar)
- **Tech:** Apps Script + HTML/JS + Chart.js.
- **Features:**
    - 3-column pricing: Popis (C), Materiál (I), Práce (J)
    - One-click dual pricing (Material + Labor simultaneously)
    - Context-aware candidate suggestions
    - Price History Graph
    - Cell notes with original name + match score
    - Feedback system (blacklist + custom prices)
    - Load-from-cell for history search
    - **Alias System Management** (Learn from manual selections, view/delete learned aliases)

---

## 🚀 3. Implementation Status

### Phase 1: Backend Core (✅ COMPLETE)
- [x] **Relational DB:** Implemented `sources`, `items`, `prices` tables.
- [x] **AI Service:** Integrated Gemini 1.5 Flash with Czech prompts.
- [x] **API Endpoints:** `/match`, `/search`, `/status`, `/items/{id}/history`, `/items/{id}/details`.
- [x] **Cloud Migration:** Deployed to Render.com + Supabase PostgreSQL.

### Phase 2: AI Extraction Refinement (✅ COMPLETE)
- [x] **Fixed AI JSON Issues:** Czech prompts, "cena bez DPH", regex fallback.
- [x] **Systém pro import:** Vytvořen nahrávací panel přímo v Google Sheets.
- [x] **Deduplikace:** Implementováno rozpoznávání stejných souborů a čísel nabídek.

### Phase 3: Frontend & UX (✅ COMPLETE)
- [x] **Price History Chart:** Chart.js integration.
- [x] **Apps Script Bridge:** Connected to cloud backend.
- [x] **Material/Montáž Split:** Dropdown to select price type.
- [x] **Transparency Features:**
    - Cell notes with original item name, match score %, source, date, ID.
    - Low-confidence highlighting (< 60% = orange background).
    - Load-from-cell button for history search.

### Phase 4: Feedback System (✅ COMPLETE)
- [x] **Blacklist Function:** Delete bad items from database via sidebar.
- [x] **Custom Prices:** Add user-defined items and prices to database.
- [x] **Cleanup Script:** Conservative removal of summary rows only.

### Phase 7: Labor & Maintenance (✅ COMPLETE)
- [x] **Labor Suggestion Engine:** Context-aware labor matching in a modal dialog.
- [x] **Database Reset Tool:** "Nuclear" button with double confirmation.
- [x] **Clasp Workflow:** Automated syncing of Apps Script files via command line.
- [x] **Project Re-structure:** Organized `gas/` and `scripts/` directories.

- [x] **UI Clarity:** Updated Upload Panel with clear material vs. labor labels.

### Phase 9: Alias System (The Brain) (✅ COMPLETE)
- [x] **Smart Learning:** System automatically saves manual user selections as "aliases" to improve future matches.
- [x] **Advanced Scoring:** Match score calculation upgraded to give >80% weight to learned aliases (passing the threshold easily).
- [x] **Alias Admin UI:** New list `ADMIN_ALIASY` in Google Sheets to view and manage (delete) what the system has learned.
- [x] **Bulk Management:** Batch-delete endpoints and UI actions for aliases.
- [x] **Automatic Testing:** Professional `pytest` suite covering Matcher, Search, and Alias flow.

---

## 📊 4. Datové zdroje
Data jsou nyní nahrávána přímo uživatelem přes **Centrum nahrávání** v Google Sheets. Systém automaticky rozlišuje mezi PDF nabídkami (`SUPPLIER`) a Excel rozpočty (`INTERNAL`) a ukládá je do cloudové databáze (Supabase).

---

## 🔧 5. API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/match` | Match items to database, returns prices |
| `GET` | `/search?q=` | Fuzzy search for items |
| `GET` | `/status` | Database statistics |
| `GET` | `/items/{id}/history` | Price history for an item |
| `GET` | `/items/{id}/details` | Full details including all sources |
| `DELETE` | `/items/{id}` | Remove item from database (blacklist) |
| `POST` | `/items/add` | Add custom item with price |
| `POST` | `/feedback/learn` | Save manual selection as alias |
| `GET` | `/admin/aliases` | List all learned aliases |
| `POST` | `/admin/aliases/batch-delete` | Batch delete aliases |

### Match Request Example
```json
POST /match
{
    "items": ["Krabice KO 97"],
    "type": "material"  // or "labor"
}
```

### Match Response
```json
{
    "Krabice KO 97": {
        "price": 25.6,
        "unit": "ks",
        "source": "ARGOS ELEKTRO",
        "date": "2025-01-22",
        "item_id": 42,
        "original_name": "Krabice odbočná KOPOS ^ KO 97/5 KA",
        "match_score": 0.85
    }
}
```

---

## 🖥️ 6. Google Sheets Integration

### Files to Deploy
1. **Code.gs** - Copy content from `google_sheets_script.js`
2. **Sidebar.html** - Copy as new HTML file

### Features
- **🚀 Ocenit výběr** - Price selected rows
- **📦 Materiál / 🔧 Montáž** - Select price type
- **📋 Load from cell** - Fill history search from selected cell
- **🔍 Zobrazit graf** - Show price history chart
- **🗑️ Smazat položku z DB** - Blacklist bad matches
- **➕ Přidat do DB** - Add custom prices
- **🧠 Správa Aliasů** - View (list `ADMIN_ALIASY`) and Delete learned search patterns.

### Cell Notes (Transparency)
After pricing, each cell contains a note:
```
📦 Krabice odbočná KOPOS ^ KO 97/5 KA
📊 Shoda: 85%
🏢 Zdroj: ARGOS ELEKTRO
📅 Datum: 2025-01-22
🔗 ID: 42
```

### Visual Indicators
- **Green background** = Manual selection (100% confirmed)
- **Orange background** = Match score < 60% (needs review)
- **No background** = Match score ≥ 60% (good match)

---

## 📁 7. Project Structure

```
ceneni/
├── backend/             # Python Backend (FastAPI, SQLAlchemy)
├── gas/                 # Google Apps Script (Frontend & Bridge)
│   ├── Cenar.js         # Main script (formerly google_sheets_script.js)
│   ├── Sidebar.html     # Pricing & Analysis Sidebar
│   ├── UploadPanel.html # Cloud Ingestion Center
│   └── LaborSuggestions.html # Phase 7: Labor Popup
├── scripts/             # Utility scripts (Cleanup, Migration)
├── .clasp.json          # Clasp configuration for local dev
├── Procfile             # Render deployment
└── brainstorm.md        # Feature roadmap & debate
```

---

## 🔐 8. Environment & Secrets

| Variable | Location | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | `.env` (local) | Google AI API |
| `DATABASE_URL` | Render.com + `.env` | Supabase PostgreSQL |

---

### Phase 5: Bulk Database Editing (Admin Sheet) (✅ COMPLETE)
- [x] **Backend Export:** Endpoint `GET /admin/items` to fetch all data.
- [x] **Backend Sync:** Endpoint `POST /admin/sync` to process bulk changes.
- [x] **Apps Script Sync:** `loadAdminSheet()` and `syncAdminSheet()` functions.
- [x] **Admin UI:** New sheet tab `ADMIN_DATABASE` with Load/Save actions.
- [x] **Filtering:** `filterAdminSheetBySelection()` to jump from budget to DB edit.

---

## 📈 9. Future Enhancements

- [ ] **Global Synonyms** - Extend alias system with global word mappings (e.g., SDK = Sádrokarton)
- [ ] **Smart Cache** - Re-enable caching with intelligent invalidation upon learning new aliases.
- [ ] **Excel Import via Sidebar** (Planned) - Import new files directly from sidebar
- [ ] **Automatic Re-pricing** - Detect when prices are outdated
- [ ] **Multi-user** - Track who added/modified prices

---

## 🏗️ Phase 6: Advanced Upload Panel (MANDATORY) - ✅ COMPLETE
> **Goal:** High-end standalone sidebar for effortless data ingestion without local Python knowledge.

### 1. UX/UI Features (Premium Design)
- **Glassmorphism Aesthetic:** Modern, sleek interface with blurred backdrops and vibrant accents.
- **Drag-and-Drop:** Intuitive file upload zone.
- **Explicit Type Selection:**
  - 📦 **Materiální nabídka** (Vendor PDF) -> Extracts Material prices.
  - 🔨 **Historický rozpočet** (Internal Excel) -> Extracts Labor prices (Montáž A).
- **Batch Processing Dashboard:**
  - Visual progress bars for each file.
  - Success/Error reporting with detailed AI reasoning if skipped.
  - Confetti celebration on batch completion.

### 2. Intelligent Deduplication (Safety First)
- **Offer Number Matching:** AI automatically extracts the "Číslo nabídky" from the PDF. If this number already exists in the database, the upload is blocked to prevent duplicate prices.
- **Content Hashing:** Every uploaded file is hashed (SHA-256). If you try to upload the exact same file under a different name, the system will recognize it and skip processing.
- **Audit Log:** View a list of "Všechny zpracované zdroje" přímo v panelu, abyste věděli, co už v systému je.

### 3. Technical Stack
- **Frontend:** HTML5, Modern CSS (Glassmorphism), Vanilla JS (Fetch API).
- **Apps Script:** `UploadPanel.html` + `showUploadPanel()` bridge.
- **Backend:** Updated `/ingest/upload` endpoint to support `file_type` override and deduplication logic.

---

## 📅 10. Development Log
### 2025-02-01: Automation & AI Refinement
- ✅ **Clasp Integration:** Replaced manual copy-pasting of Apps Script with `clasp push`.
- ✅ **Phase 7 Complete:** Implemented Labor Suggestion Engine (Materiál -> Montáž).
- ✅ **Dev Logistics:** Cleaned up project structure, moved GAS files to `gas/` folder.
- ✅ **Database Admin:** Added a safe "Nuclear" reset button for developers.

- Price history chart with Chart.js

### 2025-02-04: The Brain (Alias System)
- ✅ **Learning Loop:** Implemented feedback endpoint to learn from user manual selections.
- ✅ **Intelligent Scoring:** Upgraded search scoring to prioritize learned aliases (score > 80%).
- ✅ **Alias Management:** Added `ADMIN_ALIASY` sheet and GAS menu for full control over system memory.
- ✅ **Stability:** 4 functional tests passing via `pytest` to ensure zero regressions.
- ✅ **Code Quality:** Optimized `PriceDatabase` by unifying scoring logic and cleaning up redundant methods.

---

## 🤖 Antigravity Note: Modern Workflow
Původní proces manuálního kopírování kódu do Google Sheets byl nahrazen profesionálním workflow pomocí **Google Clasp**.
- **Předtím:** Antigravity vygeneroval kód -> uživatel ho musel ručně zkopírovat do prohlížeče (riziko chyb).
- **Nyní:** Antigravity upraví soubory v `gas/` -> uživatel napíše `clasp push` -> vše se nahraje automaticky.
- **Výsledek:** Rychlejší iterace, čistší kód a méně manuální práce.
