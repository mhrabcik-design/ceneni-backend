# Project Plan: AI-Powered Construction Pricing Assistant

> **Goal:** An intelligent system that autonomously "mines" pricing data from hundreds of PDF/Excel supplier quotes using **Generative AI**, tracks price history over time, and integrates this intelligence into Google Sheets for automated budget pricing.

---

## 📋 1. Requirements & Solution

### A. The Challenge
- **Legacy Issue:** Previous system relied on Regex, which broke with every format change.
- **Data Volume:** 100+ initial files, then monthly updates.
- **Complexity:** Need to combine market material prices with internal labor standards.

### B. The Solution: AI-First Architecture & Split Data Strategy
We treat data sources differently based on their origin:

1.  **Supplier Quotes (`Input/01_Nabidky_PDF`)**
    - **Target:** **Material Prices** (Dodávka).
    - **Method:** AI extracts Item Description + Unit Price.
    - **Logic:** Represents current market rates.

2.  **Internal Budgets (`Input/02_Historie_Excel`)**
    - **Target:** **Labor Prices** (Montáž "A").
    - **Method:** AI/Pandas looks specifically for the "Montáž A" column (Cost Price).
    - **Logic:** Represents our internal cost standards for installation.

3.  **Visualization & Merging**
    - The database stores `PriceEntry` with `price_material` and `price_labor`.
    - When pricing an item, the system can combine the freshest **Material Price** (from Supplier) with the freshest **Labor Price** (from Internal History) to form a complete unit price.

---

## 🏗️ 2. Technical Architecture

### Backend (Python/FastAPI)
- **Service:** `AIExtractor` (wraps Google GenAI SDK).
    - *Updated Logic*: Supports context-aware extraction (Extract only Labor if Source == Internal).
- **Service:** `DataManager` (orchestrates ingestion).
- **Database:** SQLite (with SQLAlchemy).
    - Tables: `SourceFile`, `items`, `price_entries`.
    - `SourceFile` now implicitly tracks origin via folder path or metadata.

### Frontend (Google Sheets Sidebar)
- **Tech:** Apps Script + HTML/JS (Vue.js or Vanilla).
- **Features:** Price History Graph, Smart Pricing Button.

---

## 🚀 3. Implementation Status

### Phase 1: Backend Core (✅ COMPLETE)
- [x] **Relational DB:** Implemented `sources`, `items`, `price_entries`.
- [x] **AI Service:** Integrated Gemini 1.5 Flash.
- [x] **API:** Endpoints ready.

### Phase 2: Refinement & specialization (🚧 IN PROGRESS)
- [ ] **Labor Extraction:** Update `AIExtractor` to target "Montáž A" in Internal Excels.
- [ ] **Material Extraction:** Ensure PDFs focus on Material.
- [ ] **Merge Logic:** Update `DataManager` to handle partial updates (e.g. valid labor, zero material).

### Phase 3: Frontend (✅ COMPLETE)
- [x] **Visualization:** Chart.js implemented.
- [x] **Integration:** Apps Script connected.
