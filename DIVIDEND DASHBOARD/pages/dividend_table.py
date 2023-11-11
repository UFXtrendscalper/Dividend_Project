import dash
from dash import html, dcc, dash_table, Input, Output, callback
from datetime import date, datetime
import pandas as pd
import plotly.express as px

#################### FUNCTIONS ####################
def create_dividend_chart(data):
    # Create the line chart
    fig = px.line(data, x='pay_date', y='next_payout', color='ticker', markers=True,
                title='Dividend Payout Over Time')
    # Update layout
    fig.update_layout(title_x=0.5, template = 'plotly_dark', xaxis_title='', yaxis_title='Payout', legend_title="Ticker")
    fig.update_layout(hoverlabel=dict(font_size=18, font_family="Rockwell", bgcolor='black', font_color='white'))
    fig.update_layout(height=400, width=1500)
    fig.update_layout(font_size=16, font_family="Rockwell")
    fig.update_layout(title_font_family="Rockwell", title_font_size=24)
    # rotate the dates on the x-axis
    fig.update_xaxes(tickangle= -45)
    # Update y-axes to include dollar sign
    fig.update_yaxes(tickprefix="$")
    return fig

def set_decimal_places(df, column_name, decimal_places):
    """
    Set the decimal places for a column in a dataframe.

    Parameters
    ----------
    df : pandas dataframe
        The dataframe to be modified.
    column_name : str
        The name of the column to be modified.
    decimal_places : int
        The number of decimal places to be set.

    Returns
    -------
    df : pandas dataframe
        The modified dataframe.
    """
    df[column_name] = df[column_name].round(decimal_places)
    return df

def calculate_upcoming_dividends():
    #  read in the dividend_info sheet
    dividend_info_df = pd.read_excel('./data/Dividend_Dashboard.xlsx', sheet_name='dividend_info')
    #  read in the current holdings sheet
    holdings_df = pd.read_excel('./data/Dividend_Dashboard.xlsx', sheet_name='current_holdings')
    #  keep only the columns we need
    holdings_df = holdings_df[['Ticker', 'Shares']]
    # sort the dividend_info_df by ticker
    dividend_info_df = dividend_info_df.sort_values(by=['ticker'])
    # create a list of tickers from dividend_info_df
    dividend_info_list = dividend_info_df['ticker'].values.tolist()
    # query the holdings_df for tickers in the dividend_info_list
    holdings_df = holdings_df[holdings_df['Ticker'].isin(dividend_info_list)]
    # sort the holdings_df by ticker
    holdings_df = holdings_df.sort_values(by=['Ticker'])
    # merge the two dataframes
    merged_df = pd.merge(dividend_info_df, holdings_df, left_on='ticker', right_on='Ticker')
    # drop the Ticker column
    merged_df = merged_df.drop(columns=['Ticker'])
    # round the cash_amount column to 2 decimal places
    merged_df = set_decimal_places(merged_df, 'cash_amount', 2)
    # calculate the next payout amount
    merged_df['next_payout'] = merged_df['cash_amount'] * merged_df['Shares']
    # round the next_payout column to 2 decimal places
    merged_df = set_decimal_places(merged_df, 'next_payout', 2)
    # create a new column for expected yearly payout
    merged_df['est_yr_payout'] = merged_df['next_payout'] * merged_df['frequency']
    # round the expected_yearly_payout column to 2 decimal places
    merged_df = set_decimal_places(merged_df, 'est_yr_payout', 2)
    # convert the pay_date column to datetime
    merged_df['pay_date'] = pd.to_datetime(merged_df['pay_date'])
    # get todays date as a datetime object
    today = pd.to_datetime(date.today())
    # format the date to match the pay_date column
    today = today.strftime("%Y-%m-%d")
    # exclude the tickers that have already paid out
    merged_df = merged_df[merged_df['pay_date'] > today]
    # sort the merged_df by pay date
    merged_df = merged_df.sort_values(by=['pay_date'])
    # convert the pay_date column back to string
    merged_df['pay_date'] = merged_df['pay_date'].dt.strftime('%Y-%m-%d')
    # convert ex_dividend_date column to string
    merged_df['ex_dividend_date'] = merged_df['ex_dividend_date'].dt.strftime('%Y-%m-%d')
    return merged_df

#################### LOAD DATA ####################
upcoming_dividends_df = calculate_upcoming_dividends()

#################### CONSTANTS ####################
MONEY_FORMAT = dash_table.FormatTemplate.money(2)
START_DATE = date.today()
# set the end date to the end of the month
END_DATE = upcoming_dividends_df['pay_date'].max()

dash.register_page(__name__, path='/dividend_table', name='Dividend Table')

#################### PAGE LAYOUT ####################
layout = html.Div(children=[
    html.Div([
        dcc.Graph(id='dividend_chart', figure=create_dividend_chart(upcoming_dividends_df), style={'margin': 'auto'}),
    ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row'}),
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.H4('Upcoming Dividend Payouts', style={'textAlign': 'left', 'margin': 10, 'paddingTop': 15}),
                html.Div(children=[
                    html.H4('Filter by Date: ', style={'textAlign': 'left', 'margin': 10, 'paddingTop': 15}),
                    dcc.DatePickerRange(id='date_range', start_date=START_DATE, end_date=END_DATE, display_format='YYYY-MM-DD', persistence=True, persisted_props=['start_date', 'end_date'], persistence_type='session',
                                    style={'margin': 10}),
                ], style={'display': 'flex'}),
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'width': '100%'}),
            dash_table.DataTable(
                id='dividend_table',
                    columns=[
                        {
                            "name": i, 
                            "id": i,
                            "type": "numeric",
                            "format": MONEY_FORMAT if i in ['cash_amount', 'next_payout', 'est_yr_payout'] else None
                        } for i in upcoming_dividends_df.columns],
                    data=upcoming_dividends_df.to_dict('records'),
                    cell_selectable=False,
                    sort_action='native',
                    filter_action='native',
                    style_header={'textAlign': 'center', 'backgroundColor': '#1E1E1E', 'fontWeight': 'bold', 'color': 'white'},
                    style_filter={'backgroundColor': '#FFEB9C', 'fontWeight': 'bold', 'color': '#9C5700'},
                    style_cell_conditional=[
                        {
                            'if': { 'column_id': ['ticker', 'frequency', 'Shares', 'next_payout', 'est_yr_payout'] },
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
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'flexDirection': 'column', 'width': '100%'}),
    ], style={'display': 'flex', 'justifyContent': 'flex-start', 'width': '60%', 'margin': 'auto'}),
])

#################### CALLBACKS ####################
@callback(
    Output('dividend_table', 'data'),
    Output('dividend_chart', 'figure'),
    Input('date_range', 'start_date'),
    Input('date_range', 'end_date')
)
def update_dividend_table(start_date_str, end_date_str):
    # Call the function to get fresh data from the Excel file
    upcoming_dividends_df = calculate_upcoming_dividends()

    div_df = upcoming_dividends_df.copy()
    # Convert string dates to datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    # convert the pay_date column to datetime
    div_df['pay_date'] = pd.to_datetime(div_df['pay_date'])
    # filter the dataframe based on the date range
    div_df = div_df[(div_df['pay_date'] >= start_date) & (div_df['pay_date'] <= end_date)]
    # convert the pay_date column back to string
    div_df['pay_date'] = div_df['pay_date'].dt.strftime('%Y-%m-%d')
    # create the chart
    fig = create_dividend_chart(div_df)
    return div_df.to_dict('records'), fig


