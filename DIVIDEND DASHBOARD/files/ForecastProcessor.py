from prophet import Prophet

class ForecastProcessor:
    @staticmethod
    def prophet_forecast(data, period=90, freq='D'):
        """
        Generates a forecast using the Prophet model from the provided time series data.

        Args:
            data (DataFrame): A Pandas DataFrame with two columns: 'ds' and 'y'.
                              'ds' is the datetime column and 'y' is the metric to forecast.
            period (int): The number of periods to forecast forward.
            freq (str): The frequency of the forecast ('D' for days, 'H' for hours, 'W' for weeks).
                        - 'D' generates daily data points.
                        - 'H' generates hourly data points.
                        - 'W' generates weekly data points, defaulting to Sunday as the week start.
                          Use 'W-MON', 'W-TUE', 'W-WED', etc., for weeks starting on other days.
                          This flexibility aligns future data points with specific weekly cycles.

        Returns:
            DataFrame: A Pandas DataFrame containing the forecast. Includes the forecasted
                       values along with components like trend and uncertainty intervals.
        """
        model = Prophet()
        model.fit(data)
        future = model.make_future_dataframe(periods=period, freq=freq)
        forecast = model.predict(future)
        return forecast
