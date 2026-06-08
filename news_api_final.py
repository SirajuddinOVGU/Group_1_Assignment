import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# NewsAPI key
api_key = "60ceb21f2784423aa8e2bc0531bdcb73"
base_url = "https://newsapi.org/v2/everything"

# Companies
companies = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "TSLA": "Tesla"
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
