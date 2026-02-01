# 🧠 Budoucí vize a strategický rozvoj (Brainstorming)

Tento dokument slouží jako pracovní prostor pro debatu o dalším směřování projektu **AI Cenový Asistent** se zaměřením na **elektro práce**.

---

## 🏗️ 1. Analýza klíčových funkcí (Prioritizace)
*Srovnání nápadů pro další rozvoj systému.*

| Funkce | Popis | Priorita |
| :--- | :--- | :--- |
| **Našeptávač prací (Labor Matcher)** | K oceněnému materiálu automaticky navrhne odpovídající montážní práci z DB. | **KRITICKÝ (P0)** |
| **Hromadná aktualizace cen** | Pro nově načtenou nabídku v Excelu aktualizuje všechny ceny jedním klikem podle DB. | **VYSOKÝ (P1)** |
| **Projektový vítěz (Bid Compare)** | Celkový přehled u srovnání cen - automatické vyhodnocení nejvýhodnějšího dodavatele pro akci. | **STŘEDNÍ (P2)** |
| **Kontext u tras (Trubky/Žlaby)** | Vazba hlavní prvek -> příslušenství (spojky, výložníky). | **NÍZKÝ (Budoucnost)** |
| **Quantity Takeoff (PDF)** | Automatické počítání prvků z výkresů. | **FOOTNOTE** |

---

## 🎯 2. Detailní rozpracování konceptů

### A. Elektro Našeptávač prací (Labor Matcher) - HLAVNÍ CÍL
- **Koncept:** Primární fokus na vazbu **Materiál -> Montáž**. 
- **Příklad:** Pokud uživatel v tabulce ocení *"Kabel CYKY-J 3x1.5"*, v Sidebaru se v nové sekci "Doporučená práce" objeví nalezené montážní položky (např. *"Montáž kabelu do 0,4kg fixed"* nebo *"Uložení pod omítku"*).
- **Změna oproti původnímu:** V této fázi neřešíme sady materiálu (kity), ale čistě doručování správné ceny za práci k vybranému materiálu.

### B. Hromadná aktualizace rozpočtu (Smart Sync)
- **Koncept:** Funkce pro starší nebo nově importované rozpočty. Systém projde označenou oblast v Excelu a u všech položek, které už zná z DB, aktualizuje jednotkovou cenu na aktuální úroveň.
- **Přínos:** Okamžité přecenění starých akcí na aktuální tržní ceny.

### C. Celkový vítěz (Project Winner)
- **Koncept:** Rozšíření srovnávací tabulky v Sidebaru. Kromě historie jednotlivých položek systém dokáže analyzovat celou skupinu položek (balík) a říct, který dodavatel (např. DEOS vs. Elfetex) je pro daný celek celkově výhodnější.

---

## 📅 3. Navržený postup (Roadmapa)

1. **Fáze 7: Labor Suggestion Engine**
   - Implementace algoritmu pro párování materiálu a odpovídající montáže.
   - UI v Sidebaru pro rychlé přidání práce.

2. **Fáze 8: Batch Update Tool**
   - Vývoj funkce pro hromadnou synchronizaci tabulky s databází.

---

## � 4. Poznámky pod čarou (Footnotes)
- *Quantity Takeoff:* Automatické počítání prvků z PDF výkresů je zajímavý směr, ale v tuto chvíli zůstává pouze jako námět pro vzdálenou budoucnost.
- *Změnové listy:* Tato funkce byla po debatě vyřazena jako nadbytečná pro současný scope.

---
*(Poslední aktualizace: 2026-02-01)*
