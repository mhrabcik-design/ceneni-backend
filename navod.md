# Návod k použití: AI Asistent pro oceňování rozpočtů

Tento systém propojuje Google Sheets s umělou inteligencí (Gemini) a cloudovou databází cen pro automatizaci tvorby rozpočtů.

---

## 🛠️ 1. První nastavení (Instalace)

Pokud instalujete systém do nové tabulky nebo aktualizujete kód, postupujte takto:

1.  V Google Sheets otevřete **Rozšíření -> Apps Script**.
2.  **Soubor Code.gs:** Vložte obsah souboru `google_sheets_script.js`.
3.  **Nový soubor HTML:** Klikněte na `+` -> `HTML`, pojmenujte ho `Sidebar` a vložte obsah souboru `Sidebar.html`.
4.  Uložte (Ctrl+S) a obnovte kartu s tabulkou (F5).
5.  V horním menu se objeví **🤖 AI Asistent**.

---

## 📋 2. Práce s rozpočtem (Sidebar)

Panel otevřete přes menu: **🤖 AI Asistent -> Otevřít panel**.

### Oceňování položek
1.  Označte v tabulce buňky s popisy položek, které chcete ocenit.
2.  V panelu zvolte, zda hledáte **Materiál** (Dodávka) nebo **Montáž**.
3.  Klikněte na **🚀 Ocenit výběr**.
4.  **Výsledek:**
    *   Do buněk se doplní nejlepší nalezená cena.
    *   **Oranžové pozadí:** Shoda je nižší než 60 % (zkontrolujte položku).
    *   **Poznámka u buňky:** Obsahuje název z DB, % shody, zdroj a datum ceny.

### Historie a grafy
*   Klikněte na jakoukoliv oceněnou buňku.
*   Klikněte na **🔍 Zobrazit graf**. V panelu se vykreslí vývoj ceny této položky v čase.
*   Tlačítko **📋 Načíst z buňky** přenese text z vybrané buňky přímo do vyhledávacího pole v panelu.

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
*   **Chyba oprávnění:** Google se může zeptat na schválení skriptu (při prvním spuštění). Klikněte na "Advanced" a "Go to... (unsafe)".
