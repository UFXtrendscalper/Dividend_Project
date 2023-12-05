import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# set the css style sheet to cyborg from https://bootswatch.com/cyborg/
external_css = [dbc.themes.CYBORG]

# create a dash app and set the pages_folder to 'pages' and use_pages to True
app = dash.Dash(__name__, pages_folder='pages', use_pages=True , external_stylesheets=external_css, suppress_callback_exceptions=True)

# create the layout for the app
app.layout = html.Div([
    # html.Br(),
    html.Div([
        html.H1('DIVIDEND DASHBOARD', style={'textAlign': 'center', 'color': 'white', 'margin': 20, 'padding': 0, 'font-family': 'Rockwell, serif'}),
        html.Img(src=app.get_asset_url('images/dividend_logo.png'), style={'width':'7%'}),
    ], style={'textAlign': 'center', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'row'}
    ),
    html.Div(children=[
                    dcc.Link(page['name'], href=page['relative_path'], className='btn btn-outline-dark') for page in dash.page_registry.values()
                    ], style={'display': 'flex', 'margin': 'auto', 'width': '45%', 'justifyContent': 'space-between'}
            ),
    dash.page_container
])

if __name__ == '__main__':
    app.run_server(debug=True)  

