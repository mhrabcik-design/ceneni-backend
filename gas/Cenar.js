/**
 * AI Cenový Asistent - Google Sheets Bridge
 * Tento kód vložte do: Rozšíření -> Apps Script
 */

const API_BASE_URL = "https://ceneni-backend.onrender.com"; // Cloud Backend (Render + Supabase)

/**
 * Získá nastavení uživatele (sloupce, threshold)
 */
function getSettings() {
    const props = PropertiesService.getUserProperties();
    return {
        threshold: parseFloat(props.getProperty('threshold') || '0.4'),
        colDesc: props.getProperty('colDesc') || 'C',
        colMaterial: props.getProperty('colMaterial') || 'I',
        colLabor: props.getProperty('colLabor') || 'J'
    };
}

/**
 * Uloží nastavení uživatele
 */
function setSettings(settings) {
    const props = PropertiesService.getUserProperties();
    props.setProperty('threshold', settings.threshold.toString());
    props.setProperty('colDesc', settings.colDesc);
    props.setProperty('colMaterial', settings.colMaterial);
    props.setProperty('colLabor', settings.colLabor);
    return true;
}

function onOpen() {
    const ui = SpreadsheetApp.getUi();
    ui.createMenu('🤖 AI Asistent')
        .addItem('Otevřít panel', 'showSidebar')
        .addItem('📤 Nahrát podklady', 'showUploadPanel')
        .addSeparator()
        .addItem('🔍 Filtrovat DB podle výběru', 'filterAdminSheetBySelection')
        .addItem('🚫 Zrušit filtr v DB', 'clearAdminFilter')
        .addSeparator()
        .addSubMenu(ui.createMenu('⚙️ Správa Databáze')
            .addItem('Načíst položky', 'loadAdminSheet')
            .addItem('Uložit změny', 'syncAdminSheet')
            .addItem('Smazat vybrané položky', 'deleteSelectedAdminItems'))
        .addSubMenu(ui.createMenu('🧠 Správa Aliasů (Učení)')
            .addItem('Zobrazit naučené aliasy', 'loadAliasesSheet')
            .addItem('Smazat vybrané aliasy', 'deleteSelectedAliases'))
        .addSeparator()
        .addItem('🧨 RESET CELÉ DATABÁZE', 'resetDatabaseWithConfirmation')
        .addToUi();
}

/**
 * Načte všechny naučené aliasy do nového listu
 */
function loadAliasesSheet() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName("ADMIN_ALIASY");

    if (!sheet) {
        sheet = ss.insertSheet("ADMIN_ALIASY");
    }

    sheet.clear();
    const headers = [["ID Aliasu", "ID Položky", "Hledaný výraz (Alias)", "Cílová položka v DB"]];
    sheet.getRange(1, 1, 1, headers[0].length).setValues(headers).setBackground("#fef7e0").setFontWeight("bold");

    const url = `${API_BASE_URL}/admin/aliases`;
    const options = {
        'method': 'get',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            const data = JSON.parse(response.getContentText());
            if (data && data.length > 0) {
                const rows = data.map(al => [
                    al.id,
                    al.item_id,
                    al.alias,
                    al.item_name
                ]);
                sheet.getRange(2, 1, rows.length, headers[0].length).setValues(rows);
                sheet.setFrozenRows(1);
                sheet.autoResizeColumns(1, 4);
                SpreadsheetApp.getUi().alert(`Načteno ${data.length} naučených aliasů.`);
            } else {
                SpreadsheetApp.getUi().alert("Zatím nebyli naučeni žádné aliasy.");
            }
        }
    } catch (e) {
        SpreadsheetApp.getUi().alert("Chyba při načítání aliasů: " + e.message);
    }
}

/**
 * Smaže vybrané aliasy z databáze
 */
function deleteSelectedAliases() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName("ADMIN_ALIASY");
    if (!sheet || ss.getActiveSheet().getName() !== "ADMIN_ALIASY") {
        SpreadsheetApp.getUi().alert("Tato funkce funguje pouze v listu ADMIN_ALIASY.");
        return;
    }

    const range = sheet.getActiveRange();
    const values = range.getValues();
    const startRow = range.getRow();
    const aliasIds = [];

    // Posbírat ID z prvního sloupce vybrané oblasti
    for (let i = 0; i < values.length; i++) {
        const id = sheet.getRange(startRow + i, 1).getValue();
        if (id && !isNaN(id)) {
            aliasIds.push(parseInt(id));
        }
    }

    if (aliasIds.length === 0) {
        SpreadsheetApp.getUi().alert("Nebyly vybrány žádné aliasy s ID.");
        return;
    }

    const ui = SpreadsheetApp.getUi();
    const confirm = ui.alert('Potvrdit smazání', `Opravdu chcete zapomenout ${aliasIds.length} naučených aliasů?`, ui.ButtonSet.YES_NO);
    if (confirm !== ui.Button.YES) return;

    const url = `${API_BASE_URL}/admin/aliases/batch-delete`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify(aliasIds),
        'muteHttpExceptions': true
    };

    try {
        const res = UrlFetchApp.fetch(url, options);
        if (res.getResponseCode() === 200) {
            // Smazat řádky z listu
            const allData = sheet.getDataRange().getValues();
            for (let i = allData.length - 1; i >= 1; i--) {
                if (aliasIds.includes(parseInt(allData[i][0]))) {
                    sheet.deleteRow(i + 1);
                }
            }
            ui.alert(`Smazáno ${aliasIds.length} aliasů.`);
        } else {
            ui.alert("Chyba při mazání: " + res.getContentText());
        }
    } catch (e) {
        ui.alert("Chyba aplikace: " + e.message);
    }
}

function showSidebar() {
    const html = HtmlService.createHtmlOutputFromFile('Sidebar')
        .setTitle('AI Cenový Asistent')
        .setWidth(300);
    SpreadsheetApp.getUi().showSidebar(html);
}

function showUploadPanel() {
    const html = HtmlService.createHtmlOutputFromFile('UploadPanel')
        .setTitle('Nahrát podklady do databáze')
        .setWidth(450)
        .setHeight(600);
    SpreadsheetApp.getUi().showModalDialog(html, '📦 Centrum nahrávání');
}

/**
 * Otevře vyskakovací okno s návrhy montážních prací
 */
function openLaborSuggestions() {
    const html = HtmlService.createHtmlOutputFromFile('LaborSuggestions')
        .setWidth(600)
        .setHeight(400);
    SpreadsheetApp.getUi().showModalDialog(html, '💡 Návrhy montáže');
}

/**
 * Vrátí název materiálu z aktuálního řádku pro kontext okna
 */
function getSuggestionContext() {
    const sheet = SpreadsheetApp.getActiveSheet();
    const cell = sheet.getActiveCell();
    // Předpokládáme, že popis je ve sloupci C (nebo dle nastavení v sidebaru, ale pro zjednodušení zkusíme aktivní buňku nebo sloupec C)
    const row = cell.getRow();
    const description = sheet.getRange(row, 3).getValue() || cell.getValue();
    return { material: String(description), row: row };
}

/**
 * Volání backendu pro získání doporučených prací
 */
function getLaborSuggestionsFromAPI(materialName) {
    const url = `${API_BASE_URL}/match/labor-suggestions`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify({ 'material_name': materialName }),
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            return JSON.parse(response.getContentText());
        }
    } catch (e) {
        Logger.log("Chyba návrhů: " + e.message);
    }
    return [];
}

/**
 * Vloží nový řádek s vybranou montáží přímo pod aktuální řádek
 */
function insertLaborRow(name, price, itemId) {
    const sheet = SpreadsheetApp.getActiveSheet();
    const activeCell = sheet.getActiveCell();
    const row = activeCell.getRow();

    // Vložit řádek pod
    sheet.insertRowAfter(row);
    const newRow = row + 1;

    // Nastavit název (sloupec C) a cenu (sloupec F - dle tvého standardu)
    sheet.getRange(newRow, 3).setValue(name);
    const priceCell = sheet.getRange(newRow, 6);
    priceCell.setValue(price);

    // Přidat poznámku s ID (důležité pro budoucí identifikaci)
    priceCell.setNote(`🔧 Montážní položka z DB\n🔗 ID: ${itemId}\n📅 Datum: ${new Date().toLocaleDateString('cs-CZ')}`);

    // Volitelně: Formátování (odsazení názvu)
    sheet.getRange(newRow, 3).setHorizontalAlignment("left").setIndent(1);

    return true;
}

/**
 * Vrátí hodnotu aktuálně vybrané buňky
 */
function getActiveCellValue() {
    const cell = SpreadsheetApp.getActiveSheet().getActiveCell();
    return cell ? String(cell.getValue()) : '';
}

/**
 * Hlavní funkce pro ocenění vybrané oblasti - DUAL (Materiál + Práce najednou)
 * @param {string} descColLetter - Sloupec s popisem položky
 * @param {string} materialColLetter - Sloupec pro cenu materiálu
 * @param {string} laborColLetter - Sloupec pro cenu práce
 */
function priceSelectionDual(descColLetter, materialColLetter, laborColLetter) {
    const sheet = SpreadsheetApp.getActiveSheet();
    const range = sheet.getActiveRange();
    const values = range.getValues();
    const startRow = range.getRow();
    const settings = getSettings();

    const descCol = columnLetterToIndex(descColLetter);
    const materialCol = columnLetterToIndex(materialColLetter);
    const laborCol = columnLetterToIndex(laborColLetter);

    // STEP 1: Collect all items
    const itemsToPrice = [];
    const rowMap = {}; // {description: rowIndex}

    for (let i = 0; i < values.length; i++) {
        const currentRow = startRow + i;
        const description = String(sheet.getRange(currentRow, descCol).getValue()).trim();

        if (description && description.length >= 3) {
            itemsToPrice.push(description);
            rowMap[description] = currentRow;
        }
    }

    if (itemsToPrice.length === 0) {
        SpreadsheetApp.getUi().alert('Žádné položky k ocenění (popis příliš krátký nebo prázdný).');
        return;
    }

    // STEP 2: Bulk fetch MATERIAL prices
    const materialResults = fetchMatchBulk(itemsToPrice, 'material', settings.threshold);

    // STEP 3: Bulk fetch LABOR prices
    const laborResults = fetchMatchBulk(itemsToPrice, 'labor', settings.threshold);

    // STEP 4: Apply results to cells
    let matchesFound = 0;

    for (const description of itemsToPrice) {
        const currentRow = rowMap[description];

        // Apply MATERIAL result
        const matchMaterial = materialResults[description];
        if (matchMaterial && matchMaterial.price > 0) {
            const priceCell = sheet.getRange(currentRow, materialCol);
            priceCell.setValue(matchMaterial.price);
            const matchScore = matchMaterial.match_score || 0;
            priceCell.setBackground(matchScore < 0.6 ? '#fff3cd' : null);
            priceCell.setNote(`📦 ${matchMaterial.original_name || 'N/A'}\n📊 Shoda: ${Math.round(matchScore * 100)}%\n🏢 Zdroj: ${matchMaterial.source || 'N/A'}\n📅 Datum: ${matchMaterial.date || 'N/A'}\n🔗 ID: ${matchMaterial.item_id || 'N/A'}`);
            matchesFound++;
        }

        // Apply LABOR result
        const matchLabor = laborResults[description];
        const laborCell = sheet.getRange(currentRow, laborCol);
        if (matchLabor && matchLabor.price > 0) {
            laborCell.setValue(matchLabor.price);
            const matchScore = matchLabor.match_score || 0;
            laborCell.setBackground(matchScore < 0.6 ? '#fff3cd' : null);
            laborCell.setNote(`🔧 ${matchLabor.original_name || 'N/A'}\n📊 Shoda: ${Math.round(matchScore * 100)}%\n🏢 Zdroj: ${matchLabor.source || 'N/A'}\n📅 Datum: ${matchLabor.date || 'N/A'}\n🔗 ID: ${matchLabor.item_id || 'N/A'}`);
        } else {
            laborCell.setValue(0);
            laborCell.setBackground(null);
            laborCell.setNote('🔧 Práce nenalezena v DB');
        }
    }

    SpreadsheetApp.getUi().alert(`Hotovo! Oceněno ${matchesFound} položek (Materiál + Práce) pomocí BULK API.`);
}

// Keep old function for backward compatibility (deprecated)
function priceSelection(descColLetter, priceColLetter, priceType) {
    const sheet = SpreadsheetApp.getActiveSheet();
    const range = sheet.getActiveRange();
    const values = range.getValues();
    const startRow = range.getRow();
    const descCol = columnLetterToIndex(descColLetter);
    const priceCol = columnLetterToIndex(priceColLetter);
    let matchesFound = 0;
    for (let i = 0; i < values.length; i++) {
        const currentRow = startRow + i;
        const description = sheet.getRange(currentRow, descCol).getValue();
        if (!description || String(description).length < 3) continue;
        const settings = getSettings();
        const match = fetchMatch(description, priceType, settings.threshold);
        if (match) {
            const priceCell = sheet.getRange(currentRow, priceCol);
            priceCell.setValue(match.price || 0);
            const matchScore = match.match_score || 0;
            priceCell.setBackground(matchScore < 0.6 ? '#fff3cd' : null);
            priceCell.setNote(`📦 ${match.original_name || 'N/A'}\n📊 Shoda: ${Math.round(matchScore * 100)}%\n🏢 Zdroj: ${match.source || 'N/A'}\n📅 Datum: ${match.date || 'N/A'}\n🔗 ID: ${match.item_id || 'N/A'}`);
            matchesFound++;
        }
    }
    SpreadsheetApp.getUi().alert(`Hotovo! Oceněno ${matchesFound} položek.`);
}

function columnLetterToIndex(letter) {
    let column = 0;
    let length = letter.length;
    for (let i = 0; i < length; i++) {
        column += (letter.charCodeAt(i) - 64) * Math.pow(26, length - i - 1);
    }
    return column;
}

/**
 * Volání backendu pro získání ceny
 * @param {string} description - Popis položky
 * @param {string} priceType - 'material' nebo 'labor'
 */
function fetchMatch(description, priceType, threshold) {
    const settings = getSettings();
    const url = `${API_BASE_URL}/match`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify({
            'items': [description],
            'type': priceType || settings.priceType,
            'threshold': threshold || settings.threshold
        }),
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            const data = JSON.parse(response.getContentText());
            return data[description] || null;
        }
    } catch (e) {
        Logger.log("Chyba při volání API: " + e.message);
    }
    return null;
}

/**
 * Získá kandidáty pro aktuálně vybranou buňku (pokud je v cenovém sloupci Materiál nebo Práce)
 */
function getActiveCellContext() {
    const sheet = SpreadsheetApp.getActiveSheet();
    const cell = sheet.getActiveCell();
    const settings = getSettings();

    const materialColIdx = columnLetterToIndex(settings.colMaterial);
    const laborColIdx = columnLetterToIndex(settings.colLabor);
    const descColIdx = columnLetterToIndex(settings.colDesc);
    const currentCol = cell.getColumn();

    // Určíme typ podle sloupce
    let priceType = null;
    if (currentCol === materialColIdx) {
        priceType = 'material';
    } else if (currentCol === laborColIdx) {
        priceType = 'labor';
    } else {
        return null; // Nejsme v cenovém sloupci
    }

    const row = cell.getRow();
    const description = sheet.getRange(row, descColIdx).getValue();

    if (!description || description.toString().length < 3) return null;

    // Najdeme kandidáty pro příslušný typ
    const match = fetchMatch(description, priceType, settings.threshold);
    if (match && match.candidates && match.candidates.length > 0) {
        return {
            row: row,
            description: description,
            candidates: match.candidates,
            type: priceType
        };
    }
    return null;
}

/**
 * Aplikuje vybraného kandidáta na konkrétní řádek
 */
function applyCandidate(row, candidate, type, query) {
    const sheet = SpreadsheetApp.getActiveSheet();
    const settings = getSettings();

    // Určíme správný sloupec podle typu
    const colIdx = type === 'labor'
        ? columnLetterToIndex(settings.colLabor)
        : columnLetterToIndex(settings.colMaterial);

    const priceField = type === 'labor' ? 'price_labor' : 'price_material';
    const price = candidate[priceField] || 0;

    const priceCell = sheet.getRange(row, colIdx);
    priceCell.setValue(price);

    // Zelená = manuální výběr (100% správně)
    priceCell.setBackground('#d4edda');

    // Přidat poznámku
    const icon = type === 'labor' ? '🔧' : '📦';
    const note = `${icon} ${candidate.item || 'N/A'}\n` +
        `✅ Manuální výběr (100%)\n` +
        `🏢 Zdroj: ${candidate.source || 'N/A'}\n` +
        `📅 Datum: ${candidate.date || 'N/A'}\n` +
        `🔗 ID: ${candidate.id || 'N/A'}`;
    priceCell.setNote(note);

    // AI Feedback - Learn the alias
    if (query && candidate.id) {
        learnFromFeedback(query, candidate.id);
    }

    return true;
}

/**
 * Pošle informaci o manuálním výběru do backendu, aby se systém naučil alias.
 */
function learnFromFeedback(query, itemId) {
    const url = `${API_BASE_URL}/feedback/learn`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify({
            'query': query,
            'item_id': itemId
        }),
        'muteHttpExceptions': true
    };

    try {
        UrlFetchApp.fetch(url, options);
    } catch (e) {
        Logger.log("Chyba při učení aliasu: " + e.message);
    }
}

/**
 * Získá detaily položky pro sidebar (všechny zdroje, cenový graf)
 */
function getItemDetails(itemId) {
    if (!itemId) return null;

    const url = `${API_BASE_URL}/items/${itemId}/details`;
    const options = {
        'method': 'get',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            return JSON.parse(response.getContentText());
        }
    } catch (e) {
        Logger.log("Chyba při načítání detailů: " + e.message);
    }
    return null;
}

/**
 * Smaže položku z databáze (blacklist) a případně i z listu ADMIN_DATABASE
 */
function deleteItem(itemId) {
    if (!itemId) return { success: false, error: "Chybí ID položky" };

    const url = `${API_BASE_URL}/items/${itemId}`;
    const options = {
        'method': 'delete',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            // Pokud jsme v ADMIN_DATABASE, smažeme řádek i vizuálně
            const sheet = SpreadsheetApp.getActiveSheet();
            if (sheet.getName() === "ADMIN_DATABASE") {
                const data = sheet.getDataRange().getValues();
                for (let i = 0; i < data.length; i++) {
                    if (data[i][0] == itemId) {
                        sheet.deleteRow(i + 1);
                        break;
                    }
                }
            }
            return { success: true };
        } else {
            return { success: false, error: response.getContentText() };
        }
    } catch (e) {
        return { success: false, error: e.message };
    }
}

/**
 * Přidá vlastní položku do databáze
 */
function addCustomItem(name, priceMaterial, priceLabor, unit) {
    if (!name) return { success: false, error: "Chybí název položky" };

    const url = `${API_BASE_URL}/items/add`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify({
            'name': name,
            'price_material': priceMaterial || 0,
            'price_labor': priceLabor || 0,
            'unit': unit || 'ks'
        }),
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            return { success: true, data: JSON.parse(response.getContentText()) };
        } else {
            return { success: false, error: response.getContentText() };
        }
    } catch (e) {
        return { success: false, error: e.message };
    }
}

/**
 * Získá ID položky z aktuálně vybraného řádku.
 * Funguje buď v listu ADMIN_DATABASE (bere ID ze sloupce A) 
 * nebo v rozpočtu (bere ID z poznámky).
 */
function getItemIdFromActiveCell() {
    const sheet = SpreadsheetApp.getActiveSheet();
    const cell = sheet.getActiveCell();
    if (!cell) return null;

    // 1. Speciální logika pro ADMIN_DATABASE (ID je v prvním sloupci)
    if (sheet.getName() === "ADMIN_DATABASE") {
        const idValue = sheet.getRange(cell.getRow(), 1).getValue();
        return idValue && !isNaN(idValue) ? parseInt(idValue) : null;
    }

    // 2. Logika pro rozpočet - hledáme v poznámkách (v buňce nebo v celém řádku)
    let note = cell.getNote();
    if (!note) {
        // Prohledat prvních 25 sloupců řádku pro nalezení poznámky s ID
        const rowNotes = sheet.getRange(cell.getRow(), 1, 1, Math.min(sheet.getLastColumn(), 25)).getNotes()[0];
        note = rowNotes.find(n => n && n.includes('🔗 ID:'));
    }

    if (note) {
        const match = note.match(/🔗 ID: (\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    return null;
}


/**
 * Získá historii cen pro danou položku (pro graf)
 */
function getItemHistory(description) {
    if (!description) return null;

    // 1. Najít ID položky podle názvu
    const searchUrl = `${API_BASE_URL}/search?q=${encodeURIComponent(description)}`;
    const options = {
        'method': 'get',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'muteHttpExceptions': true
    };

    try {
        const searchRes = UrlFetchApp.fetch(searchUrl, options);
        if (searchRes.getResponseCode() === 200) {
            const items = JSON.parse(searchRes.getContentText());
            if (items && items.length > 0) {
                const bestMatchId = items[0].id; // Bereme první shodu

                // 2. Stáhnout historii pro toto ID
                const histUrl = `${API_BASE_URL}/items/${bestMatchId}/history`;
                const histRes = UrlFetchApp.fetch(histUrl, options);

                if (histRes.getResponseCode() === 200) {
                    return {
                        "itemName": items[0].name,
                        "history": JSON.parse(histRes.getContentText())
                    };
                }
            }
        }
    } catch (e) {
        Logger.log("Chyba historie: " + e.message);
    }
    return null;
}

function getBackendStatus() {
    try {
        const response = UrlFetchApp.fetch(`${API_BASE_URL}/status`, {
            'headers': { 'bypass-tunnel-reminder': 'true' }
        });
        return JSON.parse(response.getContentText());
    } catch (e) {
        return { "status": "offline" };
    }
}

/**
 * Načte celou databázi do nového listu pro hromadnou editaci
 */
function loadAdminSheet() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName("ADMIN_DATABASE");

    if (!sheet) {
        sheet = ss.insertSheet("ADMIN_DATABASE");
    }

    sheet.clear();
    const headers = [["ID", "Název", "Cena Materiál", "Cena Montáž", "Jednotka", "Poslední Zdroj", "Poslední Datum"]];
    sheet.getRange(1, 1, 1, headers[0].length).setValues(headers).setBackground("#e8f0fe").setFontWeight("bold");

    const url = `${API_BASE_URL}/admin/items`;
    const options = {
        'method': 'get',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            const data = JSON.parse(response.getContentText());
            if (data && data.length > 0) {
                const rows = data.map(item => [
                    item.id,
                    item.name,
                    item.price_material,
                    item.price_labor,
                    item.unit,
                    item.source,
                    item.date
                ]);
                sheet.getRange(2, 1, rows.length, headers[0].length).setValues(rows);
                sheet.setFrozenRows(1);
                SpreadsheetApp.getUi().alert(`Načteno ${data.length} položek.`);
            }
        }
    } catch (e) {
        SpreadsheetApp.getUi().alert("Chyba při načítání: " + e.message);
    }
}

/**
 * Odešle změny z listu ADMIN_DATABASE zpět do databáze
 */
function syncAdminSheet() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName("ADMIN_DATABASE");

    if (!sheet) {
        SpreadsheetApp.getUi().alert("List ADMIN_DATABASE nebyl nalezen. Nejdříve jej načtěte.");
        return;
    }

    const ui = SpreadsheetApp.getUi();
    const response = ui.alert('Synchronizace', 'Opravdu chcete odeslat změny do databáze? Přepíše to aktuální názvy a přidá nové ceny k existujícím ID.', ui.ButtonSet.YES_NO);

    if (response !== ui.Button.YES) return;

    const data = sheet.getDataRange().getValues();
    const headers = data.shift(); // Remove headers

    const itemsToSync = data.filter(row => row[1]).map(row => {
        return {
            id: row[0] ? parseInt(row[0]) : null,
            name: String(row[1]),
            price_material: parseFloat(row[2]) || 0,
            price_labor: parseFloat(row[3]) || 0,
            unit: String(row[4] || "ks")
        };
    });

    const url = `${API_BASE_URL}/admin/sync`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify(itemsToSync),
        'muteHttpExceptions': true
    };

    try {
        const res = UrlFetchApp.fetch(url, options);
        if (res.getResponseCode() === 200) {
            ui.alert(`Synchronizace úspěšná! Synchronizováno ${itemsToSync.length} položek.`);
        } else {
            ui.alert("Chyba při synchronizaci: " + res.getContentText());
        }
    } catch (e) {
        ui.alert("Chyba aplikace: " + e.message);
    }
}

/**
 * Smaže všechny vybrané řádky v listu ADMIN_DATABASE z databáze
 */
function deleteSelectedAdminItems() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName("ADMIN_DATABASE");
    if (!sheet || ss.getActiveSheet().getName() !== "ADMIN_DATABASE") {
        SpreadsheetApp.getUi().alert("Tato funkce funguje pouze v listu ADMIN_DATABASE.");
        return;
    }

    const range = sheet.getActiveRange();
    const values = range.getValues();
    const startRow = range.getRow();
    const itemIds = [];

    // Posbírat ID z prvního sloupce vybrané oblasti
    for (let i = 0; i < values.length; i++) {
        const id = sheet.getRange(startRow + i, 1).getValue();
        if (id && !isNaN(id)) {
            itemIds.push(parseInt(id));
        }
    }

    if (itemIds.length === 0) {
        SpreadsheetApp.getUi().alert("Nebyly vybrány žádné položky s ID.");
        return;
    }

    const ui = SpreadsheetApp.getUi();
    const confirm = ui.alert('Potvrdit smazání', `Opravdu chcete TRVALE SMAZAT ${itemIds.length} položek z databáze?`, ui.ButtonSet.YES_NO);
    if (confirm !== ui.Button.YES) return;

    const url = `${API_BASE_URL}/admin/batch-delete`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify(itemIds),
        'muteHttpExceptions': true
    };

    try {
        const res = UrlFetchApp.fetch(url, options);
        if (res.getResponseCode() === 200) {
            // Smazat řádky z listu (zezadu, aby se nerozhodily indexy)
            const rowsToDelete = [];
            // Musíme znovu najít řádky, protože výběr mohl být nesouvislý
            const allData = sheet.getDataRange().getValues();
            for (let i = allData.length - 1; i >= 1; i--) {
                if (itemIds.includes(parseInt(allData[i][0]))) {
                    sheet.deleteRow(i + 1);
                }
            }
            ui.alert(`Smazáno ${itemIds.length} položek.`);
        } else {
            ui.alert("Chyba při mazání: " + res.getContentText());
        }
    } catch (e) {
        ui.alert("Chyba aplikace: " + e.message);
    }
}

/**
 * Vyfiltruje ADMIN_DATABASE podle názvu položky.
 * Pokud aktivní buňka nemá poznámku, prohledá řádek a zkusí najít poznámku s ID/Názvem.
 */
function filterAdminSheetBySelection() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const activeCell = ss.getActiveCell();
    const sheet = ss.getActiveSheet();
    const activeRow = activeCell.getRow();

    let note = activeCell.getNote();
    let query = activeCell.getValue();
    let filterColumn = 2; // Výchozí: sloupec "Název" (Admin DB)

    // 1. Pokud aktivní buňka nemá poznámku, zkusíme ji najít v rámci stejného řádku
    if (!note) {
        const rowRange = sheet.getRange(activeRow, 1, 1, Math.min(sheet.getLastColumn(), 25));
        const rowNotes = rowRange.getNotes()[0];
        for (let i = 0; i < rowNotes.length; i++) {
            if (rowNotes[i] && rowNotes[i].includes('📦')) {
                note = rowNotes[i];
                break;
            }
        }
    }

    // 2. Pokud jsme našli poznámku (v buňce nebo v řádku), vytáhneme z ní data
    if (note) {
        const nameMatch = note.match(/📦 (.*)/);
        const idMatch = note.match(/🔗 ID: (\d+)/);

        if (nameMatch && nameMatch[1]) {
            query = nameMatch[1].trim().split('\n')[0]; // První řádek za ikonkou
            filterColumn = 2;
        } else if (idMatch && idMatch[1]) {
            query = idMatch[1];
            filterColumn = 1;
        }
    }

    if (!query || String(query).length < 2) {
        SpreadsheetApp.getUi().alert("Vyberte buňku s názvem nebo oceněním. Položka musí mít poznámku nebo text delší než 2 znaky.");
        return;
    }

    const adminSheet = ss.getSheetByName("ADMIN_DATABASE");
    if (!adminSheet) {
        SpreadsheetApp.getUi().alert("List ADMIN_DATABASE nebyl nalezen. Nejdříve jej načtěte.");
        return;
    }

    // Reset a aplikace filtru
    let filter = adminSheet.getFilter();
    if (filter) filter.remove();

    filter = adminSheet.getDataRange().createFilter();

    const criteria = SpreadsheetApp.newFilterCriteria()
        .whenTextContains(query)
        .build();

    filter.setColumnFilterCriteria(filterColumn, criteria);

    adminSheet.activate();
}

/**
 * Zruší veškeré filtry v listu ADMIN_DATABASE
 */
function clearAdminFilter() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const adminSheet = ss.getSheetByName("ADMIN_DATABASE");
    if (adminSheet && adminSheet.getFilter()) {
        adminSheet.getFilter().remove();
    }
}

/**
 * Nukleární možnost: Reset celého systému se dvěma stupni potvrzení.
 */
function resetDatabaseWithConfirmation() {
    const ui = SpreadsheetApp.getUi();

    // 1. Stupeň varování
    const response = ui.alert(
        '🧨 POZOR: ÚPLNÝ RESET DATABÁZE',
        'Tato akce trvale vymaže VŠECHNY položky, ceny i historii z vaší databáze. \n\nOpravdu chcete pokračovat?',
        ui.ButtonSet.YES_NO
    );

    if (response !== ui.Button.YES) return;

    // 2. Stupeň varování - zadání potvrzovacího kódu
    const promptResponse = ui.prompt(
        'POTVRZENÍ SMAZÁNÍ',
        'Pro potvrzení akce napište do pole níže slovo: SMAZAT',
        ui.ButtonSet.OK_CANCEL
    );

    if (promptResponse.getSelectedButton() === ui.Button.OK &&
        promptResponse.getResponseText().trim().toUpperCase() === "SMAZAT") {

        const url = `${API_BASE_URL}/admin/reset-database`;
        const options = {
            'method': 'post',
            'contentType': 'application/json',
            'headers': { 'bypass-tunnel-reminder': 'true' },
            'muteHttpExceptions': true
        };

        try {
            const res = UrlFetchApp.fetch(url, options);
            if (res.getResponseCode() === 200) {
                ui.alert("✅ Hotovo!", "Databáze byla kompletně vyčištěna. Můžete začít s novým importem.", ui.ButtonSet.OK);
                // Pokud máme otevřený ADMIN_DATABASE, vymažeme ho taky
                const adminSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("ADMIN_DATABASE");
                if (adminSheet) adminSheet.clear();
            } else {
                ui.alert("❌ Chyba:", res.getContentText(), ui.ButtonSet.OK);
            }
        } catch (e) {
            ui.alert("❌ Chyba sítě:", e.message, ui.ButtonSet.OK);
        }
    } else {
        ui.alert("❌ Akce zrušena.", "Slovo nebylo zadáno správně.", ui.ButtonSet.OK);
    }
}

