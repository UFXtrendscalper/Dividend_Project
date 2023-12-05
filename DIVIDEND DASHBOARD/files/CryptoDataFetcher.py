import requests
from datetime import datetime, timedelta
import pandas as pd

class CryptoDataFetcher:
    def __init__(self):
        self.symbol = None

    def set_symbol(self, symbol):
        self.symbol = symbol

    def fetch_data(self, period='1day'):
        # note VIP0 is 2000 requests per 30 seconds
        # Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
        # check if symbol is set
        if not self.symbol:
            raise ValueError("Symbol not set. Use set_symbol() to set a cryptocurrency symbol before fetching data.")

        start_date = datetime.now() - timedelta(days=730)
        end_date = datetime.now()

        url = f'https://api.kucoin.com/api/v1/market/candles?type={period}&symbol={self.symbol}&startAt={int(start_date.timestamp())}&endAt={int(end_date.timestamp())}'

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data['data'], columns=['Date', 'Open', 'Close', 'High', 'Low', 'Volume', 'Turnover'])
            df['Date'] = pd.to_datetime(df['Date'], unit='s')
            df.set_index('Date', inplace=True)
            df = df.astype(float).sort_index(ascending=True)[['Open', 'High', 'Low', 'Close']]
            return df
        except requests.RequestException as e:
            # Handle different types of exceptions appropriately here
            print(f"Error fetching data: {e}")
            return None