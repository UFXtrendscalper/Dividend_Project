import dash
from dash import html, dcc, Input, Output, callback, dash_table 
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import requests
from prophet import Prophet
from datetime import date, timedelta, datetime
import os
from dotenv import load_dotenv

load_dotenv('.env')

#################### FUNCTIONS ####################
def create_indices_charts(): 
    # end def    # Download the data from yahoo finance
    tickers = ['^VIX', '^GSPC', 'CL=F', 'GC=F']
    
    data = yf.download(tickers, period='1y', interval='1d', group_by='ticker', rounding=True)

    ticker_names = []
    for i, ticker in enumerate(tickers):
        names = ['VIX Volatility Index: $', 'S&P 500 Index: $', 'Crude Oil: $', 'Gold: $']
        ticker_names.append(names[i]+str(data[ticker].Close[-1]))

    # Calculate the average close price for each index
    avg_prices = {ticker: data[ticker]['Close'].mean() for ticker in tickers}

    # Create subplots
    fig = make_subplots(rows=1, cols=4, subplot_titles=ticker_names)

    # Add traces for each index
    for i, ticker in enumerate(tickers, start=1):
        fig.add_trace(
            go.Scatter(x=data[ticker].index, y=data[ticker]['Close'], name=ticker_names[i-1]),
            row=1, col=i
        )
        # Add average line
        fig.add_hline(
            y=avg_prices[ticker], 
            line_dash="dash", 
            annotation_text=f"Avg: ${avg_prices[ticker]:.2f}",
            annotation_position="bottom right",
            annotation_bgcolor="grey",
            row=1, col=i
        )

    # Update layout
    fig.update_layout(
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
    fig.update_layout(hoverlabel=dict(font_size=12, font_family="Rockwell", bgcolor='black', font_color='white'))

    # Update xaxes and yaxes
    for i in range(1, 5):
        fig.update_xaxes(title='', showgrid=True, showticklabels=True, row=1, col=i)
        fig.update_yaxes(title='', showgrid=False, showticklabels=False, row=1, col=i)

    # Show figure
    return fig

def load_and_combine_tickers(CRYPTO_TICKERS, MT4_TICKERS, ETF_TICKERS):
    # get the Ticker column from the dividend excel file
    dividend_tickers = pd.read_excel('data/Dividend_Dashboard.xlsx', sheet_name='current_holdings', usecols='G') 
    # convert divedend tickers to a list
    dividend_tickers = dividend_tickers['Ticker'].tolist()
    # sort the list
    dividend_tickers.sort()
    tickers = ETF_TICKERS + CRYPTO_TICKERS + MT4_TICKERS + dividend_tickers
    return tickers

# get data from mt4 csv files
def get_mt4_data(symbol, period='60'):
    # read in a csv file
    path = r'C:\\Users\sean7\AppData\\Roaming\\MetaQuotes\\Terminal\\0BB29DBF61C9F39836A4ED9CF1A954C9\\MQL4\\Files\\'
    period = period # 1440 = 1 day, 60 = 1 hour
    filename = f'{symbol}_{period}.csv'
    # create column names
    col_names = ['Date', 'Open', 'High', 'Low', 'Close']
    _df = pd.read_csv(path+filename, index_col=0, parse_dates=True, delimiter=';', names=col_names)
    return _df

# get the data from yahoo finance
def get_yahoo_data(symbol):
    # todo: add a doc string
    # get data from yahoo finance to use
    ticker = yf.Ticker(symbol)
    symbol_data = ticker.history(period='2y', interval='1d')[['Open', 'High', 'Low', 'Close']]
    symbol_data.index = symbol_data.index.tz_localize(None)
    return symbol_data

def get_crypto_data(symbol, period='1day'):
    # note VIP0 is 2000 requests per 30 seconds
    # Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
    # get todays date with year month and day only
    end = datetime.now().strftime("%Y %m %d")
    # start 2 years ago
    start = (datetime.now() - timedelta(days=730)).strftime("%Y %m %d")
    # convert end to timestamp
    end = datetime.strptime(end, "%Y %m %d").timestamp()
    # convert start to timestamp
    start = datetime.strptime(start, "%Y %m %d").timestamp()
    # API endpoint
    url = f'https://api.kucoin.com/api/v1/market/candles?type={period}&symbol={symbol}&startAt={int(start)}&endAt={int(end)}'
    
    # Making a GET request
    response = requests.get(url)

    # Checking if the request was successful
    if response.status_code == 200:
        # Parsing response data
        data = response.json()
        print("Crypto Data received by Kucoin:", data.keys())
        # create a dataframe from the json data
        df = pd.DataFrame(data['data'])
        # rename the columns
        df.columns = ['Date', 'Open', 'Close', 'High', 'Low',  'Volume', 'Turnover']
        # convert date column to an integar
        df['Date'] = df['Date'].astype(int)
        # convert the timestamp to datetime
        df['Date'] = pd.to_datetime(df['Date'], unit='s')
        # set the index to be the date column
        df.set_index('Date', inplace=True)
        # set the columns to be floats
        df = df.astype(float) 
        # sort the dataframe by date
        df = df.sort_index(ascending=True)
        # keep only the columns in this order Open High Low Close
        df = df[['Open', 'High', 'Low', 'Close']]
        # return the dataframe
        return df
    else:
        print("Failed to retrieve Kucoin data. Status code:", response.status_code)

# splice the data when povided a date best to do a forecast on 2 years of data
def splice_data(df, date, query=False, query_on=''):
    # todo: add a doc string
    if query:
        return df.query(f'{query_on} >= "{date}"')
    return df.loc[date:]    

def forcasting_preparation(df):
    # todo: add a doc string
    df = df.reset_index()
    return df[['Date', 'Close']]
        
# use prophet to forecast the data
def forecast_data(data, freq='D'):
    # todo: add a doc string
    '''Notes for freq Parameter::
    Can use 'D' for days and 'H' for hours and 'W' for weeks 
    When using 'W' for weeks, the generated future data points will always fall on the start of the week, regardless of the start date in the history.
    The 'W' frequency will default to generating dates that fall on a Sunday. However, you can specify a different day of the week by using 'W-MON', 'W-TUE', 'W-WED', etc., to have the weeks start on Monday, Tuesday, Wednesday, and so on. This allows for more flexibility in aligning the generated future data points with the specific weekly cycle of your dataset.'''
    data = data.rename(columns={'Date': 'ds', 'Close': 'y'})
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=90, freq=freq)
    forecast = model.predict(future)
    return forecast

def process_forecasted_data(forecast_df):
    # todo: add a doc string
    df = forecast_df.copy()
    # smooth out the prediction lines
    df['predicted_price'] = df['yhat'].rolling(window=7).mean()
    df['upper_band'] = df['yhat_upper'].rolling(window=7).mean()
    df['lower_band'] = df['yhat_lower'].rolling(window=7).mean()
    # keep only needed columns in the forecast dataframe
    df = df[['ds', 'predicted_price', 'lower_band', 'upper_band', 'trend']] 
    # rename the ds column to Date
    df = df.rename(columns={'ds': 'Date'})
    # set the Date column as the index
    df = df.set_index('Date') 
    return df

def merge_dataframes(original_data, forecast_data):
    # merge the forecast dataframe with the original dataframe on the Date index
    merged_df = pd.merge(original_data, forecast_data, on='Date', how='outer')
    return merged_df 

def plotly_visualize_forecast(symbol, timeframe, merged_data, width=1500, height=890):
    # todo: add a doc string

    # check if symbol is in the ticker dictionary
    if symbol in TICKER_DICT:
        symbol = TICKER_DICT[symbol]
    #  get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")

    # create the date buttons
    if timeframe == 'Daily':
        date_buttons = [{'count': 15, 'label': '1Y', 'step': "month", 'stepmode': "todate"},
                        {'count': 9, 'label': '6M', 'step': "month", 'stepmode': "todate"},
                        {'count': 6, 'label': '3M', 'step': "month", 'stepmode': "todate"},
                        {'count': 4, 'label': '1M', 'step': "month", 'stepmode': "todate"}, 
                        {'step': "all"}]
    # create the plotly chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=merged_data.index, open=merged_data.Open, high=merged_data.High, low=merged_data.Low, close=merged_data.Close, name='Candlestick', increasing_line_color='#F6FEFF', decreasing_line_color='#1CBDFB'))
    
    if timeframe == 'Daily':
        # update the layout of the chart with the buttons
        fig.update_layout(  
            {'xaxis':
                {'rangeselector': {'buttons': date_buttons, 
                                    'bgcolor': '#444654', 
                                    'activecolor': '#1E82CD',
                                    'bordercolor': '#444654',
                                    'font': {'color': 'white'}}
                }
            },
        )

    fig.update_layout(
        width=width, height=height, xaxis_rangeslider_visible=False, 
        paper_bgcolor='#202123', plot_bgcolor='#202123', font=dict(color='white', size=12),
        font_size=14, font_family="Rockwell", title_font_family="Rockwell", title_font_size=24
    )
    
    #  update the layout of the chart with the title and axis labels
    fig.update_layout( 
        {'annotations': [{  "text": f"This graph was last generated on {timestamp}", 
                            "showarrow": False, "x": 0.55, "y": 1.05, "xref": "paper", "yref": "paper"}]},
    )

    fig.update_layout( 
        {'title': {'text':f'{symbol} {timeframe} Chart', 'x': 0.5, 'y': 0.95}},
        yaxis=dict(title='', gridcolor='#444654'), xaxis=dict(gridcolor='#444654')
    )
    # Update y-axes to include dollar sign
    fig.update_yaxes(tickprefix="$")
    
    # add the predicted price and trend lines to the chart
    fig.add_trace(go.Scatter(x=merged_data.index, y=merged_data.predicted_price, line=dict(color='#B111D6', width=1), name='Predicted Price'))
    fig.add_trace(go.Scatter(x=merged_data.index, y=merged_data.trend, line=dict(color='#0074BA', width=1), name='Predicted Trend'))
    fig.add_trace(go.Scatter(x=merged_data.index, y=merged_data.upper_band, line=dict(color='#1E82CD', width=2), name='upper_band'))
    fig.add_trace(go.Scatter(x=merged_data.index, y=merged_data.lower_band, line=dict(color='#1E82CD', width=2), name='lower_band'))
    return fig

def process_chart_pipeline(symbol, show_hourly_chart=False):
    # todo add an if statement for forex pairs to use alphavantage api  
    print('processing chart pipeline', symbol)
    if symbol in CRYPTO_TICKERS:
        if show_hourly_chart:
            print('processing hourly crypto', symbol)
            get_crypto_data(symbol, period='1hour')    
            fig = go.Figure()
            return fig
        else:
            print('processing daily crypto', symbol)
            crypto_df = get_crypto_data(symbol)    
            # work through the process
            forecasting_prep = forcasting_preparation(crypto_df)
            forecasted_data = forecast_data(forecasting_prep)
            processed_forecast = process_forecasted_data(forecasted_data)
            merged_data = merge_dataframes(crypto_df, processed_forecast)
            # use plotly_visualize_forecast to plot the data
            fig = plotly_visualize_forecast(symbol, "Daily", merged_data)
            return fig    
    if symbol in MT4_SYMBOLS:
        print('\nprocessing mt4', symbol)
        daily_dataframes = {}
        daily_dataframes[symbol] = {
            'symbol_name': symbol,
            'timeframe': 'Daily',
            'freq': 'D',
            'df': get_mt4_data(symbol, period='1440')
        }
        timeframe = daily_dataframes[symbol]['timeframe']
        freq = daily_dataframes[symbol]['freq']
        original_data = daily_dataframes[symbol]['df'].copy()

        # work through the process
        forecasting_prep = forcasting_preparation(original_data)
        forecasted_data = forecast_data(forecasting_prep, freq=freq)
        processed_forecast = process_forecasted_data(forecasted_data)
        merged_data = merge_dataframes(original_data, processed_forecast)
        # use plotly_visualize_forecast to plot the data
        fig = plotly_visualize_forecast(symbol, timeframe, merged_data)
        return fig
    else:
        data = get_yahoo_data(symbol)
        forcasting_prep = forcasting_preparation(data)
        forecast = forecast_data(forcasting_prep)
        processed_forecast = process_forecasted_data(forecast)
        merged_data = merge_dataframes(data, processed_forecast)
        # visulize the data 
        fig = plotly_visualize_forecast(symbol, 'Daily', merged_data)
        return fig

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
MT4_SYMBOLS = ["USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "GBPUSD", "EURUSD", "OILUSe", "XAUUSD", "S&P500e", "BTCUSD", "ETHUSD"] 
ETF_SYMBOLS = ['SPLG', 'GLD']
TICKERS = load_and_combine_tickers(CRYPTO_TICKERS, MT4_SYMBOLS, ETF_SYMBOLS)
TICKER_DICT = {'USDCAD':'USD/CAD', 'USDJPY':'USD/JPY', 'USDCHF':'USD/CHF', 'EURUSD':'EUR/USD', 'GBPUSD':'GBP/USD', 'AUDUSD':'AUD/USD', 'NZDUSD':'NZD/USD', 'OILUSe':'Crude Oil', 'XAUUSD':'Gold Futures', 'GLD':'Gold ETF', 'S&P500e':'S&P 500 Futures', 'SPLG':'S&P 500 ETF', 'BTC-USDC':'Bitcoin', 'ETH-USDC':'Ethereum'}
TODAYS_DATE = date.today()
POLYGON_API_KEY = os.environ.get('POLYGON_IO_API')
ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_CO_API')
MONEY_FORMAT = dash_table.FormatTemplate.money(2)


dash.register_page(__name__, path='/market_watch', name='Market Watch 📈')

#################### PAGE LAYOUT ####################
layout = html.Div(children=[
        html.Br(),
        html.Div(children=[
            dcc.Graph(figure=create_indices_charts()),
        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'width': '100%'}),
        html.Hr(style={'color': 'white'}),
        html.Div([


            html.Div([
                html.H4('Select TimeFrame:', style={'width': '100%'}),
                dcc.Dropdown(id='timeframe_dropdown', 
                            options=[{'label': 'Daily', 'value': 'Daily'}, {'label': 'Hourly', 'value': 'Hourly'}],
                            value='Daily', 
                            clearable=False
                            ),
                html.H4('Select Ticker:', style={'width': '100%'}),
                dcc.Dropdown(id='ticker_dropdown', 
                            options=[{'label': TICKER_DICT[ticker], 'value': ticker} if ticker in TICKER_DICT else {'label': ticker, 'value': ticker} for ticker in TICKERS],
                            value=TICKERS[0], 
                            clearable=False
                            )
            ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row', 'width': '100%', 'padding': '10px 40px 10px 40px', 'display': 'inline-block'}),
            html.Div(children=[
                dcc.Graph( id='ticker_chart', figure=process_chart_pipeline(TICKERS[0])),
                html.Div(id='div_table', children=[
                
                ]),
            ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'width': '100%', 'marginBottom': '10px', 'padding' : '10px'}),
        

        ], style={'width': '100%', 'textAlign': 'center', 'display': 'flex', 'justifyContent': 'left', 'alignItems': 'left', 'flexDirection': 'row'}),
        
        dcc.Interval(
            id='interval-component',
            interval=15*60*1000, # in milliseconds = will update every 15 minutes
            n_intervals=0
        )
        
])

#################### CALLBACKS ####################
@callback(
    Output('ticker_chart', 'figure'), 
    Output('div_table', 'children'),
    Input('timeframe_dropdown', 'value'),
    Input('ticker_dropdown', 'value'),
    Input('interval-component', 'n_intervals'),
    # do not run the callback if the ticker is not changed
    prevent_initial_call=True
    )
def update_chart(timeframe, ticker, n):
    if timeframe == 'Hourly':
        fig = process_chart_pipeline(ticker, show_hourly_chart=True)
    else:
        fig = process_chart_pipeline(ticker)
    table = create_table(ticker)
    return fig, table

