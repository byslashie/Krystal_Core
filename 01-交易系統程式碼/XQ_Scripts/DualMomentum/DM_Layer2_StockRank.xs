// ============================================================
// [SKILL 2] 族群內個股動能排名
// 檔名：DM_Layer2_StockRank
// 用途：第二層，在入選族群的成員股裡選動能最強個股
//
// 使用方式：
//   候選池設為「Layer1 入選族群的所有成員股」
//   可在 XQ 建立「動態群組」= Layer1 結果的成員
//   或每月手動把 Layer1 前 3 族群的成員貼進候選池
//   排行取前 TopStocks 檔
// ============================================================

Var:
  mom3(0), mom6(0), mom12(0), score(0), vol60(0);

Input:
  TopStocks(2, "每族群取幾檔");
  MinLiquidity(3, "最低日均成交金額(億)");

// 流動性過濾（Gary Antonacci：避免中小型股執行成本侵蝕報酬）
// 近 20 日平均成交金額，單位：元
// 3億以下排除
Var: avgValue(0);
avgValue := Average(Amount, 20) / 100000000;  // 轉換為億元

If avgValue < MinLiquidity Then Begin
  ret := 0;
  Exit;
End;

// 三週期動能
mom3  := RateOfChange(C, 63);
mom6  := RateOfChange(C, 126);
mom12 := RateOfChange(C, 252);

// 絕對動能過濾：三週期全正才進入排名
If (mom3 > 0) AND (mom6 > 0) AND (mom12 > 0) Then
  score := (mom3 + mom6 + mom12) / 3
Else
  score := -9999;

// 排行（降冪）
Rank myRank Desc Begin
  If score > 0 Then retval := score;
End;

If myRank.pos <= TopStocks Then ret := 1;

// 輸出欄位
OutputField1(score,              "個股動能分數");
OutputField2(mom3,               "近3月%");
OutputField3(mom6,               "近6月%");
OutputField4(mom12,              "近12月%");
OutputField5(myRank.pos,         "族群內排名");
OutputField6(avgValue,           "日均成交(億)");
OutputField7(HVolatility(C, 60), "60日波動");
OutputField8(RateOfChange(C, 5), "近5日報酬%");
