# Session Handoff - 2026-02-04 (Update: Intelligent Alias Management)

## 🎯 Aktuální stav projektu
Backend i Frontend jsou plně připraveny na **Alias Systém**. Systém se učí z manuálních výběrů a uživatel má plnou kontrolu nad touto "pamětí" přímo z Excelu.

### ✅ Dokončeno (Dnes)
1. **Alias Systém (Backend)**:
   - Integrovaná tabulka aliasů, automatické bodování (80%+ pro naučené vazby).
   - Nový endpoint `/admin/aliases` pro výpis a `/admin/aliases/batch-delete` pro promazávání.
2. **Frontend Management (Google Sheets)**:
   - Nové menu **🧠 Správa Aliasů (Učení)**.
   - Funkce **Zobrazit naučené aliasy** (vytvoří list `ADMIN_ALIASY`).
   - Funkce **Smazat vybrané aliasy** (umožní systému "zapomenout" chybnou vazbu).
   - Reorganizace menu do podnabídek pro lepší přehlednost.
3. **Automatizace**:
   - Vše pushnuto na GitHub a automaticky nahráno do Google Sheets přes `clasp`.

### 🏁 Stav Checklistu
- ✅ **Security**: PASSED
- ✅ **Lint**: PASSED
- ✅ **Schema**: PASSED (Updated with item_aliases)
- ✅ **Tests**: PASSED (4 functional tests passing via pytest)

### 🔧 Aktuální konfigurace
- **Backend API**: `https://ceneni-backend.onrender.com`
- **Excel Admin Listy**: `ADMIN_DATABASE` (položky), `ADMIN_ALIASY` (naučené vazby).

### 📋 Příští kroky (TO DO)
1. **Unit Testy (Priorita 1)**:
   - Vytvořit `backend/tests/test_api.py`.
   - Pokrýt testy: Párování, Ingest souborů, Alias systém.
2. **Cache Re-evaluation (Priorita 2)**:
   - Zapnout cache s logikou invalidace (při naučení nového aliasu smazat cache pro daný termín).
3. **Socratic Discovery**:
   - Prozkoumat možnost "globálních synonym" (např. auto-učit, že "SDK" == "Sádrokarton").

---

**Poznámka:** Pokud chcete spravovat naučené vazby, stačí v menu AI Asistenta zvolit "Zobrazit naučené aliasy". Systém je nyní "chytrý" a pamatuje si vaše rozhodnutí.
