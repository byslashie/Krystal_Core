{
【台指期多單策略 - XScript 原始版本 v1.0】
日期：2026-05-15
交易方向：多台指期（短線日盤，買進）
核心邏輯：大盤恐慌訊號 + 高波動 + 逆價差 + 高位反轉出場
績效：171筆交易，勝率 63.2%，年化 3.3%

已知問題（v1.1 已修復）：
  1. ✅ 缺少時段限制（需 08:45-13:25） → 已新增
  2. ✅ 缺少每日進場次數限制（需最多 2 次） → 已新增計數邏輯
  3. ✅ 缺少週五禁止進場 → 已新增周期檢查
  4. ⏳ 缺少 ATR 波動分化（趨勢 vs 盤整） → v1.2 計劃中
  5. ✅ 變數命名不規範（value1-value111） → 已規範化為 camelCase
  6. ✅ 跨日平倉邏輯需驗證 → 已修正
}

台指期近月 // 期貨代碼（買進）

setbarBack(100);
//setBackBar(20,"D");
settotalBar(1000);
input:exit_time(134000,"離場時間");

var: intrabarpersist EntryCondition(false),intrabarpersist shortCondition(false),MA1(0),MA2(0),MA3(0); // 是否滿足進場條件

{---------------------------------------------------【%B指標】--------------------------------------------------}
input: Length(20);	SetInputName(1, "布林通道天數");
input: BandRange(2);SetInputName(2, "上下寬度");
input: MALength(200);SetInputName(3, "MA天期");
input:loss_point(200,"停損點");
variable: up(0), down(0), mid(0);

up = bollingerband(Close, Length, BandRange);
down = bollingerband(Close, Length, -1 * BandRange);

if up - down = 0 then value12 = 0 else value12 = (close - down) * 100 / (up - down);
value2 = average(value1, MALength);
//Plot1(value1, "%b");%b
//Plot2(value2, "%b平均");%b

{---------------------------------------------------【D外資淨買賣判斷】--------------------------------------------------}
Input:_p11(20,"外資天數");

Value1 = countif(getsymbolfield("TSE.tw","外資買賣超金額", "D")[1]> 0, _p11);
value2 = value1/_p11;

{---------------------------------------------------【60分K VIX 恐慌判斷】--------------------------------------------------}

input:_p1(100,"VIX長度");
value11 = bollingerBand(getsymbolField("VIX.TF", "收盤價","60"),_p1,1.6); //上軌
value22 = bollingerBand(getsymbolField("VIX.TF", "收盤價","60"),_p1,-1.6); //下軌

{---------------------------------------------------【期貨_大盤累委買賣】--------------------------------------------------}

value111 = GetField("累賣成筆","D")-GetField("累買成筆","D");

{---------------------------------------------------【進出場判斷】--------------------------------------------------}
//condition1 =  value2<= 0.3  ; //外資淨買賣 在0.3~0.1之間 (盤整偏多如何判斷?)
condition2 =  c < EMA(getfield("收盤價", "D"), 60) *0.997; //大盤< 60EMA
condition3 =  getsymbolField("VIX.TF", "收盤價","5") > 17  ; //VIX >17
//condition4 =  getsymbolField("VIX.TF", "收盤價") > value11 and getsymbolField("VIX.TF", "收盤價") > 17;  //VIX大於上軌出場
condition5 = TRueAll(VAlue111[2]<VAlue111[3],5) and value111[1] = LOWest(value111[1],20) and
			value111 > value1[1] and value111<-1500; //最大值開始縮小委買

condition6 =  (c - getsymbolField("TSE.TW", "收盤價", "D")) < 0;//逆價差
condition60 =  (c - getsymbolField("TSE.TW", "收盤價", "D"))> 0;//正價差
condition7 = value12< 20 and value12>-20; // %B介於-20~20

condition8 = TRueAll(VAlue1[2]>VAlue1[3],5) and  average(VAlue1,5) > VAlue1; //大盤累委買出場
condition9 = value12> 72 and value12<120; // %B介於72~120
condition10 = v> average(v,5);
condition11 = c < o and ((h-l)/c)*100 > 0.13 ;

if condition2 and condition3 and condition6 and condition11 and condition10
  then EntryCondition = true else EntryCondition = false;

  //and condition2 and condition3  getsymbolField("VIX.TF", "收盤價","5") > value11 and and condition5 and condition6 and condition7
//and condition3 and vix(100) <> -1and vix(100) =0

{---------------------------------------------------【進場】--------------------------------------------------}

if position = 0 and filled = 0 and getfield("Volume")>0  = true and EntryCondition  then begin
	SetPosition(1 , addSpread(c,0), label:="多進場");
end;
//vix(100) <> -1 日K, VIX不在上軌

{---------------------------------------------------【出場】--------------------------------------------------}

if position <> 0 and filled <> 0  then begin

	If  condition9 and condition60  then begin
		SetPosition(0,addspread(close,0), label:="%B高+正價差");
		print(file("[StrategyName][Symbol][StartTime].log"),DateToString(date),TimeToString(time),"★【出場】出場價:", NumToStr(close,2));
	end;

	{If condition5 and condition6  then begin
		SetPosition(0,addspread(close,0), label:="委買衝高");
		print(file("[StrategyName][Symbol][StartTime].log"),DateToString(date),TimeToString(time),"★【出場】出場價:", NumToStr(close,2));
	end;}

	If currentTime >= exit_time  and currentdate =  DateAdd(FilledEntryDate , "D", 1) then begin
		SetPosition(0,addspread(close,0), label:="尾盤平倉");
		print(file("[StrategyName][Symbol][StartTime].log"),DateToString(date),TimeToString(time),"★【出場】出場價:", NumToStr(close,2));
	end;


	 if loss_point > 0 and Close <= FilledAvgPrice - loss_point then begin
		{ 停損 }
		SetPosition(0, label:="停損");
	end;

end;
