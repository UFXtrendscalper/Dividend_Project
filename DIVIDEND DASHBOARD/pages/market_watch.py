import dash
import os
import pickle
import requests
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, State, callback, dash_table 
from plotly.subplots import make_subplots
from datetime import date, datetime
from dotenv import load_dotenv
from files.TradingBotController import TradingBotController
from files.StockDataFetcher import StockDataFetcher
from files.CryptoDataFetcher import CryptoDataFetcher
from files.MT4DataFetcher import MT4DataFetcher
from files.ForecastProcessor import ForecastProcessor
from files.DataProcessor import DataProcessor

load_dotenv('.env')

#################### Object Instantiation ####################
bot_controller = TradingBotController()
stock_data_fetcher = StockDataFetcher()
crypto_data_fetcher = CryptoDataFetcher()
mt4_data_fetcher = MT4DataFetcher()

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

# splice the data when povided a date best to do a forecast on 2 years of data
def splice_data(df, date, query=False, query_on=''):
    # todo: add a doc string
    if query:
        return df.query(f'{query_on} >= "{date}"')
    return df.loc[date:]    

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
    fig.data = []
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
    print('\n\nprocessing chart pipeline', symbol)
    if symbol not in CRYPTO_TICKERS and symbol not in MT4_SYMBOLS:
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
        # visulize the data 
        fig = plotly_visualize_forecast(symbol, 'Daily', MERGED_DATA[symbol])
        return fig
    elif symbol in CRYPTO_TICKERS:
        # set the symbol
        crypto_data_fetcher.set_symbol(symbol)
        if show_hourly_chart:
            print('\nprocessing hourly crypto', symbol)
            # fetch the data
            crypto_df = crypto_data_fetcher.fetch_data(period='1hour')
            # prepare the data for prophet
            prep_data = DataProcessor.prepare_data_for_prophet(crypto_df)
            # forecast the data 
            forecast = ForecastProcessor.prophet_forecast(prep_data, freq='H')
            # process the forecasted data 
            processed_forecast = DataProcessor.process_prophet_forecast(forecast)
            # merge the dataframes
            MERGED_DATA[symbol] = DataProcessor.merge_dataframes_for_prophet(crypto_df, processed_forecast) 
            # slice the data to only show the last 291 rows
            crypto_slice_df = MERGED_DATA[symbol].iloc[-291:]
            # use plotly_visualize_forecast to plot the data
            fig = plotly_visualize_forecast(symbol, "1hour", crypto_slice_df)
            return fig
        else:
            print('\nprocessing daily crypto', symbol)
            # fetch the data
            crypto_df = crypto_data_fetcher.fetch_data(period='1day')
            # prepare the data for prophet
            prep_data = DataProcessor.prepare_data_for_prophet(crypto_df)
            # forecast the data 
            forecast = ForecastProcessor.prophet_forecast(prep_data)
            # process the forecasted data 
            processed_forecast = DataProcessor.process_prophet_forecast(forecast)
            # merge the dataframes
            MERGED_DATA[symbol] = DataProcessor.merge_dataframes_for_prophet(crypto_df, processed_forecast)
            # use plotly_visualize_forecast to plot the data
            fig = plotly_visualize_forecast(symbol, "Daily", MERGED_DATA[symbol])
            return fig   
    elif symbol in MT4_SYMBOLS:
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
        # use plotly_visualize_forecast to plot the data
        fig = plotly_visualize_forecast(symbol, timeframe, MERGED_DATA[symbol])
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
MT4_SYMBOLS = ["USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "GBPUSD", "EURUSD", "OILUSe", "XAUUSD", "S&P500e"] 
ETF_SYMBOLS = ['SPLG', 'GLD']
TICKERS = load_and_combine_tickers(CRYPTO_TICKERS, MT4_SYMBOLS, ETF_SYMBOLS)
TICKER_DICT = {'USDCAD':'USD/CAD', 'USDJPY':'USD/JPY', 'USDCHF':'USD/CHF', 'EURUSD':'EUR/USD', 'GBPUSD':'GBP/USD', 'AUDUSD':'AUD/USD', 'NZDUSD':'NZD/USD', 'OILUSe':'Crude Oil', 'XAUUSD':'Gold Futures', 'GLD':'Gold ETF', 'S&P500e':'S&P 500 Futures', 'SPLG':'S&P 500 ETF', 'BTC-USDC':'Bitcoin', 'ETH-USDC':'Ethereum'}
TODAYS_DATE = date.today()
POLYGON_API_KEY = os.environ.get('POLYGON_IO_API')
ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_CO_API')
MONEY_FORMAT = dash_table.FormatTemplate.money(2)
MERGED_DATA = {}


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
                            value='Daily', clearable=False, persistence=True, persisted_props=['value'], 
                            persistence_type='local'
                            ),
                html.Br(),            
                html.H4('Select Ticker:', style={'width': '100%'}),
                dcc.Dropdown(id='ticker_dropdown', 
                            options=[{'label': TICKER_DICT[ticker], 'value': ticker} if ticker in TICKER_DICT else {'label': ticker, 'value': ticker} for ticker in TICKERS],
                            value=TICKERS[0], clearable=False, persistence=True, persisted_props=['value'], persistence_type='local'
                            ),
                
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
                    html.Div(id='autotrade_label', children=[html.P('Autotrade is Off', style={'width': '100%', 'color': 'red'})], style={'display': 'block'}),  # Initially set to not display
                    html.Br(),
                ], style={'display': 'none'})  # Initially set to not display


            ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row', 'width': '100%', 'padding': '10px 40px 10px 40px', 'display': 'inline-block'}),
            
            html.Div(children=[
                dcc.Graph( id='ticker_chart', figure={}),
                html.Div(id='div_table', children=[
                
                ]),
            ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'width': '100%', 'marginBottom': '10px', 'padding' : '10px'}),
        

        ], style={'width': '100%', 'textAlign': 'center', 'display': 'flex', 'justifyContent': 'left', 'alignItems': 'left', 'flexDirection': 'row'}),
        
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
    Input('timeframe_dropdown', 'value'),
    Input('ticker_dropdown', 'value'),
    Input('interval-component', 'n_intervals'),
    Input('buy_textarea', 'value'),
    Input('sell_textarea', 'value'),
    State('autotrade_store', 'data'),  # Access store_data as State
    # do not run the callback if the ticker is not changed
    prevent_initial_call=False
    )
def update_chart(timeframe, ticker, n, buy_message, sell_message, store_data):
    if timeframe == 'Hourly':
        fig = process_chart_pipeline(ticker, show_hourly_chart=True)
    else:
        fig = process_chart_pipeline(ticker)
    table = create_table(ticker)
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
    
    return fig, table

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