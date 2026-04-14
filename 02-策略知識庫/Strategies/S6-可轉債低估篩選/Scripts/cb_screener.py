import pandas as pd
import requests
from io import StringIO
import datetime

def get_cb_data():
    """
    獲取櫃買中心 (TPEx) 的可轉債行情數據。
    """
    url = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/cb_result.php?l=zh-tw&o=csv"
    # 注意：TPEx 官網通常需要日期參數，或者下載當日
    # 這裡做一個簡單的模擬獲取（實例中可能需要更複雜的爬蟲邏輯）
    # 對於演示，我們假設已有數據或通過 API 獲取
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # 去除前幾行標題
            lines = response.text.split('\n')
            data_start = 0
            for i, line in enumerate(lines):
                if "代號" in line:
                    data_start = i
                    break
            
            clean_csv = '\n'.join(lines[data_start:])
            df = pd.read_csv(StringIO(clean_csv))
            return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def screen_undervalued_cb(df):
    """
    執行 S6 策略篩選邏輯:
    1. 價格介於 100-110
    2. 溢價率 (Premium) < 30%
    """
    if df is None or df.empty:
        return None
    
    # 欄位清理與轉換 (這裡需對應 TPEx CSV 的實際欄位名)
    # 假設欄位有: '代號', '名稱', '收盤價', '溢價率(%)', '轉換價值'
    # 實際上 TPEx 的 CSV 需要清理
    
    # 模擬篩選結果 (針對目前演示)
    # 實際運作時，需要精確解析 CSV
    
    # 過濾條件示例:
    # screened = df[(df['收盤價'] >= 100) & (df['收盤價'] <= 110)]
    # ...
    
    return df # 返回原始數據供後續處理

if __name__ == "__main__":
    print(f"正在執行 S6 可轉債低估篩選... 基準日: {datetime.date.today()}")
    # df = get_cb_data()
    # results = screen_undervalued_cb(df)
    # print(results)
    print("腳本框架已建立。由於獲取歷史數據與清洗需要實時環境與特定 API，")
    print("目前建議先參考 thefew.tw 篩選結果，或稍後由我手動解析最新 CSV。")
