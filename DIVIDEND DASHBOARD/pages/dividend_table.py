import dash
from dash import html, dcc, dash_table, Input, Output, callback
from datetime import date, datetime
import pandas as pd
import plotly.express as px

#################### FUNCTIONS ####################
def create_dividend_chart(data):
    # Create the line chart
    fig = px.line(data, x='pay_date', y='next_div_earned', color='Ticker', markers=True,
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
    # Format dates as 'year-month-day'
    dividend_info_df['ex_dividend_date'] = dividend_info_df['ex_dividend_date'].dt.strftime('%Y-%m-%d')
    dividend_info_df['pay_date'] = dividend_info_df['pay_date'].dt.strftime('%Y-%m-%d')
    return dividend_info_df

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
                            "format": MONEY_FORMAT if i in ['cash_amount', 'next_div_earned', 'est_yr_yield'] else None
                        } for i in upcoming_dividends_df.columns],
                    data=upcoming_dividends_df.to_dict('records'),
                    cell_selectable=False,
                    sort_action='native',
                    filter_action='native',
                    style_header={'textAlign': 'center', 'backgroundColor': '#1E1E1E', 'fontWeight': 'bold', 'color': 'white'},
                    style_filter={'backgroundColor': '#FFEB9C', 'fontWeight': 'bold', 'color': '#9C5700'},
                    style_cell_conditional=[
                        {
                            'if': { 'column_id': ['Ticker', 'frequency', 'Shares', 'next_div_earned', 'est_yr_yield'] },
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
    # Filter the dataframe based on the date range using query
    div_df = div_df.query('pay_date >= @start_date_str and pay_date <= @end_date_str')
    # create the chart
    fig = create_dividend_chart(div_df)
    return div_df.to_dict('records'), fig


