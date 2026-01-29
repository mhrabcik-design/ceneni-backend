/**
 * AI Cenový Asistent - Google Sheets Bridge
 * Tento kód vložte do: Rozšíření -> Apps Script
 */

const API_BASE_URL = "https://ceneni-backend.onrender.com"; // Cloud Backend (Render + Supabase)

function onOpen() {
    const ui = SpreadsheetApp.getUi();
    ui.createMenu('🤖 AI Asistent')
        .addItem('Otevřít panel', 'showSidebar')
        .addToUi();
}

function showSidebar() {
    const html = HtmlService.createHtmlOutputFromFile('Sidebar')
        .setTitle('AI Cenový Asistent')
        .setWidth(300);
    SpreadsheetApp.getUi().showSidebar(html);
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

            // Přidat poznámku s originálním názvem pro transparentnost
            const note = `📦 ${match.original_name || 'N/A'}\n` +
                `📊 Shoda: ${Math.round((match.match_score || 0) * 100)}%\n` +
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

