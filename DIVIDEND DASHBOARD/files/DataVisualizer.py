import plotly.graph_objects as go
from datetime import datetime

class DataVisualizer:
    def __init__(self, data, symbol, timeframe, width=1500, height=890):
        self.data = data
        self.symbol = symbol
        self.timeframe = timeframe
        self.width = width
        self.height = height

    def create_candlestick_chart(self):
        # todo: add a doc string
        #  get timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")

        # # create the date buttons
        # if timeframe == 'Daily':
        #     date_buttons = [{'count': 15, 'label': '1Y', 'step': "month", 'stepmode': "todate"},
        #                     {'count': 9, 'label': '6M', 'step': "month", 'stepmode': "todate"},
        #                     {'count': 6, 'label': '3M', 'step': "month", 'stepmode': "todate"},
        #                     {'count': 4, 'label': '1M', 'step': "month", 'stepmode': "todate"}, 
        #                     {'step': "all"}]
        
        # create the plotly chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=self.data.index, open=self.data.Open, high=self.data.High, low=self.data.Low, close=self.data.Close, name='Candlestick', increasing_line_color='#F6FEFF', decreasing_line_color='#1CBDFB'))
        
        # if timeframe == 'Daily':
        #     # update the layout of the chart with the buttons
        #     fig.update_layout(  
        #         {'xaxis':
        #             {'rangeselector': {'buttons': date_buttons, 
        #                                 'bgcolor': '#444654', 
        #                                 'activecolor': '#1E82CD',
        #                                 'bordercolor': '#444654',
        #                                 'font': {'color': 'white'}}
        #             }
        #         },
        #     )

        fig.update_layout(
            width=self.width, height=self.height, xaxis_rangeslider_visible=False, 
            paper_bgcolor='#202123', plot_bgcolor='#202123', font=dict(color='white', size=12),
            font_size=14, font_family="Rockwell", title_font_family="Rockwell", title_font_size=24
        )
        
        #  update the layout of the chart with the title and axis labels
        fig.update_layout( 
            {'annotations': [{  "text": f"This graph was last generated on {timestamp}", 
                                "showarrow": False, "x": 0.55, "y": 1.05, "xref": "paper", "yref": "paper"}]},
        )

        fig.update_layout( 
            {'title': {'text':f'{self.symbol} {self.timeframe} Chart', 'x': 0.5, 'y': 0.95}},
            yaxis=dict(title='', gridcolor='#444654'), xaxis=dict(gridcolor='#444654')
        )
        # Update y-axes to include dollar sign
        fig.update_yaxes(tickprefix="$")
        
        # add the predicted price and trend lines to the chart
        fig.add_trace(go.Scatter(x=self.data.index, y=self.data.predicted_price, line=dict(color='#B111D6', width=1), name='Predicted Price'))
        fig.add_trace(go.Scatter(x=self.data.index, y=self.data.trend, line=dict(color='#0074BA', width=1), name='Predicted Trend'))
        fig.add_trace(go.Scatter(x=self.data.index, y=self.data.upper_band, line=dict(color='#1E82CD', width=2), name='upper_band'))
        fig.add_trace(go.Scatter(x=self.data.index, y=self.data.lower_band, line=dict(color='#1E82CD', width=2), name='lower_band'))
        return fig
