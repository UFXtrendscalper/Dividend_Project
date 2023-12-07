import plotly.graph_objects as go
from datetime import datetime

class DataVisualizer:
    def __init__(self, data, symbol=None, timeframe=None, width=1500, height=890):
        self.data = data
        self.symbol = symbol
        self.timeframe = timeframe
        self.width = width
        self.height = height
        

    def create_candlestick_chart(self):
        """
        Creates a candlestick chart with additional predicted price and trend lines.

        Returns:
            fig (go.Figure): A Plotly Figure object containing the candlestick chart.
        """
        # Initialize a new figure instead of adding to self.fig
        fig = go.Figure()

        # Define traces
        candlestick_trace = go.Candlestick(
            x=self.data.index, 
            open=self.data.Open, 
            high=self.data.High, 
            low=self.data.Low, 
            close=self.data.Close, 
            name='Candlestick', 
            increasing_line_color='#F6FEFF', 
            decreasing_line_color='#1CBDFB'
        )

        predicted_price_trace = go.Scatter(
            x=self.data.index, 
            y=self.data.predicted_price, 
            line=dict(color='#B111D6', width=1), 
            name='Predicted Price'
        )

        trend_trace = go.Scatter(
            x=self.data.index, 
            y=self.data.trend, 
            line=dict(color='#0074BA', width=1), 
            name='Predicted Trend'
        )

        upper_band_trace = go.Scatter(
            x=self.data.index, 
            y=self.data.upper_band, 
            line=dict(color='#1E82CD', width=2), 
            name='upper_band'
        )

        lower_band_trace = go.Scatter(
            x=self.data.index, 
            y=self.data.lower_band, 
            line=dict(color='#1E82CD', width=2), 
            name='lower_band'
        )

        # Add all traces to the figure
        fig.add_traces([candlestick_trace, predicted_price_trace, trend_trace, upper_band_trace, lower_band_trace])

        # Get timestamp for annotation
        timestamp = datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")

        # Update layout
        fig.update_layout(
            title={'text': f'{self.symbol} {self.timeframe} Chart', 'x': 0.5, 'y': 0.95},
            yaxis=dict(title='', gridcolor='#444654', tickprefix="$"),
            xaxis=dict(gridcolor='#444654'),
            annotations=[{"text": f"This graph was last generated on {timestamp}", 
                          "showarrow": False, "x": 0.55, "y": 1.05, "xref": "paper", "yref": "paper"}],
            width=self.width, height=self.height, xaxis_rangeslider_visible=False, 
            paper_bgcolor='#202123', plot_bgcolor='#202123', 
            font=dict(color='white', size=12),
            font_size=14, font_family="Rockwell", title_font_family="Rockwell", title_font_size=24
        )

        return fig
