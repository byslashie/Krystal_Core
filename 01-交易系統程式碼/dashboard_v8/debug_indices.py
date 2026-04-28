import yfinance as yf
import pandas as pd

INDEX_META = [
    {'id': 'dji',    'label': '道瓊工業',  'ticker': '^DJI',  'flag': 'us', 'country': '美國'},
    {'id': 'spx',    'label': 'S&P 500',   'ticker': '^GSPC', 'flag': 'us', 'country': '美國'},
    {'id': 'nasdaq', 'label': '納斯達克',   'ticker': '^IXIC', 'flag': 'us', 'country': '美國'},
    {'id': 'twii',   'label': '台灣加權',   'ticker': '^TWII', 'flag': 'tw', 'country': '台灣'},
    {'id': 'otc',    'label': '櫃買指數',   'ticker': '^TWOII', 'flag': 'tw', 'country': '台灣'},
    {'id': 'n225',   'label': '日經 225',   'ticker': '^N225', 'flag': 'jp', 'country': '日本'},
]

for meta in INDEX_META:
    try:
        print(f"Fetching {meta['ticker']}...")
        tkr = yf.Ticker(meta['ticker'])
        hist = tkr.history(period='1y')
        print(f"  {meta['ticker']} length: {len(hist)}")
        if len(hist) < 5:
            print(f"  {meta['ticker']} SKIPPED (too short)")
    except Exception as e:
        print(f"  {meta['ticker']} ERROR: {e}")
