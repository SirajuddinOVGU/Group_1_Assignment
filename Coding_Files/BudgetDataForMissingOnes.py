"""BudgetDataForMissingOnes.py

For movies where Budget is '-', searches Wikipedia for the film,
then scrapes the Production Budget from the infobox.

Usage:
  python BudgetDataForMissingOnes.py
"""

import re
import time
import logging
import urllib.parse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
INPUT_FILE  = 'Outputs&ExcelFiles/BigDataSetCleaned.xlsx'
OUTPUT_FILE = 'Outputs&ExcelFiles/FinalBigDataSet.xlsx'
DELAY       = 2.0   # seconds between movies
# ────────────────────────────────────────────────────────────────────────────

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; movie-budget-research/1.0)',
    'Accept-Language': 'en-US,en;q=0.9',
}


def search_wikipedia(title: str, year: Optional[int] = None) -> Optional[str]:
    """Search Wikipedia and return the URL of the best matching film article."""
    query = f'{title} {year} film' if year else f'{title} film'
    search_url = (
        'https://en.wikipedia.org/w/api.php'
        f'?action=query&list=search&srsearch={urllib.parse.quote(query)}'
        '&format=json&srlimit=5'
    )
    # Retry up to 3 times with increasing backoff on 429
    for attempt in range(3):
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=15)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                logger.warning(f'  Rate limited — waiting {wait}s before retry...')
                time.sleep(wait)
                continue
            resp.raise_for_status()
            results = resp.json().get('query', {}).get('search', [])
            if not results:
                return None

            norm_title = title.lower().strip()

            # Prefer results whose title contains the movie name + 'film'
            for r in results:
                r_title = r['title'].lower()
                if norm_title in r_title and 'film' in r_title:
                    return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(r['title'].replace(' ', '_'))}"

            # Fallback: first result
            first = results[0]['title']
            return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(first.replace(' ', '_'))}"

        except requests.HTTPError:
            raise
        except Exception as e:
            logger.warning(f'  Wikipedia search failed: {e}')
            return None

    logger.warning('  Wikipedia search failed after retries.')
    return None


def scrape_budget_from_wikipedia(url: str) -> Optional[str]:
    """Fetch a Wikipedia film article and extract Budget from the infobox."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f'  Wikipedia page fetch failed: {e}')
        return None

    soup = BeautifulSoup(resp.content, 'html.parser')

    # Wikipedia film infobox uses a table with class 'infobox'
    infobox = soup.find('table', class_=re.compile(r'infobox'))
    if not infobox:
        logger.warning('  No infobox found on page.')
        return None

    for row in infobox.find_all('tr'):
        header = row.find('th')
        data   = row.find('td')
        if not header or not data:
            continue

        header_text = header.get_text(strip=True).lower()
        if 'budget' in header_text:
            raw = data.get_text(strip=True)
            # Extract first dollar amount, e.g. '$50,000,000' or '$50 million'
            # Try $X,XXX,XXX format first
            match = re.search(r'\$[\d,]+', raw)
            if match:
                return match.group()
            # Try '$X million' format → convert to full number
            match = re.search(r'\$\s*([\d.]+)\s*[-–]?\s*([\d.]+)?\s*million', raw, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                return f'${int(amount * 1_000_000):,}'

    logger.warning('  Budget row not found in infobox.')
    return None


def get_budget(title: str, year: Optional[int] = None) -> Optional[str]:
    wiki_url = search_wikipedia(title, year)
    if not wiki_url:
        return None
    logger.info(f'  Wikipedia: {wiki_url}')
    time.sleep(0.3)
    return scrape_budget_from_wikipedia(wiki_url)


def is_missing(val) -> bool:
    return str(val).strip() in ('-', '', 'nan', 'N/A', 'Not Found', 'None')


def main():
    logger.info(f'Loading: {INPUT_FILE}')
    sheets_dict = pd.read_excel(INPUT_FILE, sheet_name=None)

    for sheet_name, df in sheets_dict.items():
        logger.info(f'\n=== Sheet: {sheet_name} ===')

        if 'Release' not in df.columns or 'Budget' not in df.columns:
            logger.warning('  Missing required columns — skipping.')
            continue

        year_col = next((c for c in df.columns if str(c).strip().lower() == 'year'), None)

        missing_mask = df['Budget'].apply(is_missing)
        logger.info(f'  Movies with missing budget: {missing_mask.sum()}')

        for idx in df[missing_mask].index:
            title = str(df.at[idx, 'Release']).strip()
            year  = int(df.at[idx, year_col]) if year_col else None
            logger.info(f'\n  [{idx+1}/{len(df)}] {title} ({year})')

            budget = get_budget(title, year)

            if budget:
                df.at[idx, 'Budget'] = budget
                logger.info(f'  ✓ {budget}')
            else:
                logger.warning('  ✗ Budget not found.')

            time.sleep(DELAY)

        sheets_dict[sheet_name] = df

    logger.info(f'\nSaving to: {OUTPUT_FILE}')
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    logger.info('✓ Done!')


if __name__ == '__main__':
    main()