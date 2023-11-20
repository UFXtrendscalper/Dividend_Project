import dash
from dash import html, dcc, Input, Output, callback, dash_table
import plotly.express as px
import pandas as pd
import datetime as datetime
import numpy as np

#################### CONSTANTS ####################
MONEY_FORMAT = dash_table.FormatTemplate.money(2)
PERCENTAGE_FORMAT = dash_table.FormatTemplate.percentage(2)
# get the current date and time
CURRENT_TIME = datetime.datetime.now()
# reformat to not show microseconds
CURRENT_TIME = CURRENT_TIME.strftime("%Y-%m-%d %H:%M:%S")
# excel file path
EXCEL_FILE = 'data/Dividend_Dashboard.xlsx'

#################### FUNCTIONS ####################
def get_yr_div_profits(sheet_names):
    yr_div_profits = {}
    for sheet in sheet_names:
        data = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
        div_profits = round(data['Amount'].sum(), 2)
        yr_div_profits[sheet] = div_profits
    df = pd.DataFrame.from_dict(yr_div_profits, orient='index', columns=['Amount'])
    return df

def get_current_holdings():
    #  read in the current holdings sheet
    c_holdings_df = pd.read_excel(EXCEL_FILE, sheet_name='current_holdings')
    #  keep only the columns we need
    c_holdings_df = c_holdings_df[['Ticker', 'Date Op.', 'Shares', 'Close' , 'Pur. Price', 'Exit Price', 'Amt. Paid', 'Pos. Value', 'G/L ($)', 'G/L (%)', 'Div. Earned']]
    # rounding the values to 2 decimal places
    c_holdings_df = c_holdings_df.round(2)
    # convert the shares to int type
    c_holdings_df['Shares'] = c_holdings_df['Shares'].astype(int)
    # sort the values by the G/L ($)
    c_holdings_df = c_holdings_df.sort_values(by='G/L ($)', ascending=False)
    # convert the Date Op. column to string
    c_holdings_df['Date Op.'] = c_holdings_df['Date Op.'].dt.strftime('%m-%d-%Y')
    return c_holdings_df

# get the dividends paid by month
def sum_dividends_by_month():
    data = pd.read_excel(EXCEL_FILE, sheet_name='2023')
    data = data[['Month', 'Amount']]
    # Define the order for the months
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # Convert the 'Month' column to a categorical type with the specified order
    data['Month'] = pd.Categorical(data['Month'], categories=months_order, ordered=True)
    # group by month and sum the dividends paid
    data = data.groupby(['Month']).sum()
    return data

# create a line chart directly without a callback
def create_line_chart(data):
    # Calculate the average of the 'Amount'
    average_amount = data['Amount'].mean()
    # Create the line chart
    fig = px.line(data, x=data.index, y='Amount', title='Dividends Paid by Month')
    # Add markers and show the value of each point
    fig.update_traces(mode='markers+lines', hovertemplate=None)
    # Update layout
    fig.update_layout(hovermode='x unified', template='plotly_dark')
    fig.update_layout(hoverlabel=dict(font_size=16, font_family="Rockwell"))
    fig.update_layout(title_x=0.5, xaxis_title='', yaxis_title='')
    fig.update_layout(height=400, width=800)
    fig.update_layout(font_size=16, font_family="Rockwell")
    fig.update_layout(title_font_family="Rockwell", title_font_size=24)
    # Add the horizontal line
    fig.add_hline(y=average_amount, line_dash="dash", 
                  annotation_text=f"Average: ${average_amount:.2f}", 
                  annotation_position="top right")
    # Update y-axes to include dollar sign
    fig.update_yaxes(tickprefix="$")
    return fig

# create a bar chart directly without a callback
def create_bar_chart(df):
    # Create the bar chart
    fig = px.bar(df, x=df.index, y='Amount', title='Dividend Profits')
    # Update layout
    fig.update_layout(template = 'plotly_dark', title_x=0.5, xaxis_title='', yaxis_title='')
    fig.update_layout(height=400, width=800)
    fig.update_layout(font_size=16, font_family="Rockwell")
    fig.update_layout(title_font_family="Rockwell", title_font_size=24)
    # Update y-axes to include dollar sign
    fig.update_yaxes(tickprefix="$")
    return fig

def preprocess_data(df):
    """
    Preprocesses the closed trades dataframe by keeping specific columns,
    changing NaN values to 0 in the 'Div. Earned' column, and calculating
    the 'Amount' column.

    Parameters:
    df (DataFrame): The original dataframe of closed trades.

    Returns:
    DataFrame: The preprocessed dataframe.
    """
    # Keep specific columns
    dataframe = df.copy()[['Date Closed', 'G/L ($)', 'Div. Earned']]

    # Change NaN to 0 in the 'Div. Earned' column
    dataframe['Div. Earned'] = dataframe['Div. Earned'].fillna(0)

    # Calculate the 'Amount' column
    dataframe['Amount'] = dataframe['G/L ($)'] - dataframe['Div. Earned']

    # Drop the 'G/L ($)' and 'Div. Earned' columns and rename 'Date Closed'
    dataframe = dataframe[['Date Closed', 'Amount']].rename(columns={'Date Closed': 'Date'})

    return dataframe

def load_and_preprocess_data(filepath):
    """
    Reads data from an Excel file and preprocesses it for analysis.
    It reads data from different sheets and formats them.

    Parameters:
    filepath (str): Path to the Excel file containing the data.

    Returns:
    tuple: A tuple containing preprocessed dataframes.
    """
    # Read data from Excel file
    closed_trades_df = pd.read_excel(filepath, sheet_name='closed_trades')
    div_paid_2023_df = pd.read_excel(filepath, sheet_name='2023')
    div_paid_2022_df = pd.read_excel(filepath, sheet_name='2022')
    div_paid_2021_df = pd.read_excel(filepath, sheet_name='2021')

    # Preprocess closed trades data
    closed_trades_df = preprocess_data(closed_trades_df)

    # Keep only Date and Amount columns for dividend data
    div_paid_2023_df = div_paid_2023_df[['Date', 'Amount']]
    div_paid_2022_df = div_paid_2022_df[['Date', 'Amount']]
    div_paid_2021_df = div_paid_2021_df[['Date', 'Amount']]

    # Concatenate the dividend dataframes
    div_paid_df = pd.concat([div_paid_2023_df, div_paid_2022_df, div_paid_2021_df, closed_trades_df])

    return div_paid_df

def calculate_cumulative_growth(df):
    """
    Groups the dataframe by date, sums the amounts, and calculates the cumulative
    growth.

    Parameters:
    df (DataFrame): The dataframe with dividend payments and closed trades.

    Returns:
    DataFrame: The dataframe with an additional column for cumulative growth.
    """
    # Group by date and sum the amounts
    df = df.groupby('Date').sum()

    # Calculate cumulative sum of the values
    df['cumulative_growth'] = np.cumsum(df['Amount'])

    # Round the values in the dataframe
    df = df.round(2)

    return df

def plot_cumulative_growth(df):
    """
    Plots a line chart of cumulative growth over time.

    Parameters:
    df (DataFrame): The dataframe containing the date and cumulative growth.

    Returns:
    None: Displays the plot.
    """
    fig = px.line(df, x=df.index, y='cumulative_growth', 
                  title='Cumulative Growth:<br> Including Closed Trades and Dividends Paid',
                  template='plotly_dark')
    fig.update_layout(hoverlabel=dict(font_size=16, font_family="Rockwell"))
    fig.update_layout(title_x=0.5, xaxis_title='', yaxis_title='')
    fig.update_layout(height=400, width=800)
    fig.update_layout(font_size=16, font_family="Rockwell")
    fig.update_layout(title_font_family="Rockwell", title_font_size=24)
    fig.update_yaxes(tickprefix="$")
    return fig

def plot_yearly_dividends(df):
    """
    Plots a bar chart of yearly dividend payouts.

    Parameters:
    df (DataFrame): The dataframe containing the year and total dividends paid.

    Returns:
    None: Displays the plot.
    """
    fig = px.bar(df, y='Amount', title='Yearly Payouts:<br> Including Closed Trades and Dividends Paid',
                 template='plotly_dark')
    fig.update_layout(hoverlabel=dict(font_size=16, font_family="Rockwell"))
    fig.update_layout(title_x=0.5, xaxis_title='', yaxis_title='')
    fig.update_layout(height=400, width=800)
    fig.update_layout(font_size=16, font_family="Rockwell")
    fig.update_layout(title_font_family="Rockwell", title_font_size=24)
    fig.update_yaxes(tickprefix="$")
    fig.update_xaxes(tickmode='linear')
    return fig

dash.register_page(__name__, path='/', name='Home 🤑')

#################### LOAD DATA ####################
div_profits_df = get_yr_div_profits(['2021', '2022', '2023'])
cur_holdings_df = get_current_holdings()
cur_dividends_paid_df = sum_dividends_by_month()

filepath = './data/Dividend_Dashboard.xlsx'
div_paid_df = load_and_preprocess_data(filepath)
# Calculate cumulative growth
cumulative_growth_df = calculate_cumulative_growth(div_paid_df)

# Prepare and plot yearly dividends
div_paid_yearly_df = cumulative_growth_df.groupby(pd.Grouper(freq='Y')).sum()
div_paid_yearly_df.index = div_paid_yearly_df.index.year

#################### PAGE LAYOUT ####################
layout = html.Div(children=[
    html.Div(children=[
        html.Br(),
        html.Div(children=[
            dcc.Graph(figure=create_bar_chart(div_profits_df)),
            dcc.Graph(figure=create_line_chart(cur_dividends_paid_df))
        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row'}),
        html.Div(children=[
            dcc.Graph(figure = plot_cumulative_growth(cumulative_growth_df)),
            dcc.Graph(figure = plot_yearly_dividends(div_paid_yearly_df)),
        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row'}),
        html.Div(children=[
            html.Div([
                html.H4('Current Holdings', style={'paddingLeft': '25px'}),
                html.H6(f'(Last updated {CURRENT_TIME})', id='last_update', style={'paddingLeft': '10px', 'paddingTop': '15px'}),
            ], style={'font-family': 'Rockwell, serif', 'textAlign': 'left', 'display': 'flex', 'justifyContent': 'left', 'alignItems': 'left', 'flexDirection': 'row'}),
            dash_table.DataTable(
                id='curr_holdings_table',
                columns=[
                    {
                        "name": i, 
                        "id": i,
                        "type": "numeric",
                        "format": MONEY_FORMAT if i in ['Close', 'Pur. Price', 'Exit Price', 'Amt. Paid', 'Pos. Value', 'G/L ($)', 'Div. Earned'] else
                                  PERCENTAGE_FORMAT if i == 'G/L (%)' else None 
                     } for i in cur_holdings_df.columns],
                data=cur_holdings_df.to_dict('records'),
                cell_selectable=False,
                sort_action='native',
                filter_action='native',
                style_header={'textAlign': 'center', 'backgroundColor': '#1E1E1E', 'fontWeight': 'bold', 'color': 'white'},
                style_filter={'backgroundColor': '#FFEB9C', 'fontWeight': 'bold', 'color': '#9C5700'},
                style_cell_conditional=[
                    {
                        'if': { 'column_id': ['Ticker', 'Shares'] },
                        'textAlign': 'center'
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
                    # Odd rows with G/L ($) greater than 0
                    {
                        'if': {
                            'filter_query': '{G/L ($)} > 0',
                            'row_index': 'odd',
                        },
                        'backgroundColor': '#00B050',  # A darker green background for odd rows
                        'color': '#115910',
                        'fontWeight': 'bold'
                    },
                    # Even rows with G/L ($) greater than 0
                    {
                        'if': {
                            'filter_query': '{G/L ($)} > 0',
                            'row_index': 'even',
                        },
                        'backgroundColor': '#D9EAD3',  # A lighter green background for even rows
                        'color': '#115910',
                        'fontWeight': 'bold'
                    },
                ],
                style_as_list_view=False,
                style_table={'overflowX': 'scroll', 'width': '100%'}, 
            )
        ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'left', 'alignItems': 'left', 'flexDirection': 'column'}),
        dcc.Interval(
            id='interval-component',
            interval=30*60*1000, # in milliseconds = 5 minutes
            n_intervals=0
        )
    ])
])

#################### CALLBACKS ####################
@callback(
    Output('curr_holdings_table', 'data'),
    Output('last_update', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_curr_holdings_table(n):
    holdings_df = get_current_holdings()
    # update the timestamp
    cur_time = datetime.datetime.now()
    cur_time = cur_time.strftime("%Y-%m-%d %H:%M:%S")
    timestamp = f'(Last updated {cur_time})'
    return holdings_df.to_dict('records'), timestamp

