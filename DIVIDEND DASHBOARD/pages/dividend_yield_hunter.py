import dash
from dash import html, dcc, Input, Output, callback, dash_table, no_update, State
from dash import callback_context
import pandas as pd
from datetime import date, timedelta, datetime
from files.StockDataFetcher import StockDataFetcher
import requests
import yfinance as yf
from prophet import Prophet
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from scipy.signal import savgol_filter

load_dotenv('.env')

############### Object Instantiation ###############
stock_data_fetcher = StockDataFetcher()

#################### FUNCTIONS ####################
def fetch_and_filter_dividends(selected_date, api):
    # Calculate the date one day after today
    fetch_date = selected_date
    #  format the date to match "Year-mmonth-day"
    fetch_date = fetch_date.strftime('%Y-%m-%d')

    url = f'https://api.polygon.io/v3/reference/dividends?ex_dividend_date={fetch_date}&dividend_type=CD&order=asc&limit=1000&sort=ex_dividend_date&apiKey={api}'

    # make a request to the url 
    response = requests.get(url)
    # convert the response to json
    data = response.json()

    # check if data is empty
    if data['results']:
        # create a dataframe from the json data
        df = pd.DataFrame(data['results'])
        # create a list from the dataframe ticker column
        ticker_list = df['ticker'].tolist()
    else:
        ticker_list = None
        df3 = pd.DataFrame()
        return ticker_list, df3
    
    # get close prices for the tickers
    ticker_prices = yf.download(ticker_list, period='1d', interval='1d', prepost=True, rounding=True)['Close']
    # grap only the last row of the dataframe if there are multiple rows
    ticker_prices = ticker_prices.tail(1)
    # transpose the dataframe
    ticker_prices = ticker_prices.T
    # rename the column to close price
    ticker_prices.columns = ['close_price']
    df2 = df.copy()
    df2['close_Prices'] = df['ticker'].map(ticker_prices['close_price']) 
    df3 = df2.copy()
    # calculate the percentage of the dividend
    df3['percentage'] = (df2['cash_amount'] / df2['close_Prices'])*100
    #  calculate the yearly percentage based on frequency
    df3['yearly_percentage'] = (df3['percentage'] * df3['frequency'])
    # drop rows with missing values
    df3 = df3.dropna()
    # sort the dataframe by yearly_percentage
    df3 = df3.sort_values(by=['yearly_percentage'], ascending=False)
    # query the dataframe for yearly_percentage greater than 5
    df3 = df3.query('yearly_percentage > 5')
    df3[['cash_amount','ex_dividend_date','frequency','pay_date','ticker','close_Prices','percentage','yearly_percentage']]
    # create a list of the tickers
    ticker_list = df3['ticker'].tolist()
    return ticker_list, df3


def forcasting_preparation(df):
    # todo: add a doc string
    df = df.reset_index()
    return df[['Date', 'Close']]
        
# use prophet to forecast the data
def forecast_data(data):
    # todo: add a doc string
    data = data.rename(columns={'Date': 'ds', 'Close': 'y'})
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=90, freq='D')
    forecast = model.predict(future)
    return forecast

def process_forecasted_data(forecast_df):
    df = forecast_df.copy()
    # keep only needed columns in the forecast dataframe
    df = df[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']]  
    # use savgol_filter
    df['predicted_price'] = savgol_filter(df['yhat'], window_length=31, polyorder=2) 
    df['upper_band'] = savgol_filter(df['yhat_upper'], window_length=31, polyorder=2)
    df['lower_band'] = savgol_filter(df['yhat_lower'], window_length=31, polyorder=2)
    return df 

#################### CONSTANTS ####################
TODAYS_DATE = date.today()
MONEY_FORMAT = dash_table.FormatTemplate.money(2)
DECIMAL_FORMAT = dash_table.FormatTemplate.Format(precision=2, symbol_suffix='%')
POLYGON_API = os.environ.get('POLYGON_IO_API')

dash.register_page(__name__, path='/dividend_yield_hunter', name='Dividend Yield Hunter 🏹')

#################### PAGE LAYOUT ####################
layout = html.Div(children=[
    html.Div(children=[
        html.Br(),
        html.H4(f'Dividend Yield Hunter {TODAYS_DATE}', style={'textAlign': 'center', 'margin': 10, 'padding': 0}),
        html.Div(children=[
            dcc.DatePickerSingle(id='user_date', date=TODAYS_DATE, display_format='YYYY-MM-DD'),
        ], style={'margin': 30}),
        html.Div(children=[
            html.Button('Find Dividends', id='find-button', className='btn btn-outline-dark', n_clicks=0, style={'margin': 10}),
            html.Button('Clear Charts', id='clear-button', className='btn btn-outline-danger', n_clicks=0, style={'margin': 10}),
        ], style={'display': 'flex', 'justifyContent': 'left', 'alignItems': 'left', 'flexDirection': 'row', 'margin': 20})
    ]),
    dcc.Loading(
        id="loading",
        type="graph", # This can be "graph", "cube", "circle", "dot", or "default"
        children=html.Div(id='container', children=[], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'margin': 20})
    ),
])

@callback(
    [Output('container', 'children'), Output('find-button', 'n_clicks')],
    [Input('clear-button', 'n_clicks'), Input('find-button', 'n_clicks'), Input('user_date', 'date')],
    prevent_initial_call=True
)
def update_output(clear_clicks, find_clicks, date):
    # Determine which input was triggered
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update  # In case the callback was triggered without any of the specified inputs being clicked

    # Get the ID of the button that triggered the callback
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # If the clear button was clicked, clear the charts and reset find button clicks
    if button_id == 'clear-button':
        return [], 0

    # If the find button was clicked, generate the graphs
    elif button_id == 'find-button':
        # If the find button has not been clicked, do not update the graphs
        if find_clicks <= 0:
            return no_update, no_update

        # convert the date to a datetime object and format it
        date = datetime.strptime(date, '%Y-%m-%d').date()
        ticker_list, dataframe = fetch_and_filter_dividends(date, POLYGON_API)

        # If there are no dividends tomorrow, do not update the graphs
        if ticker_list:
            buy_list = []

            for symbol in ticker_list:
                # set the symbol
                stock_data_fetcher.set_ticker(symbol)
                # fetch the data
                data = stock_data_fetcher.fetch_data()
                forcasting_prep = forcasting_preparation(data)
                forecast = forecast_data(forcasting_prep)
                processed_forecast = process_forecasted_data(forecast)
                # check if price is less then the lower band
                date = data.index[-1].strftime('%Y-%m-%d')
                price = data.Close[-1]
                lower_band = processed_forecast.query(f'ds == "{date}"')['lower_band'].values[0]
                # # check if the price is below the lower band
                if price < lower_band:
                    # visualize the data
                    # plotly_visualize_forecast(symbol, data, processed_forecast)
                    # append symbol to the short list
                    buy_list.append([symbol, data, processed_forecast])

            # if there are no stocks to buy return a message
            if not buy_list:
                components_to_return = html.H3('There are no dividends opportunities', style={'textAlign': 'center', 'margin': 10, 'padding': 0, 'color': 'white'}), find_clicks
                return components_to_return, find_clicks
            
            buy_df = dataframe[['cash_amount','ex_dividend_date','frequency','pay_date','ticker','close_Prices','percentage','yearly_percentage']]
            # extract the symbols from the buy_list
            symbols = [sub_list[0] for sub_list in buy_list]
            # filter the buy_df for the symbols in the buy_list
            buy_df = buy_df[buy_df['ticker'].isin(symbols)]
            # create a column that contains the number of shares to buy based on 100$ investment
            buy_df['num_shares_100'] = 100 / buy_df['close_Prices']
            # convert to integer
            buy_df['num_shares_100'] = buy_df['num_shares_100'].astype(int)
            buy_df['purchase_cost'] = buy_df['num_shares_100'] * buy_df['close_Prices']
            buy_df['next_div_pay'] = buy_df['num_shares_100'] * buy_df['cash_amount']
            buy_df['yr_div_pay'] = buy_df['next_div_pay'] * buy_df['frequency']    

            # Generate graphs for each item in the list
            graphs = [create_chart(symbol) for symbol in buy_list]
            # generate the yield table 
            yield_table = create_table(buy_df)
            
            # Now append the yield_table_component to your graphs list or any other container list
            # that you are using to return the layout components
            components_to_return = graphs + [yield_table]
        else:
            components_to_return = html.H3('There are no dividends opportunities', style={'textAlign': 'center', 'margin': 10, 'padding': 0, 'color': 'white'})
        # Make sure to return the correct number of outputs
        return components_to_return, find_clicks
    
    # If the callback was not triggered by one of the buttons we're interested in
    return no_update, no_update


def create_chart(symbol):
    # Placeholder for creating a chart component based on the symbol
    # You would replace this with your actual chart creation code that uses the symbol
    # unpack the symbol list
    symbol, data, processed_forecast = symbol
    # create the chart
    fig = plotly_visualize_forecast(symbol, data, processed_forecast)

    return dcc.Graph(
        id=f'graph-{symbol}',
        figure=fig
    )

#  using plotly to plot the data. Create a candlstick chart with the 50 moving average
def plotly_visualize_forecast(symbol, data, forcast_processed, width=1200, height=600):
    #  get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")
    date_buttons = [{'count': 9, 'label': '6M', 'step': "month", 'stepmode': "todate"},
                    {'count': 6, 'label': '3M', 'step': "month", 'stepmode': "todate"},
                    {'count': 4, 'label': '1M', 'step': "month", 'stepmode': "todate"}]
    # create the plotly chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index, open=data.Open, high=data.High, low=data.Low, close=data.Close, name='Candlestick', increasing_line_color='#F6FEFF', decreasing_line_color='#1CBDFB'))
    
    # update the layout of the chart with the buttons and timestamp along with some kwargs
    fig.update_layout(  
        {'xaxis':
            {'rangeselector': {'buttons': date_buttons, 
                                'bgcolor': '#444654', 
                                'activecolor': '#1E82CD',
                                'bordercolor': '#444654',
                                'font': {'color': 'white'}}
            }
        },
            width=width, height=height, xaxis_rangeslider_visible=False, 
            paper_bgcolor='#202123', plot_bgcolor='#202123', font=dict(color='white', size=12),
            font_size=14, font_family="Rockwell", title_font_family="Rockwell", title_font_size=24
    )
    
    #  update the layout of the chart with the title and axis labels
    fig.update_layout( 
        {'annotations': [{  "text": f"This graph was last generated on {timestamp}", 
                            "showarrow": False, "x": 0.8, "y": 1.05, "xref": "paper", "yref": "paper"}]},
    )

    fig.update_layout( 
        {'title': {'text':f'{symbol} Price Chart', 'x': 0.5, 'y': 0.95}},
        yaxis=dict(title='Price', gridcolor='#444654'), xaxis=dict(gridcolor='#444654')
    )
    # Update y-axes to include dollar sign
    fig.update_yaxes(tickprefix="$")
    
    # add the predicted price and trend lines to the chart
    fig.add_trace(go.Scatter(x=forcast_processed.ds, y=forcast_processed.predicted_price, line=dict(color='#B111D6', width=1), name='Predicted Price'))
    fig.add_trace(go.Scatter(x=forcast_processed.ds, y=forcast_processed.trend, line=dict(color='#0074BA', width=1), name='Predicted Trend'))
    fig.add_trace(go.Scatter(x=forcast_processed.ds, y=forcast_processed.upper_band, line=dict(color='#1E82CD', width=2), name='upper_band'))
    fig.add_trace(go.Scatter(x=forcast_processed.ds, y=forcast_processed.lower_band, line=dict(color='#1E82CD', width=2), name='lower_band'))
    return fig

def create_table(df):
    return dash_table.DataTable(
        id='yield_table',
                    columns=[
                        {
                            "name": i, 
                            "id": i,
                            "type": "numeric",
                            "format": MONEY_FORMAT if i in ['cash_amount', 'close_Prices', 'purchase_cost', 'next_div_pay', 'yr_div_pay'] 
                            else DECIMAL_FORMAT if i in ['percentage', 'yearly_percentage']
                            else None
                        } for i in df.columns],
                    data=df.to_dict('records'),
                    cell_selectable=False,
                    sort_action='native',
                    filter_action='native',
                    style_header={'textAlign': 'center', 'backgroundColor': '#1E1E1E', 'fontWeight': 'bold', 'color': 'white'},
                    style_filter={'backgroundColor': '#FFEB9C', 'fontWeight': 'bold', 'color': '#9C5700'},
                    style_cell_conditional=[
                        {
                            'if': { 'column_id': ['ticker', 'frequency', 'num_shares_100'] },
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
                    style_table={'overflowX': 'scroll', 'width': '100%'}
    )
            
