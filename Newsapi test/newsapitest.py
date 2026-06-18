import pandas as pd
import requests
import time
from datetime import datetime, timedelta

# =====================================================
# BATCH 1
# =====================================================

COMPANIES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "META": "Meta",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "BRK-B": "Berkshire Hathaway",
    "JPM": "JPMorgan",
    "JNJ": "Johnson & Johnson"
}

# =====================================================
# LAST 1 YEAR
# =====================================================

END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365)

all_results = []

current_start = START_DATE

while current_start < END_DATE:

    current_end = current_start + timedelta(days=7)

    start_str = current_start.strftime("%Y%m%d%H%M%S")
    end_str = current_end.strftime("%Y%m%d%H%M%S")

    print(f"\nWeek: {current_start.date()}")

    for ticker, company in COMPANIES.items():

        try:

            print(f"Collecting {ticker}")

            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
            )

            params = {
                "query": f'"{company}"',
                "mode": "artlist",
                "format": "json",
                "startdatetime": start_str,
                "enddatetime": end_str,
                "maxrecords": 250
            }

            r = requests.get(
                url,
                params=params,
                timeout=60
            )

            if r.status_code != 200:

                print(f"HTTP {r.status_code}")
                continue

            data = r.json()

            articles = data.get("articles", [])

            article_count = len(articles)

            all_results.append({
                "Stock": ticker,
                "Company": company,
                "WeekStart": current_start.date(),
                "NewsCount": article_count
            })

            print(
                f"{ticker}: {article_count} articles"
            )

            time.sleep(2)

        except Exception as e:

            print(e)

    current_start = current_end

# =====================================================
# SAVE
# =====================================================

news_df = pd.DataFrame(all_results)

news_df.to_csv(
    "gdelt_batch1_weekly_news.csv",
    index=False
)

news_df.to_excel(
    "gdelt_batch1_weekly_news.xlsx",
    index=False
)

print("\nDone")
print(news_df.head())
print(news_df.shape)