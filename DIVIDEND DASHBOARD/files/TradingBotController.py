import requests
import json

class TradingBotController:
    def start_bot(self, trade_message):
        print("\nStarting the buy bot...\n")
        # Convert string dict to dict
        trade_dict = eval(trade_message)
        trade_dict = json.dumps(trade_dict, indent=4)
        # Define the API endpoint
        api_url = "https://3commas.io/trade_signal/trading_view"
        # Your data payload this is for stopping the bot
        payload = trade_dict
        # Send POST request
        response = requests.post(api_url, json=payload)
        # Check response
        if response.status_code == 200:
            print("Bot started successfully.")
        else:
            print("Failed to stop the bot. Status code:", response.status_code)

    def stop_bot(self, trade_message):
        print("\nStopping the buy bot...\n")
        # Convert string dict to dict
        trade_dict = eval(trade_message)
        trade_dict = json.dumps(trade_dict, indent=4)
        # Define the API endpoint
        api_url = "https://3commas.io/trade_signal/trading_view"
        # Your data payload this is for stopping the bot
        payload = trade_dict
        # Send POST request
        response = requests.post(api_url, json=payload)
        # Check response
        if response.status_code == 200:
            print("Bot stopped successfully.")
        else:
            print("Failed to stop the bot. Status code:", response.status_code)
