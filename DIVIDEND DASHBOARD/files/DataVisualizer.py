import plotly.graph_objects as go
from datetime import datetime

class DataVisualizer:
    @staticmethod
    def create_candlestick_chart(data, symbol, timeframe, width=1500, height=890):
        """
        Creates a candlestick chart with additional predicted price and trend lines.

        Returns:
            fig (go.Figure): A Plotly Figure object containing the candlestick chart.
        """
        # Initialize a new figure instead of adding to self.fig
        fig = go.Figure()
        # clear the figure
        fig.data = []
        # clear the layout
        fig.layout = {}
        # clear the frames
        fig.frames = []
        
        # Define traces
        candlestick_trace = go.Candlestick(
            x=data.index, 
            open=data.Open, 
            high=data.High, 
            low=data.Low, 
            close=data.Close, 
            name='Candlestick', 
            increasing_line_color='#F6FEFF', 
            decreasing_line_color='#1CBDFB'
        )

        predicted_price_trace = go.Scatter(
            x=data.index, 
            y=data.predicted_price, 
            line=dict(color='#B111D6', width=1), 
            name='Predicted Price'
        )

        trend_trace = go.Scatter(
            x=data.index, 
            y=data.trend, 
            line=dict(color='#0074BA', width=1), 
            name='Predicted Trend'
        )

        upper_band_trace = go.Scatter(
            x=data.index, 
            y=data.upper_band, 
            line=dict(color='#1E82CD', width=2), 
            name='upper_band'
        )

        lower_band_trace = go.Scatter(
            x=data.index, 
            y=data.lower_band, 
            line=dict(color='#1E82CD', width=2), 
            name='lower_band'
        )

        # Add all traces to the figure
        fig.add_traces([candlestick_trace, predicted_price_trace, trend_trace, upper_band_trace, lower_band_trace])

        # Get timestamp for annotation
        timestamp = datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")

        # Update layout
        fig.update_layout(
            title={'text': f'{symbol} {timeframe} Chart', 'x': 0.5, 'y': 0.95},
            yaxis=dict(title='', gridcolor='#444654', tickprefix="$"),
            xaxis=dict(gridcolor='#444654'),
            annotations=[{"text": f"This graph was last generated on {timestamp}", 
                          "showarrow": False, "x": 0.55, "y": 1.05, "xref": "paper", "yref": "paper"}],
            width=width, height=height, xaxis_rangeslider_visible=False, 
            paper_bgcolor='#202123', plot_bgcolor='#202123', 
            font=dict(color='white', size=12),
            font_size=14, font_family="Rockwell", title_font_family="Rockwell", title_font_size=24
        )

        return fig
