//+------------------------------------------------------------------+
//|                                          UFX_FXRateCollector.mq4 |
//|                                                                  |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright ""
#property link      ""
#property version   "1.00"

static int curBarsOnChart, dailyBarsOnChart;
// Define the array
string symbols[] = {"USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "GBPUSD", "EURUSD", "OILUSe", "XAUUSD", "S&P500e", "BTCUSD", "ETHUSD"};

//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
// run a check that the chart is on the 1 hour timeframe
   if(Period() != PERIOD_M15)
     {
      bool success = ChartSetSymbolPeriod(0, Symbol(), PERIOD_M15);
      // Check if the chart change was unsuccessful
      if(!success)
        {
         // Alert the user
         Alert("Failed to change the chart");
         Alert("Please Change to 1 Hour TimeFrame");
         // Return failure to initialize
         return(INIT_FAILED);
        }
     }
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {


  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   if(IsNewCandle(PERIOD_CURRENT, curBarsOnChart))
     {
      //will run every new candle on current chart
      //get the hourly data and save to csv file
      Print("collecting data every 15mins");
      getHourlyData();
      getDailyData();
     }

   if(IsNewCandle(PERIOD_D1, dailyBarsOnChart))
     {
      //will run every new daily candle
      Print("New Daily Candle Formed"); //printing for future use of new candle function
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool IsNewCandle(int timeframe, int tBarsOnChart)
  {

   if(iBars(Symbol(), timeframe) == tBarsOnChart)
     {
      return(false);
     }
   else
     {
      if(timeframe == PERIOD_CURRENT)
         curBarsOnChart = iBars(Symbol(), timeframe);
      if(timeframe == PERIOD_D1)
         dailyBarsOnChart= iBars(Symbol(), timeframe);
      return(true);
     }
  }
//+------------------------------------------------------------------+
// Function to save candle data to a CSV file
//+------------------------------------------------------------------+
void SaveCandleDataToCSV(string fileName, MqlRates &rates[], int ratesSize)
  {
// Open a CSV file
   int fileHandle = FileOpen(fileName, FILE_WRITE | FILE_CSV);

// Check if the file is opened successfully
   if(fileHandle == INVALID_HANDLE)
     {
      Print("Error opening file: ", GetLastError());
      return;
     }

// Write data to the file
   for(int i = 0; i < ratesSize; i++)
     {
      FileWrite(fileHandle,
                TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES),
                rates[i].open,
                rates[i].high,
                rates[i].low,
                rates[i].close);
     }

// Close the file
   FileClose(fileHandle);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void getHourlyData()
  {
// Iterate through all symbols
   for(int i = 0; i < ArraySize(symbols); i++)
     {
      // Define the array for MqlRates
      MqlRates rates[];
      // Copy rates into the array
      //Note:: symbol can be any symbol ex EURUSD & Period can be any ex PERIOD_H1
      int candles_back = 730;
      int copied = CopyRates(symbols[i], PERIOD_H1, 0, candles_back, rates);

      // Check if rates are copied successfully
      if(copied <= 0)
        {
         Print("Error copying rates: ", GetLastError(), " for ", symbols[i]);
        }

      // Call the function to save data to CSV
      string filename = symbols[i]+"_"+string(PERIOD_H1)+".csv";
      SaveCandleDataToCSV(filename, rates, ArraySize(rates));
     }//end of for loop

   Print("Finished Processing 1 Hour Data");
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void getDailyData()
  {
// Iterate through all symbols
   for(int i = 0; i < ArraySize(symbols); i++)
     {
      // Define the array for MqlRates
      MqlRates rates[];
      // Copy rates into the array
      //Note:: symbol can be any symbol ex EURUSD & Period can be any ex PERIOD_H1
      int candles_back = 730;
      int copied = CopyRates(symbols[i], PERIOD_D1, 0, candles_back, rates);

      // Check if rates are copied successfully
      if(copied <= 0)
        {
         Print("Error copying rates: ", GetLastError(), " for ", symbols[i]);
        }

      // Call the function to save data to CSV
      string filename = symbols[i]+"_"+string(PERIOD_D1)+".csv";
      SaveCandleDataToCSV(filename, rates, ArraySize(rates));
     }//end of for loop

   Print("Finished Processing Daily Data");

  }
//+------------------------------------------------------------------+
