# Session Handoff - 2026-02-04

## Poslední změny (2026-02-03)

### ✅ Dokončeno

1. **Reverted cache implementace**
   - Cache způsobovala bugy (ceny 0, nefunkční kandidáti)
   - Vráceno k funkční verzi bez cache (`722bcca`)
   - Cache implementace odložena na později

2. **Fix: Materiál s cenou 0 se nepřepisuje**
   - Pokud API vrátí cenu 0, buňka zůstane prázdná (`cd0e821`)

3. **Fix: Sync používá float toleranci**
   - Opraveno porovnávání cen (tolerance 0.01) aby se položky neoznačovaly jako změněné kvůli float precision (`5c9113b`)

4. **Fix: Kandidáti se zobrazují vždy**
   - API nyní vrací top 5 kandidátů bez ohledu na match score (`3947d3f`)
   - Uživatel může vybrat alternativu i při vysoké shodě

5. **Fix: Smart source_type pro ruční ceny**
   - Jen práce (mat=0) → INTERNAL
   - Jen materiál (práce=0) → SUPPLIER  
   - Obojí → ADMIN

6. **Historie a analýza**
   - Zobrazuje pouze ceny materiálu (práce ignorovány)

### ⏳ K otestování (po Render deploy)

- **Zobrazení kandidátů** - mělo by fungovat pro všechny buňky (i s vysokou shodou)
- Po kliknutí na buňku v cenovém sloupci → "🔍 Zobrazit kandidáty" by mělo ukázat nabídku

### 🔧 Nastavení sloupců

Uživatel používá vlastní nastavení:
- Popis: **C**
- Materiál: **E**
- Práce: **F**

(Defaulty jsou I a J)

### 📋 Budoucí úkoly (viz FUTURE_IDEAS.md)

1. **Aliasový systém** - učení z manuálních výběrů (naplánováno, neimplementováno)
2. **Cache optimalizace** - implementovat správně po stabilizaci základních funkcí

### 🔗 Poslední commity

```
3947d3f fix: always return candidates regardless of match score
5c9113b fix: sync uses float tolerance to prevent false change detection
cd0e821 fix: skip material prices of 0 during pricing
722bcca revert: removed broken cache, back to working version
```

### � Poznámky

- Databáze byla resetována a znovu naplněna (uživatel nahrál podklady)
- Render backend se automaticky deployuje po push na main
- GAS deployment: `clasp push` z `gas/` složky

---

**Příští kroky:**
1. Otestovat zobrazení kandidátů
2. Pokud funguje, začít s alias systémem
3. Cache implementovat až po plné stabilizaci
