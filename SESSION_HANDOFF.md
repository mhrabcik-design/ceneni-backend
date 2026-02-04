# Session Handoff - 2026-02-04 (Update: Mainframe Transition)

## 🎯 Aktuální stav projektu
Projekt je ve stabilizovaném stavu "Zero Bug Policy". Backend byl kompletně vyčištěn od lint chyb a logika matchování byla zpevněna.

### ✅ Dokončeno (Dnes)
1. **Kompletní Linting Backend**:
   - Nainstalován a spuštěn `ruff`.
   - Opraveno 130+ chyb (bare excepts, import order, multi-line statements).
   - Backend nyní splňuje standard PEP8.
2. **Git & GitHub Sync**:
   - Všechny změny pushnuty na `main`.
   - Nasazeno na Render (automatický deploy).
3. **Stabilizace GAS-Backend Bridge**:
   - Opravena tolerance pro float precision (0.01) v `sync_admin_items`.
   - Vyřešeny problémy s chybějícím `os` modulem v `data_manager.py`.

### 🏁 Stav Checklistu
- ✅ **Security**: PASSED
- ✅ **Lint**: PASSED
- ✅ **Schema**: PASSED
- ❌ **Tests**: FAILED (Doinstalován `pytest`, ale v projektu zatím nejsou žádné `.py` testy – nalezena 0).

### 🔧 Aktuální konfigurace (Mainframe připomenutí)
- **Backend API**: `https://ceneni-backend.onrender.com`
- **Sloupce v Google Sheets**:
  - Popis: **C** (sloupec 3)
  - Materiál: **E** (sloupec 5)
  - Práce: **F** (sloupec 6)
- **Logika Price Selection**: Podporuje manuální výběr z top 5 kandidátů v sidebaru.

### 📋 Příští kroky (Draft pro novou session)
1. **Aliasový systém** (Větev: `feature/alias-system`):
   - Učení se z manuálních výběrů (pokud uživatel vybere kandidáta, systém si to zapamatuje jako alias).
2. **Vytvoření Unit Testů**:
   - Vytvořit `backend/tests/test_api.py` pro 100% zelený checklist.
3. **Cache**:
   - Re-implementace cache až po plné stabilizaci alias systému.

---

**Poznámka pro "Mainframe":** Před zahájením vývoje Alias systému doporučuji vytvořit novou větev `git checkout -b feature/alias-system`. Kód je čistý a připravený.
