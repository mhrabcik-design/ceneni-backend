/**
 * AI Cenový Asistent - Google Sheets Bridge
 * Tento kód vložte do: Rozšíření -> Apps Script
 */

const API_BASE_URL = "https://ceneni-backend.onrender.com"; // Cloud Backend (Render + Supabase)

function onOpen() {
    const ui = SpreadsheetApp.getUi();
    ui.createMenu('🤖 AI Asistent')
        .addItem('Otevřít panel', 'showSidebar')
        .addItem('📤 Nahrát podklady', 'showUploadPanel')
        .addSeparator()
        .addItem('🔍 Filtrovat DB podle výběru', 'filterAdminSheetBySelection')
        .addItem('🚫 Zrušit filtr v DB', 'clearAdminFilter')
        .addSeparator()
        .addItem('⚙️ Správa: Načíst databázi', 'loadAdminSheet')
        .addItem('💾 Správa: Uložit změny', 'syncAdminSheet')
        .addItem('🗑️ Správa: SMAZAT VÝBĚR', 'deleteSelectedAdminItems')
        .addToUi();
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
 * Vrátí hodnotu aktuálně vybrané buňky
 */
function getActiveCellValue() {
    const cell = SpreadsheetApp.getActiveSheet().getActiveCell();
    return cell ? String(cell.getValue()) : '';
}

/**
 * Hlavní funkce pro ocenění vybrané oblasti
 * @param {string} descColLetter - Sloupec s popisem položky
 * @param {string} priceColLetter - Sloupec pro cenu
 * @param {string} priceType - 'material' nebo 'labor'
 */
function priceSelection(descColLetter, priceColLetter, priceType) {
    const sheet = SpreadsheetApp.getActiveSheet();
    const range = sheet.getActiveRange();
    const values = range.getValues();
    const startRow = range.getRow();

    // Převod písmen sloupců na indexy (A=1, B=2, C=3)
    const descCol = columnLetterToIndex(descColLetter);
    const priceCol = columnLetterToIndex(priceColLetter);

    let matchesFound = 0;

    for (let i = 0; i < values.length; i++) {
        const currentRow = startRow + i;
        const description = sheet.getRange(currentRow, descCol).getValue();

        if (!description || String(description).length < 3) continue;

        const match = fetchMatch(description, priceType || 'material');
        if (match) {
            const priceCell = sheet.getRange(currentRow, priceCol);
            priceCell.setValue(match.price || 0);

            // Barva podle kvality shody
            const matchScore = match.match_score || 0;
            if (matchScore < 0.6) {
                // Nízká shoda - oranžová (varování)
                priceCell.setBackground('#fff3cd');
            } else {
                // Dobrá shoda - reset na výchozí
                priceCell.setBackground(null);
            }

            // Přidat poznámku s originálním názvem pro transparentnost
            const note = `📦 ${match.original_name || 'N/A'}\n` +
                `📊 Shoda: ${Math.round(matchScore * 100)}%\n` +
                `🏢 Zdroj: ${match.source || 'N/A'}\n` +
                `📅 Datum: ${match.date || 'N/A'}\n` +
                `🔗 ID: ${match.item_id || 'N/A'}`;
            priceCell.setNote(note);
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
function fetchMatch(description, priceType) {
    const url = `${API_BASE_URL}/match`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify({
            'items': [description],
            'type': priceType || 'material'
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

