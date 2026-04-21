/**
 * Google Apps Script to create USD and TWD charts in daily_nav sheet
 *
 * USAGE:
 * 1. Open your Google Sheet
 * 2. Click Extensions → Apps Script
 * 3. Paste this entire code into the editor
 * 4. Click Run (select createDailyNavCharts)
 * 5. Authorize if needed
 * 6. Two charts will be automatically created!
 */

function createDailyNavCharts() {
  const spreadsheet = SpreadsheetApp.getActive();
  const sheet = spreadsheet.getSheetByName("daily_nav");

  if (!sheet) {
    Logger.log("Error: daily_nav sheet not found");
    return;
  }

  // USD Chart (rows 1-11: header + 10 USD records)
  const usdChartBuilder = sheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange("A1:F11"))
    .setOption("title", "Daily P&L - USD (美金)")
    .setOption("curveType", "function")
    .setOption("legend", { position: "bottom" })
    .setOption("pointSize", 5)
    .setOption("lineWidth", 2)
    .setPosition(2, 8, 0, 0);

  sheet.insertChart(usdChartBuilder.build());
  Logger.log("USD chart created");

  // TWD Chart (rows 12-18: 7 TWD records)
  const twdChartBuilder = sheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange("A12:F18"))
    .setOption("title", "Daily P&L - TWD (台幣)")
    .setOption("curveType", "function")
    .setOption("legend", { position: "bottom" })
    .setOption("pointSize", 5)
    .setOption("lineWidth", 2)
    .setPosition(12, 8, 0, 0);

  sheet.insertChart(twdChartBuilder.build());
  Logger.log("TWD chart created");

  Logger.log("SUCCESS: Both charts created!");
}
