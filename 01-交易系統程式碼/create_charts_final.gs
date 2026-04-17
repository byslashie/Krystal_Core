/**
 * Google Apps Script - Create USD and TWD Charts
 *
 * QUICK START:
 * 1. Open your Google Sheet at: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
 * 2. Click "Extensions" → "Apps Script"
 * 3. Paste ALL of this code (replace everything)
 * 4. Click "Run" button (select createCharts function)
 * 5. Click "Authorize" if prompted
 * 6. Done! Two charts created automatically
 */

function createCharts() {
  const sheet = SpreadsheetApp.getActive();
  const dataSheet = sheet.getSheetByName("daily_nav");

  if (!dataSheet) {
    Logger.log("Error: daily_nav sheet not found");
    return;
  }

  // ===== USD Chart (rows 1-11) =====
  const usdChart = dataSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange("A1:A11"))  // X-axis: dates
    .addRange(dataSheet.getRange("F1:F11"))  // Y-axis: NAV
    .setOption("title", "Daily P&L - USD (美金)")
    .setOption("legend", { position: "bottom" })
    .setOption("pointSize", 4)
    .setOption("lineWidth", 2)
    .setOption("colors", ["#1f77b4"])
    .setOption("hAxis", { title: "Date" })
    .setOption("vAxis", { title: "NAV", minValue: 0 })
    .setPosition(2, 8, 0, 0);  // Row 2, Column H

  dataSheet.insertChart(usdChart.build());
  Logger.log("✓ USD chart created");

  // ===== TWD Chart (rows 12-18) =====
  const twdChart = dataSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange("A12:A18"))  // X-axis: dates
    .addRange(dataSheet.getRange("F12:F18"))  // Y-axis: NAV
    .setOption("title", "Daily P&L - TWD (台幣)")
    .setOption("legend", { position: "bottom" })
    .setOption("pointSize", 4)
    .setOption("lineWidth", 2)
    .setOption("colors", ["#ff7f0e"])
    .setOption("hAxis", { title: "Date" })
    .setOption("vAxis", { title: "NAV", minValue: 0 })
    .setPosition(12, 8, 0, 0);  // Row 12, Column H

  dataSheet.insertChart(twdChart.build());
  Logger.log("✓ TWD chart created");

  Logger.log("✓✓✓ SUCCESS! Both charts created!");
}
