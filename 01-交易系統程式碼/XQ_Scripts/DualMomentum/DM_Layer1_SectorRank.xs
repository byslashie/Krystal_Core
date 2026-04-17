// ============================================================
// 兩層 Dual Momentum 系統 for XQ / XS
// 架構：Layer1 族群篩選 → Layer2 個股排名 → Layer3 執行監控
// 作者：自用版本，每月月底跑一次
// ============================================================

// ============================================================
// [SKILL 1] 族群代表股動能排名
// 檔名：DM_Layer1_SectorRank
// 用途：第一層，判斷哪些族群的動能分數最高
// 候選池：每個族群挑 1 檔市值最大代表股（或族群 ETF）
//
// 使用方式：
//   候選池設為「族群代表股清單」（約 8-10 檔）
//   排行取前 3（或你設定的 topN）
//   輸出這 3 個族群的代碼，記錄下來供 Layer2 使用
// ============================================================

Var:
  mom3(0), mom6(0), mom12(0), score(0);

Input:
  TopN(3, "取前幾個族群");

// 三週期動能分數（對應 63/126/252 交易日）
mom3  := RateOfChange(C, 63);
mom6  := RateOfChange(C, 126);
mom12 := RateOfChange(C, 252);

// 絕對動能過濾：三個週期都必須 > 0 才納入排名
// 符合 Gary Antonacci Absolute Momentum 原則
If (mom3 > 0) AND (mom6 > 0) AND (mom12 > 0) Then
  score := (mom3 + mom6 + mom12) / 3
Else
  score := -9999;  // 任一週期為負 → 強制排除

// 排行（降冪）
Rank myRank Desc Begin
  If score > 0 Then retval := score;
End;

// 取前 TopN 個族群代表股
If myRank.pos <= TopN Then ret := 1;

// 輸出欄位
OutputField1(score,           "族群動能分數");
OutputField2(mom3,            "近3月動能%");
OutputField3(mom6,            "近6月動能%");
OutputField4(mom12,           "近12月動能%");
OutputField5(myRank.pos,      "族群排名");
OutputField6(RateOfChange(C,5), "近5日報酬%");
OutputField7(HVolatility(C, 60), "60日波動度");
