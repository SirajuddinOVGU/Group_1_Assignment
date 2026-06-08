from newsapi import NewsApiClient
import pandas as pd
import time

# NewsAPI key
api = NewsApiClient(api_key="aaee18fbaac94d8e8948136bfd5e687e")

# Companies
companies = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "TSLA": "Tesla"
}

# Months from Jan 2022 to Dec 2023
months = pd.date_range(
    start="2022-01-01",
    end="2023-12-01",
    freq="MS"
)

results = []

for ticker, company in companies.items():

    print(f"\nProcessing {company}")

    for month_start in months:

        month_end = month_start + pd.offsets.MonthEnd(1)

        response = api.get_everything(
            q=company,
            from_param=month_start.strftime("%Y-%m-%d"),
            to=month_end.strftime("%Y-%m-%d"),
            language="en",
            page_size=1  # only need totalResults
        )

        results.append({
            "ticker": ticker,
            "company": company,
            "month": month_start.strftime("%Y-%m"),
            "article_count": response["totalResults"]
        })

        print(
            f"{month_start.strftime('%Y-%m')} : "
            f"{response['totalResults']}"
        )

        time.sleep(1)  # helps avoid rate limits

coverage_df = pd.DataFrame(results)

coverage_df.to_csv(
    "monthly_media_coverage.csv",
    index=False
)

print("\nDone!")
print(coverage_df.head())