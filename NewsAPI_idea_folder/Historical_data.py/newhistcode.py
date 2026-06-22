import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# SETTINGS

START_DATE = "2022-01-01"
END_DATE = "2023-12-31"

TICKERS = [
    "AAPL","MSFT","AMZN","GOOGL","META",
    "NVDA","TSLA","BRK-B","JPM","JNJ",
    "V","PG","XOM","UNH","HD",
    "MA","PFE","BAC","CVX","WMT",
    "ABT","KO","PEP","NFLX","DIS",
    "AGX","PLAB","BKE","KLIC","VRA",
    "NHTC","ELA","WHG","ULBI","MLAB",
    "PRQR","OHI","HALL","LWAY","IDT",
    "GBLI","AE","PFIN","MLR","CODA",
    "BRT","WSTL","LIQT","BRMK","DRCT"
]

# DOWNLOAD DATA

all_data = []

for ticker in TICKERS:

    try:
        print(f"Downloading {ticker}...")

        df = yf.download(
            ticker,
            start=START_DATE,
            end=END_DATE,
            progress=False,
            auto_adjust=False
        )

        if len(df) == 0:
            print(f"No data found for {ticker}")
            continue

        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Daily return
        df["Return"] = df["Close"].pct_change()

        # Absolute return
        df["abs_Return"] = df["Return"].abs()

        # 30-day rolling volatility
        df["Volatility"] = (
            df["Return"]
            .rolling(window=30)
            .std()
        )

        # Log volume
        df["log_Volume"] = np.log(df["Volume"])

        # Company information
        stock = yf.Ticker(ticker)

        try:
            market_cap = stock.info.get("marketCap", np.nan)
        except:
            market_cap = np.nan

        df["MarketCap"] = market_cap

        # Add ticker
        df["Stock"] = ticker

        # Convert index to column
        df = df.reset_index()

        all_data.append(df)

        print(f"Success: {ticker}")

    except Exception as e:
        print(f"Error with {ticker}: {e}")

# COMBINE INTO PANEL DATASET

panel_data = pd.concat(all_data, ignore_index=True)


# KEEP ONLY VARIABLES NEEDED

panel_data = panel_data[
    [
        "Date",
        "Stock",
        "Close",
        "Volume",
        "log_Volume",
        "Return",
        "abs_Return",
        "Volatility",
        "MarketCap"
    ]
]


# CLEAN DATA

panel_data = panel_data.dropna()

# SAVE FILES

panel_data.to_csv(
    "panel_stock_data.csv",
    index=False
)

panel_data.to_excel(
    "panel_stock_data.xlsx",
    index=False
)

print("\n====================================")
print("DOWNLOAD COMPLETE")
print("====================================")
print(f"Observations: {len(panel_data):,}")
print(f"Companies: {panel_data['Stock'].nunique()}")
print("Saved:")
print("- panel_stock_data.csv")
print("- panel_stock_data.xlsx")
