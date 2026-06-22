import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# NewsAPI key
api_key = "aaee18fbaac94d8e8948136bfd5e687e" #Carmenapi: 60ceb21f2784423aa8e2bc0531bdcb73 #Siraapi: aaee18fbaac94d8e8948136bfd5e687e
base_url = "https://newsapi.org/v2/everything"

# Companies
companies = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Google",
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
    "PLAB": "Photronics",
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
    "IDT": "IDT Corporation",
    "GBLI": "Global Indemnity",
    "AE": "Adams Resources",
    "PFIN": "P&F Industries",
    "MLR": "Miller Industries",
    "CODA": "Coda Octopus",
    "BRT": "BRT Realty Trust",
    "WSTL": "Westell Technologies",
    "LIQT": "Sievert Larson",
    "BRMK": "Broadmark Realty",
    "DRCT": "Direct Digital Holdings"
}

# Use recent data only (free tier allows last ~30 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

results = []
errors = []

for ticker, company in companies.items():
    print(f"\nProcessing {company}")

    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        from_date = current_date.strftime("%Y-%m-%d")
        to_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            params = {
                "q": company,
                "from": from_date,
                "to": to_date,
                "language": "en",
                "pageSize": 1,  # only need totalResults
                "apiKey": api_key
            }
            
            response = requests.get(base_url, params=params)
            data = response.json()

            # Check if response is valid
            if data.get("status") == "error":
                error_msg = f"{company} ({from_date}): {data.get('message', 'Unknown error')}"
                errors.append(error_msg)
                print(f"  ERROR: {error_msg}")
                continue

            article_count = data.get("totalResults", 0)
            results.append({
                "ticker": ticker,
                "company": company,
                "date": from_date,
                "article_count": article_count
            })

            print(f"  {from_date}: {article_count} articles")

            # Rate limiting
            time.sleep(1.2)

        except Exception as e:
            error_msg = f"{company} ({from_date}): {str(e)}"
            errors.append(error_msg)
            print(f"  EXCEPTION: {error_msg}")
            time.sleep(2)
            continue

# Create DataFrame
coverage_df = pd.DataFrame(results)

# Save to CSV
output_file = "monthly_media_coverage.csv"
coverage_df.to_csv(output_file, index=False)

print("\n" + "="*60)
print(f"✓ Data saved to: {output_file}")
print(f"✓ Total records: {len(coverage_df)}")

if errors:
    print(f"\n⚠ Errors encountered ({len(errors)}):")
    for error in errors:
        print(f"  - {error}")

print("\nFirst few records:")
print(coverage_df.head(10))

print("\nSummary by company:")
print(coverage_df.groupby("company")["article_count"].agg(["sum", "mean", "max"]).round(1))
