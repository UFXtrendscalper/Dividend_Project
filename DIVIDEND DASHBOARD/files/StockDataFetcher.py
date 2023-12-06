import yfinance as yf

class StockDataFetcher:
    """
    A class for fetching stock data for a specified ticker symbol.

    Attributes:
    -----------
    ticker : str
        A string to store the stock ticker symbol.

    Methods:
    --------
    set_ticker(self, ticker)
        Sets the stock ticker symbol.

    fetch_data(self, period='2y', interval='1d')
        Fetches and returns stock data for the set ticker symbol.
    """
    def __init__(self):
        """
        Initializes the StockDataFetcher class with no ticker set.
        """
        self.ticker = None

    def set_ticker(self, ticker):
        """
        Sets the stock ticker symbol for data fetching.

        Parameters:
        -----------
        ticker : str
            The ticker symbol of the stock for which data is to be fetched.
        """
        self.ticker = ticker

    def fetch_data(self, period='2y', interval='1d'):
        """
        Fetches and returns stock data for the set ticker symbol.

        Parameters:
        -----------
        period : str, optional
            The period over which to fetch stock data (default is '2y', indicating 2 years).
        interval : str, optional
            The interval between data points (default is '1d', indicating 1 day).

        Returns:
        --------
        pandas.DataFrame
            A DataFrame containing stock data with columns for Open, High, Low, and Close values.

        Raises:
        -------
        ValueError
            If the ticker symbol is not set before calling this method.
        """
        if not self.ticker:
            raise ValueError("Ticker symbol not set. Use set_ticker() to set a stock ticker symbol before fetching data.")
        symbol_data = yf.download(self.ticker, period=period, interval=interval, rounding=True)[['Open', 'High', 'Low', 'Close']]
        return symbol_data
