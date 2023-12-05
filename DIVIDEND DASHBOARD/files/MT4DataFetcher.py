import pandas as pd
import os

class MT4DataFetcher:
    def __init__(self, period='1440', base_path=None):
        """
        Initializes an instance of the MT4DataFetcher.

        :param period: The timeframe for the MT4 data, default is '1440' (daily).
        :param base_path: The base path where the MT4 CSV files are stored.
        """
        self.symbol = None
        self.period = period
        self.base_path = base_path or r'C:\Users\sean7\AppData\Roaming\MetaQuotes\Terminal\0BB29DBF61C9F39836A4ED9CF1A954C9\MQL4\Files'

    def set_symbol(self, symbol):
        """
        Sets the symbol for the MT4 data.

        :param symbol: The symbol to fetch data for.
        """
        self.symbol = symbol

    def set_period(self, period):
        """
        Sets the period for the MT4 data.

        :param period: The period to set.
        """
        self.period = period

    def fetch_data(self):
        """
        Fetches the MT4 data for the set symbol and period.

        :return: A DataFrame containing the fetched data.
        """
        if not self.symbol:
            raise ValueError("Symbol not set. Use set_symbol() to set the symbol before fetching data.")

        filename = f'{self.symbol}_{self.period}.csv'
        file_path = os.path.join(self.base_path, filename)

        try:
            col_names = ['Date', 'Open', 'High', 'Low', 'Close']
            df = pd.read_csv(file_path, index_col=0, parse_dates=True, delimiter=';', names=col_names)
            return df
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found at {file_path}")
        except Exception as e:
            raise Exception(f"Error while reading the CSV file: {e}")

