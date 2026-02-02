# 🔄 Session Handoff - 2026-02-02

> **INSTRUCTION FOR AI:** Read this file FIRST. This project is synced via OneDrive. The previous session was on a different machine and ended with some local-only changes that couldn't be pushed due to OS-level permission issues.

## 🚀 Today's Achievements (Ready locally)

1. **PDF Extraction Logic Improvement**:
   - `backend/services/ai_extractor.py`: Gemini prompts updated to combine multi-line descriptions (e.g., Code + Name split across lines).
   - Rules softened to ensure one item stays as one entry while combining text.

2. **Automatic Data Cleaning**:
   - `backend/database/price_db.py`: Added `_clean_item_name()` method.
   - Automatically removes sequential IDs (1., a), 10.), bullet points, and noise before saving to DB.
   - Applied to both automatic ingestion and manual selection.

3. **Intelligent Selection UI (GAS)**:
   - `gas/Sidebar.html` & `gas/Cenar.js`: New automatic candidate detection.
   - If a cell with score < Threshold (default 40%) is clicked, a "Top Candidates" menu appears in the Sidebar.
   - Users can choose the correct item with 1 click, seeing Name, Price, Date, and **PDF Source**.

4. **Maintenance Tool**:
   - `scripts/normalize_items.py`: Created a script to clean up historical database fragmentation and merge duplicate items.

## ⚠️ TECHNICAL DEBT / PENDING SYNC

The following actions **FAILED** on the previous machine due to environment restrictions and MUST be completed here:

- [ ] **Git Push**: Local commits failed with `mmap` error. 
  - *Action:* Run `git status`, `git add .`, `git commit -m "feat: complete matching selection logic"`, and `git push origin main`.
- [ ] **GAS Push (clasp)**: Failed due to PowerShell Execution Policy.
  - *Action:* Run `clasp push` to sync the new Sidebar and Bridge logic to Google Sheets.
- [ ] **DB Optimization**: 
  - *Action:* Run `python scripts/normalize_items.py` to clean up old fragmented entries in Supabase.

## 📍 Current State
- **Database:** Supabase (Cloud) - Shared across machines.
- **Backend:** Hosted on Render - Needs Git Push to redeploy.
- **GAS:** Local files updated, needs `clasp push` to update the actual Sheets Add-on.

## ⏭️ Next Steps
1. Verify `git` and `clasp` are working on this machine.
2. Complete the "Pending Sync" tasks above.
3. Test the automatic candidate menu in Google Sheets.
