import dash
import os
import pickle
import requests
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, State, callback, dash_table 
from plotly.subplots import make_subplots
from datetime import date
from dotenv import load_dotenv
from files.TradingBotController import TradingBotController
from files.StockDataFetcher import StockDataFetcher
from files.CryptoDataFetcher import CryptoDataFetcher
from files.MT4DataFetcher import MT4DataFetcher
from files.ForecastProcessor import ForecastProcessor
from files.DataProcessor import DataProcessor
from files.DataVisualizer import DataVisualizer

load_dotenv('.env')

#################### Object Instantiation ####################
bot_controller = TradingBotController()
stock_data_fetcher = StockDataFetcher()
crypto_data_fetcher = CryptoDataFetcher()
mt4_data_fetcher = MT4DataFetcher()
#################### FUNCTIONS ####################

def download_market_data(tickers, period='1y', interval='1d'):
    """Downloads historical market data for given tickers."""
    try:
        return yf.download(tickers, period=period, interval=interval, group_by='ticker', rounding=True)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def prepare_chart_data(data, tickers):
    """Prepares data for chart plotting, including calculating averages and generating titles."""
    ticker_names = []
    avg_prices = {}
    for ticker in tickers:
        ticker_name = TICKER_TO_NAME_MAP.get(ticker, ticker)
        last_close = data[ticker].Close[-1]
        ticker_names.append(f"{ticker_name}: ${last_close}")
        avg_prices[ticker] = data[ticker]['Close'].mean()
    return ticker_names, avg_prices

def create_subplot(ticker_names, data, avg_prices, tickers):
    """Creates a subplot of market data."""
    market_charts = make_subplots(rows=1, cols=len(tickers), subplot_titles=ticker_names)
    return market_charts

def customize_chart_layout(market_charts, data, ticker_names, avg_prices, tickers):
    """Customizes the layout of the chart."""
    # Add a line chart for each ticker to the subplot
    for i, ticker in enumerate(tickers, start=1):
        market_charts.add_trace(
            go.Scatter(x=data[ticker].index, y=data[ticker]['Close'], name=ticker_names[i-1]),
            row=1, col=i
        )
        # Add a horizontal line showing the average price
        market_charts.add_hline(
            y=avg_prices[ticker], 
            line_dash="dash", 
            annotation_text=f"Avg: ${avg_prices[ticker]:.2f}",
            annotation_position="bottom right",
            annotation_bgcolor="grey",
            row=1, col=i
        )

    # Update the layout to set the visual style and size of the charts
    market_charts.update_layout(
        template='plotly_dark',
        title='Market Watch 📈',
        title_font_family="Rockwell",
        title_font_size=24,
        title_x=0.5,
        width=1500,  # Adjusted for 4 charts
        height=400,
        margin=dict(l=10, r=15, t=90, b=20),
        showlegend=False
    )
    # Update hover label settings for better readability
    market_charts.update_layout(hoverlabel=dict(font_size=12, font_family="Rockwell", bgcolor='black', font_color='white'))

    # Update the x and y axes for each chart for aesthetics
    for i in range(1, 5):
        market_charts.update_xaxes(title='', showgrid=True, showticklabels=True, row=1, col=i)
        market_charts.update_yaxes(title='', showgrid=False, showticklabels=False, row=1, col=i)

    return market_charts    

def create_indices_charts(tickers=['^VIX', '^GSPC', 'CL=F', 'GC=F'], period='1y', interval='1d'):
    """
    Generates a subplot of line charts for different market indices.
    """
    data = download_market_data(tickers, period, interval)
    if data is None:
        return None

    ticker_names, avg_prices = prepare_chart_data(data, tickers)
    market_charts = create_subplot(ticker_names, data, avg_prices, tickers)
    market_charts = customize_chart_layout(market_charts, data, ticker_names, avg_prices, tickers)
    return market_charts

def load_and_combine_tickers(CRYPTO_TICKERS, MT4_TICKERS, ETF_TICKERS):
    # get the Ticker column from the dividend excel file
    dividend_tickers = pd.read_excel('data/Dividend_Dashboard.xlsx', sheet_name='current_holdings', usecols='G') 
    # convert divedend tickers to a list
    dividend_tickers = dividend_tickers['Ticker'].tolist()
    # sort the list
    dividend_tickers.sort()
    tickers = ETF_TICKERS + CRYPTO_TICKERS + MT4_TICKERS + dividend_tickers
    return tickers

def splice_data(df, num_bars):
    # todo: add a doc string
    # return th complete dataframe if num_bars is 0
    if num_bars >= 700:
        return df
    else:
        data = df.copy()
        return data.tail(num_bars + 90) # add 90 to account for the 90 day forecast
    
def getAdjustedSymbolNameForChart(symbol):
    # check if symbol is in the ticker dictionary
    if symbol in TICKER_DICT:
        return TICKER_DICT[symbol]
    return symbol

def process_stock_data(symbol):
    print('\nprocessing daily stock', symbol)
    # set the ticker
    stock_data_fetcher.set_ticker(symbol)
    # fetch the data
    data = stock_data_fetcher.fetch_data()
    # prepare the data for prophet
    prep_data = DataProcessor.prepare_data_for_prophet(data)
    # forecast the data 
    forecast = ForecastProcessor.prophet_forecast(prep_data)
    processed_forecast = DataProcessor.process_prophet_forecast(forecast)
    # merge the dataframes 
    MERGED_DATA[symbol] = DataProcessor.merge_dataframes_for_prophet(data, processed_forecast)
    # slice the merged data using the num_bars as a percentage
    stock_slice_df = splice_data(MERGED_DATA[symbol], 100)
    return create_chart_figure(stock_slice_df, symbol, 'Daily')

def process_crypto_data(symbol, timeframe):
    print(f'\nprocessing {timeframe} crypto', symbol)
    # Choose the appropriate period based on the timeframe
    period = '1hour' if timeframe == '1hour' else '1day'
    freq = 'H' if timeframe == '1hour' else 'D'
    # set the symbol
    crypto_data_fetcher.set_symbol(symbol)
    # fetch the data
    crypto_df = crypto_data_fetcher.fetch_data(period=period)
    # prepare the data for prophet
    prep_data = DataProcessor.prepare_data_for_prophet(crypto_df)
    # forecast the data 
    forecast = ForecastProcessor.prophet_forecast(prep_data, freq=freq)
    # process the forecasted data 
    processed_forecast = DataProcessor.process_prophet_forecast(forecast)
    # merge the dataframes
    MERGED_DATA[symbol] = DataProcessor.merge_dataframes_for_prophet(crypto_df, processed_forecast) 
    if timeframe == '1hour':
        # For hourly data, slice to show the last 291 rows
        crypto_slice_df = MERGED_DATA[symbol].iloc[-291:]
    else:
        # For daily data, use splice_data function
        crypto_slice_df = splice_data(MERGED_DATA[symbol], 100)
    return create_chart_figure(crypto_slice_df, symbol, timeframe)

def process_mt4_data(symbol):
    print('\nprocessing mt4', symbol)
    # set the symbol
    mt4_data_fetcher.set_symbol(symbol)
    timeframe = 'Daily'
    freq = 'D'
    mt4_data = mt4_data_fetcher.fetch_data()
    # prepare the data for prophet
    prep_data = DataProcessor.prepare_data_for_prophet(mt4_data)
    # forecast the data 
    forecast = ForecastProcessor.prophet_forecast(prep_data, freq=freq)
    # process the forecasted data 
    processed_forecast = DataProcessor.process_prophet_forecast(forecast)
    # merge the dataframes
    MERGED_DATA[symbol] = DataProcessor.merge_dataframes_for_prophet(mt4_data, processed_forecast)
    # slice the merged data using the num_bars as a percentage
    mt4_slice_df = splice_data(MERGED_DATA[symbol], 100)
    return create_chart_figure(mt4_slice_df, symbol, timeframe)

def create_chart_figure(data_slice, symbol, timeframe):
    chart_symbol_title = getAdjustedSymbolNameForChart(symbol)
    fig = DataVisualizer.create_candlestick_chart(data_slice, chart_symbol_title, timeframe)
    return fig

def process_chart_pipeline(symbol, show_hourly_chart=False):
    if symbol in CRYPTO_TICKERS:
        timeframe = '1hour' if show_hourly_chart else '1day'
        return process_crypto_data(symbol, timeframe)
    elif symbol in MT4_SYMBOLS:
        return process_mt4_data(symbol)
    else:
        return process_stock_data(symbol)
        

def fetch_dividend_data(ticker, api_key):
    """
    Fetches the dividend data for a given stock ticker using the Polygon API.

    Parameters:
    ticker (str): The stock ticker symbol.
    api_key (str): Your Polygon API key.

    Returns:
    DataFrame: A DataFrame containing dividend information.
    """
    # Format the URL for the API request, including the ticker symbol and API key
    url = f'https://api.polygon.io/v3/reference/dividends?ticker={ticker}&limit=1&apiKey={api_key}'

    # Make a GET request to the API and parse the JSON response
    response = requests.get(url).json()

    # Check if the response contains results and return an empty DataFrame if not
    if not response.get('results'):
        return pd.DataFrame()

    # Convert the extracted data into a Pandas DataFrame
    dividend_df = pd.DataFrame(response['results'])

    # Select and retain only the specified columns in the DataFrame
    dividend_df = dividend_df[['ticker', 'cash_amount', 'ex_dividend_date', 'frequency', 'pay_date']]

    return dividend_df

def create_table(ticker):
    try:
        table_df = fetch_dividend_data(ticker, POLYGON_API_KEY)
    except:
        table_df = pd.DataFrame()
    return dash_table.DataTable(
                id='dividend_table',
                    columns=[
                        {
                            "name": i, 
                            "id": i,
                            "type": "numeric",
                            "format": MONEY_FORMAT if i in ['cash_amount'] else None
                        } for i in table_df.columns],
                    data=table_df.to_dict('records'),
                    cell_selectable=False,
                    style_header={'textAlign': 'center', 'backgroundColor': '#1E1E1E', 'fontWeight': 'bold', 'color': 'white'},
                    style_cell_conditional=[
                        {
                            'if': { 'column_id': ['ticker', 'frequency', 'cash_amount', 'ex_dividend_date', 'pay_date'] },
                            'textAlign': 'center',
                        }
                    ],
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#1E1E1E',
                            'color': 'white',
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'row_index': 'even'},
                            'backgroundColor': '#adaaaa',  # A light grey for even rows
                            'color': 'black',
                            'fontWeight': 'bold'
                        },
                    ],
                    style_as_list_view=False,
                    style_table={'overflowX': 'scroll', 'width': '100%'}, 
            )


#################### CONSTANTS ####################
CRYPTO_TICKERS = ['BTC-USDC', 'ETH-USDC']
MT4_SYMBOLS = ["USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "GBPUSD", "EURUSD", "OILUSe", "XAUUSD", "S&P500e"] 
ETF_SYMBOLS = ['SPLG', 'GLD']
TICKERS = load_and_combine_tickers(CRYPTO_TICKERS, MT4_SYMBOLS, ETF_SYMBOLS)
TICKER_DICT = {'USDCAD':'USD/CAD', 'USDJPY':'USD/JPY', 'USDCHF':'USD/CHF', 'EURUSD':'EUR/USD', 'GBPUSD':'GBP/USD', 'AUDUSD':'AUD/USD', 'NZDUSD':'NZD/USD', 'OILUSe':'Crude Oil', 'XAUUSD':'Gold Futures', 'GLD':'Gold ETF', 'S&P500e':'S&P 500 Futures', 'SPLG':'S&P 500 ETF', 'BTC-USDC':'Bitcoin', 'ETH-USDC':'Ethereum'}
TODAYS_DATE = date.today()
POLYGON_API_KEY = os.environ.get('POLYGON_IO_API')
ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_CO_API')
MONEY_FORMAT = dash_table.FormatTemplate.money(2)
MERGED_DATA = {}
# Map of ticker symbols to human-readable names
TICKER_TO_NAME_MAP = {
    '^VIX': 'VIX Volatility Index',
    '^GSPC': 'S&P 500 Index',
    'CL=F': 'Crude Oil',
    'GC=F': 'Gold'
}


dash.register_page(__name__, path='/market_watch', name='Market Watch 📈')

#################### PAGE LAYOUT ####################
layout = html.Div(children=[
        html.Br(),
        html.Div(children=[
            dcc.Graph(figure=create_indices_charts()),
        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'width': '100%'}),
        html.Hr(style={'color': 'white'}),
        dcc.Loading(id='loading_chart', children=[
            html.Div([
                html.Div([
                    html.H4('Select Ticker:', style={'width': '100%'}),
                    dcc.Dropdown(id='ticker_dropdown', 
                                options=[{'label': TICKER_DICT[ticker], 'value': ticker} if ticker in TICKER_DICT else {'label': ticker, 'value': ticker} for ticker in TICKERS],
                                value=TICKERS[0], clearable=False, persistence=True, persisted_props=['value'], persistence_type='local'
                                ),
                    html.Br(),
                    html.H4('Select TimeFrame:', style={'width': '100%'}),
                    dcc.Dropdown(id='timeframe_dropdown', 
                                options=[{'label': 'Daily', 'value': 'Daily'}, {'label': 'Hourly', 'value': 'Hourly'}],
                                value='Daily', clearable=False, persistence=True, persisted_props=['value'], 
                                persistence_type='local'
                                ),
                    html.Br(),            
                    
                    # Wrapped BUY and SELL sections in a Div with an id 'bot_info'
                    html.Div(id='bot_info', children=[
                        html.Br(),
                        html.H4('Start Bot Message:', style={'width': '100%', 'color': 'green'}),
                        dcc.Textarea(id='buy_textarea', value='', placeholder='Enter Message to Start Bot', style={'width': '100%', 'height': '150px', 'resize': 'none', 'textAlign': 'left', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column'}),
                        html.Br(),
                        html.H4('Stop Bot Message:', style={'width': '100%', 'color': 'red'}),
                        dcc.Textarea(id='sell_textarea', value='', placeholder='Enter Message to Stop Bot', style={'width': '100%', 'height': '150px', 'resize': 'none', 'textAlign': 'left', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column'}),
                        html.Br(),
                        html.Button(id='autotrade_button', className='btn btn-outline-dark', children='Autotrade', n_clicks=0, style={'width': '100%', 'height': '50px', 'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column'}),
                        html.Br(),
                        html.Div(id='autotrade_label', children=[

                        ], style={'display': 'block'}),  # Initially set to not display
                        html.Br(),
                    ], style={'display': 'none'})  # Initially set to not display


                ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row', 'width': '100%', 'padding': '10px 40px 10px 40px', 'display': 'inline-block'}),
                
                html.Div(children=[
                                dcc.Graph( id='ticker_chart', figure={}),
                                html.Div(id='div_table', children=[
                                ]),
                        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'width': '100%', 'marginBottom': '10px', 'padding' : '10px'}),
                
            ], style={'width': '100%', 'textAlign': 'center', 'display': 'flex', 'justifyContent': 'left', 'alignItems': 'left', 'flexDirection': 'row'}),
            
        ], type='circle', fullscreen=False), # Loading component ends here
        dcc.Interval(
            id='interval-component',
            interval=15*60*1000, # in milliseconds = will update every 15 minutes
            n_intervals=0
        ), 
        dcc.Store(id='autotrade_store', storage_type='local')
        
])

#################### CALLBACKS ####################
@callback(
    Output('ticker_chart', 'figure'), 
    Output('div_table', 'children'),
    Output('div_table', 'style'),
    Input('timeframe_dropdown', 'value'),
    Input('ticker_dropdown', 'value'),
    Input('buy_textarea', 'value'),
    Input('sell_textarea', 'value'),
    State('autotrade_store', 'data'),  # Access store_data as State
    Input('interval-component', 'n_intervals'),
    # do not run the callback if the ticker is not changed
    prevent_initial_call=False
    )
def update_chart(timeframe, ticker, buy_message, sell_message, store_data, n):
    show_hourly_chart = True if timeframe == 'Hourly' else False
    new_fig = process_chart_pipeline(ticker, show_hourly_chart=show_hourly_chart)
    # Use store_data to check autotrade status and ticker selection is Bitcoin
    if ticker == 'BTC-USDC' and store_data and store_data.get('autotrade_on'):
        # get the latest row where Close is not null
        latest_data = MERGED_DATA[ticker].iloc[-91]
        # Check conditions and print for now
        if latest_data['Close'] < latest_data['lower_band']:
            print(f"BTC-USDC Close price is below the lower band: {latest_data['Close']}")
            # Implement buy logic here
            bot_controller.start_bot(buy_message)
        elif latest_data['Close'] > latest_data['upper_band']:
            print(f"BTC-USDC Close price is above the upper band: {latest_data['Close']}")
            # Implement sell logic here
            bot_controller.stop_bot(sell_message)
    # show if ticker is not i crypto or mt4
    if ticker not in CRYPTO_TICKERS and ticker not in MT4_SYMBOLS:
        table = create_table(ticker)
        return new_fig, table, {'display': 'block'}
    else:
        return new_fig, '', {'display': 'none'}
    
# Callback to toggle visibility of the BUY and SELL sections
@callback(
    Output('bot_info', 'style'),
    Output('buy_textarea', 'value'),
    Output('sell_textarea', 'value'),
    Input('ticker_dropdown', 'value')
)
def toggle_bot_info_visibility(selected_ticker):
    # Check if the selected ticker is Bitcoin
    print('\nselected_ticker', selected_ticker)
    if selected_ticker == 'BTC-USDC':  # Replace with your Bitcoin ticker ID
        # check if the pickle file exists
        if os.path.exists('data/trade_messages.pickle'):
            # load the pickle file
            with open('data/trade_messages.pickle', 'rb') as file:
                trade_messages = pickle.load(file)
            # return the trade messages
            buy_message = trade_messages['buy_message']
            print('buy_message', buy_message)
            sell_message = trade_messages['sell_message']
            print('sell_message', sell_message)
        # If Bitcoin is selected, make the sections visible
        return {'display': 'block'}, buy_message, sell_message
    else:
        # If another ticker is selected, hide the sections
        return {'display': 'none'}, '', ''

# Callback to toggle the Autotrade label
@callback(
    Output('autotrade_label', 'children'),
    Output('autotrade_store', 'data'),  # Update the store with the current state
    Input('autotrade_button', 'n_clicks'),
    Input('buy_textarea', 'value'),
    Input('sell_textarea', 'value'),
    State('autotrade_store', 'data'),  # Use the store's data to determine the current state
    prevent_initial_call=True
)
def toggle_autotrade(n_clicks, buy_message, sell_message, store_data):
    # Initialize store_data if it's None
    if store_data is None:
        store_data = {'autotrade_on': False, 'buy_message': '', 'sell_message': ''}

    # Check if the number of clicks is even or odd
    if n_clicks % 2 == 0:
        # Even number of clicks, autotrade is off
        store_data['autotrade_on'] = False
        label = [html.P('Autotrade is Off', style={'color': 'red'})]
    else:
        # Odd number of clicks, autotrade is on
        store_data['autotrade_on'] = True
        label = [html.P('Autotrade is On', style={'color': 'green'})]
        
        # Update the buy and sell messages
        if buy_message and sell_message:
            store_data['buy_message'] = buy_message
            store_data['sell_message'] = sell_message
        
        # don't save the buy and sell messages if they are empty
        if buy_message == '' or sell_message == '':
            return label, store_data
        # create a dictionary to store the buy and sell messages
        trade_messages = {'buy_message': buy_message, 'sell_message': sell_message}
        # SAVE THE BUY AND SELL MESSAGES TO A PICKLE FILE
        with open('data/trade_messages.pickle', 'wb') as file:
            pickle.dump(trade_messages, file)
    return label, store_data

