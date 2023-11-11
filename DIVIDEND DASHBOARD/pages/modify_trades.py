import dash
from dash import html, dcc

dash.register_page(__name__, path='/modify_trades', name='Add/Remove Trades 💲')

layout = html.Div(children=[
    html.Div(children=[
        html.Br(),
        html.H3('Add a Symbol', style={'textAlign': 'center', 'margin': 10, 'padding': 0}),
        #  add an input box for the symbol, shares, purchase price, exit price and a submit button
        html.Div(children=[
            html.Div(children=[
                dcc.Input(id='symbol_input', placeholder='Enter a symbol', type='text', value='', style={'width': '50%', 'margin': 'auto', 'display': 'inline-block'}),
                dcc.Input(id='shares_input', placeholder='Enter shares', type='number', value='', style={'width': '50%', 'margin': 'auto', 'display': 'inline-block'}),
            ], style={'marginBottom': '20px'}),
            html.Div(children=[
                dcc.Input(id='purchase_price_input', placeholder='Enter purchase price', type='number', value='', style={'width': '50%', 'margin': 'auto', 'display': 'inline-block'}),
                dcc.Input(id='exit_price_input', placeholder='Enter exit price', type='number', value='', style={'width': '50%', 'margin': 'auto', 'display': 'inline-block'}),
            ], style={'marginBottom': '20px'}),
            html.Button('Submit', id='submit_button', n_clicks=0, style={'width': '20%', 'margin': 'auto', 'display': 'inline-block'}),
        ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'flexDirection': 'column'}),
        html.P('Note:: will try and use this when everything is migrated to SQL', style={'textAlign': 'center', 'margin': 10, 'padding': 0}),
        
    ])
])

