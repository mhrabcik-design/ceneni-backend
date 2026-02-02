# Návod k použití: AI Asistent pro oceňování rozpočtů

Tento systém propojuje Google Sheets s umělou inteligencí (Gemini) a cloudovou databází cen pro automatizaci tvorby rozpočtů.

---

## 🛠️ 1. První nastavení (Instalace)

Pokud instalujete systém do nové tabulky nebo aktualizujete kód, máte dvě možnosti:

**Možnost A: Profesionální (Doporučeno)**
1. V terminálu ve složce projektu napište: `clasp push`.
2. Všechny soubory se automaticky nahrají do vašeho Apps Scriptu.

**Možnost B: Manuální**
1. V Google Sheets otevřete **Rozšíření -> Apps Script**.
2. **Soubor Code.gs:** Vložte obsah souboru `gas/Cenar.js`.
3. **HTML soubory:** Vytvořte nové soubory `Sidebar`, `UploadPanel` a `LaborSuggestions` a vložte do nich obsah odpovídajících `.html` souborů ze složky `gas/`.

Po nahrání uložte (Ctrl+S) a obnovte kartu s tabulkou (F5). V horním menu se objeví **🤖 AI Asistent**.

---

## 📋 2. Práce s rozpočtem (Sidebar)

Panel otevřete přes menu: **🤖 AI Asistent -> Otevřít panel**.

### Oceňování položek (3-sloupcový systém)
Systém nyní pracuje se třemi sloupci:
- **Sloupec C (Popis):** Text položky k ocenění
- **Sloupec I (Materiál):** Cena materiálu z dodavatelských nabídek
- **Sloupec J (Práce):** Cena montáže z interních rozpočtů

1.  Označte v tabulce buňky s popisy položek.
2.  Klikněte na **🚀 Ocenit označený výběr**.
3.  **Výsledek:** Oba sloupce (I + J) se vyplní najednou.
4.  **Barevná legenda:**
    *   **Zelené pozadí:** Manuální výběr z menu – 100% potvrzeno.
    *   **Oranžové pozadí:** Shoda je nižší než 60 % (zkontrolujte položku).
    *   **Bez pozadí:** Automatická shoda nad 60% (OK).
    *   **Poznámka u buňky:** Obsahuje název z DB, % shody, zdroj a datum ceny.

### 🎯 Menu kandidátů (kontextové nabídky)
Pokud kliknete na buňku ve sloupci Materiál (I) nebo Práce (J):
1.  V sidebaru se automaticky zobrazí **Top kandidáti** pro daný typ.
2.  Vyberte správnou položku jedním klikem.
3.  Buňka se **zazelení** (manuální výběr = 100% správně).

### Historie a grafy
*   Klikněte na jakoukoliv oceněnou buňku.
*   Klikněte na **🔍 Zobrazit graf**. V panelu se vykreslí vývoj ceny této položky v čase.
*   Tlačítko **📋 Načíst z buňky** přenese text z vybrané buňky přímo do vyhledávacího pole v panelu.

### 📤 2.5 Nahrávání podkladů (Integrita Dat)
Pro udržení čistoty dat systém striktně rozděluje zdroje:

1.  **📦 Nabídky (Materiál)** - nahrávejte sem PDF/XLS od dodavatelů (DEK, Argos...). Systém z nich čerpá **pouze ceny materiálu**.
2.  **🔨 Rozpočty (Práce)** - nahrávejte sem vaše interní XLS rozpočty. Systém z nich čerpá **pouze ceny montáže**.

*Tip: Stačí zvolit správné tlačítko v nahrávacím panelu. Pokud nahrajete rozpočet jako "Práci", systém automaticky ignoruje ceny materiálu, které v něm jsou, aby vám nezkreslily historii tržních cen.*

---

## ⚙️ 3. Správa databáze (Admin Sheet)

Pro hromadné úpravy cen a názvů slouží dedikovaný list.

### Načtení a úprava
1.  V menu klikněte na **⚙️ Správa: Načíst databázi**.
2.  Vytvoří se list `ADMIN_DATABASE` se všemi položkami z cloudu.
3.  Zde můžete libovolně měnit názvy, ceny nebo jednotky.
4.  Po úpravách klikněte na **💾 Správa: Uložit změny**. Změny se odešlou do cloudu.
    *   *Poznámka:* Změna ceny vytvoří v DB nový historický záznam (zachováváme historii). Změna názvu aktualizuje název položky.

### Inteligentní filtrování
*   Pokud v rozpočtu narazíte na položku, kterou chcete v DB opravit:
*   Stůjte na této položce a v menu klikněte na **🔍 Filtrovat DB podle výběru**.
*   Skript vás přepne do `ADMIN_DATABASE` a automaticky vyfiltruje přesně tuto položku.

### Mazání (Blacklist)
*   Pokud je v databázi nesmyslná položka, označte ji (v rozpočtu nebo v Admin listu).
*   V panelu klikněte na **🗑️ Smazat položku z DB**. Položka se už nikdy nebude nabízet.

### 🧨 Úplný reset (Nukleární tlačítko)
*   Pokud chcete začít úplně od nuly, běžte do menu: **🤖 AI Asistent -> 🧨 RESET CELÉ DATABÁZE**.
*   Systém vyžaduje dvě potvrzení (druhé potvrzení vyžaduje vepsání slova `SMAZAT`).
*   **Varování:** Tato akce trvale vymaže veškerá data v databázi (názvy, ceny, historii).

---

## 🚀 4. Aktualizace systému

Systém běží na cloudu Render.com. Pokud dojde k úpravě backendu (Python kód):
1.  Změny se pushnou na GitHub.
2.  Render automaticky provede "Redeploy" (trvá cca 2 minuty).
3.  Stav serveru můžete kdykoliv zkontrolovat v panelu (Status: Online/Offline).

---

## ❓ 5. Řešení problémů

*   **Skript se zasekl:** Obnovte stránku tabulky (F5).
*   **Vrací to 0.00 Kč:** Položka nebyla v databázi nalezena s dostatečnou shodou. Zkuste ji přidat ručně přes tlačítko **➕ Přidat do DB**.
*   **Chyba oprávnění:** Google se může zeptat na schválení skriptu (při prvním spuštění). Klikněte na "Advanced" and "Go to... (unsafe)".
