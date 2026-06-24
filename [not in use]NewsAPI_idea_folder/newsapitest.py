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
    "GOOGL": "Alphabet",
    "META": "Meta",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "BRK-B": "Berkshire Hathaway",
    "JPM": "JPMorgan Chase",
    "JNJ": "Johnson & Johnson",
    "V": "Visa",
    "PG": "Procter & Gamble",
    "XOM": "Exxon Mobil",
    "UNH": "UnitedHealth Group",
    "HD": "Home Depot",
    "MA": "Mastercard",
    "PFE": "Pfizer",
    "BAC": "Bank of America",
    "CVX": "Chevron",
    "WMT": "Walmart",
    "ABT": "Abbott Laboratories",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "NFLX": "Netflix",
    "DIS": "The Walt Disney Company",
    "AGX": "Argan Inc",
    "PLAB": "Photronics"
    "BKE": "Buckle Inc.",
    "KLIC": "Kulicke and Soffa",
    "VRA": "Vera Bradley",
    "NHTC": "Natural Health Trends",
    "ELA": "Envela Corporation",
    "WHG": "Westwood Holdings",
    "ULBI": "Ultralife Corporation",
    "MLAB": "Mesa Laboratories",
    "PRQR": "ProQR Therapeutics",
    "OHI": "Omega Healthcare",
    "HALL": "Hallmark Financial",
    "LWAY": "Lifeway Foods",
    "IDT": "IDT Corporation"
    "GBLI": "Global Indemnity",
    "AE": "Adams Resources",
    "PFIN": "P&F Industries",
    "MLR": "Miller Industries",
    "CODA": "Coda Octopus",
    "BRT": "BRT Realty Trust",
    "WSTL": "Westell Technologies"
    "LIQT": "Sievert Larson",
    "BRMK": "Broadmark Realty",
    "DRCT": "Direct Digital Holdings"
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
