import yfinance as yf

class StockDataFetcher:
    def __init__(self):
        self.ticker = None

    def set_ticker(self, ticker):
        self.ticker = ticker

    def fetch_data(self, period='2y', interval='1d'):
        if not self.ticker:
            raise ValueError("Ticker symbol not set. Use set_ticker() to set a stock ticker symbol before fetching data.")
        symbol_data = yf.download(self.ticker, period=period, interval=interval, rounding=True)[['Open', 'High', 'Low', 'Close']]
        return symbol_data
