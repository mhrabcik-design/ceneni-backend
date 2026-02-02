# 💡 Budoucí vylepšení a nápady

Tento dokument slouží k ukládání myšlenek na budoucí vylepšení projektu, které aktuálně nejsou prioritou, ale mají potenciál zvýšit hodnotu systému.

## 1. Dohledatelnost položek v originálních dokumentech (ID/Pozice)

### Motivace
Při práci s rozsáhlými PDF nabídkami (desítky stran) může být obtížné zpětně dohledat, kde přesně se konkrétní cena v originálním dokumentu nachází. Většina nabídek používá vlastní číslování (ID položek jako "1.", "2.1", "a)").

### Aktuální stav
- ID položek jsou při extrakci/ukládání odstraňována z názvu, aby nedocházelo k duplicitám a zmatku při vyhledávání.
- Reference na originál je pouze přes název souboru.

### Návrh řešení
1. **Databáze**: Přidat sloupec `source_item_id` (nebo `source_position`) do tabulky `prices`.
2. **AI Extrakce**: Upravit prompt pro Gemini, aby do samostatného pole extrahovalo i toto pořadové číslo/ID z dokumentu.
3. **UI (GAS)**: V sidebaru v Google Sheets zobrazovat toto ID jako informativní popisek u každého nálezu ceny (např. *"Pozice v nab.: 2.14"*).

### Výhody
- Názvy položek zůstanou čisté a snadno vyhledatelné.
- Uživatel získá přesnou navigaci do zdrojového PDF souboru.
