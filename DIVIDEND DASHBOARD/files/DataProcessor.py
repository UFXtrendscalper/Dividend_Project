import pandas as pd

class DataProcessor:
    @staticmethod
    def prepare_data_for_prophet(data):
        """
        Prepares the input data for use with the Prophet forecasting model.

        This method takes a DataFrame with a Date column and a target column (e.g., Close price), 
        resets its index, and renames the columns to be compatible with Prophet ('ds' for date, 
        and 'y' for the target variable).

        Parameters:
        data (DataFrame): The input DataFrame with at least two columns: 'Date' and a target 
                          variable (e.g., 'Close').

        Returns:
        DataFrame: A processed DataFrame with columns renamed for Prophet model compatibility.
        """
        data = data.reset_index()
        data = data[['Date', 'Close']]
        data = data.rename(columns={'Date': 'ds', 'Close': 'y'})
        return data

    @staticmethod
    def process_prophet_forecast(forecast_df):
        """
        Processes the forecast DataFrame obtained from the Prophet model.

        This method takes the forecast DataFrame, smoothens the prediction lines using a rolling mean,
        and keeps only relevant columns for further analysis.

        Parameters:
        forecast_df (DataFrame): The forecast DataFrame obtained from the Prophet model.

        Returns:
        DataFrame: A DataFrame with smoothed predicted prices, upper and lower confidence bands, 
                   and the trend, indexed by date.
        """
        df = forecast_df.copy()
        # smooth out the prediction lines
        df['predicted_price'] = df['yhat'].rolling(window=7).mean()
        df['upper_band'] = df['yhat_upper'].rolling(window=7).mean()
        df['lower_band'] = df['yhat_lower'].rolling(window=7).mean()
        # keep only needed columns in the forecast dataframe
        df = df[['ds', 'predicted_price', 'lower_band', 'upper_band', 'trend']] 
        # rename the ds column to Date
        df = df.rename(columns={'ds': 'Date'})
        # set the Date column as the index
        df = df.set_index('Date') 
        return df

    @staticmethod
    def merge_dataframes_for_prophet(original_data, forecast_data):
        """
        Merges the original data DataFrame with the processed forecast DataFrame.

        This method performs an outer join on the 'Date' column, allowing for the combination of 
        the original data with the forecast data, facilitating comparison and analysis.

        Parameters:
        original_data (DataFrame): The original data DataFrame.
        forecast_data (DataFrame): The processed forecast DataFrame from the Prophet model.

        Returns:
        DataFrame: A merged DataFrame containing both the original and forecast data.
        """
        merged_df = pd.merge(original_data, forecast_data, on='Date', how='outer')
        return merged_df 


    # Future methods for other ML techniques can be added similarly
    # For example:
    @staticmethod
    def prepare_data_for_other_ml_technique(data):
        # Implementation for another ML technique
        pass
