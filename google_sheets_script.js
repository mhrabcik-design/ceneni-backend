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
 */
function priceSelection(descColLetter, priceColLetter) {
    const sheet = SpreadsheetApp.getActiveSheet();
    const range = sheet.getActiveRange();
    const values = range.getValues();
    const startRow = range.getRow();

    // Převod písmen sloupců na indexy (A=1, B=2, C=3)
    const descCol = columnLetterToIndex(descColLetter);
    const priceCol = columnLetterToIndex(priceColLetter);

    let matchesFound = 0;

    for (let i = 0; i < values.length; i++) {
        // Získáme text popisu ze správného sloupce v daném řádku (absolutně na listu)
        const currentRow = startRow + i;
        const description = sheet.getRange(currentRow, descCol).getValue();

        if (!description || String(description).length < 3) continue;

        const match = fetchMatch(description);
        if (match) {
            // Zápis ceny do cílového sloupce
            // Backend vrací 'price' (materiál) a 'price_labor' (práce)
            const totalPrice = (match.price || 0) + (match.price_labor || 0);
            sheet.getRange(currentRow, priceCol).setValue(totalPrice);
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
 * Volání vašeho lokálního Python backendu
 */
function fetchMatch(description) {
    const url = `${API_BASE_URL}/match`;
    const options = {
        'method': 'post',
        'contentType': 'application/json',
        'headers': { 'bypass-tunnel-reminder': 'true' },
        'payload': JSON.stringify({ 'items': [description] }),
        'muteHttpExceptions': true
    };

    try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() === 200) {
            const data = JSON.parse(response.getContentText());
            // Backend vrací dict: { "description": { data... } }
            return data[description] || null;
        }
    } catch (e) {
        Logger.log("Chyba při volání API: " + e.message);
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

