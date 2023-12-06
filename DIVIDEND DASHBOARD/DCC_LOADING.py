import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import time

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div([
    dcc.Input(id='input-box', value='Type something', type='text'),
    html.Button('Submit', id='button'),
    dcc.Loading(
        id="loading-1",
        type="circle", # This can be "graph", "cube", "circle", "dot", or "default"
        children=html.Div(id="loading-output-1")
    )
])

# Define callback to update loading output
@app.callback(
    Output('loading-output-1', 'children'),
    [Input('button', 'n_clicks')],
    [dash.dependencies.State('input-box', 'value')]
)
def update_output(n_clicks, value):
    if n_clicks is None:
        return 'Click the button to see something!'
    else:
        time.sleep(3) # Simulate a delay
        return f'You have entered: {value}'

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=3000)
