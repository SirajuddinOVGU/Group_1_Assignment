"""Scrapes budget data from Box Office Mojo for movies in the Excel file (2015-2019).

Strategy:
  1. For each year (2015-2019), fetch the wide-release rankings page
  2. Collect each movie's detail page URL from the table
  3. Match those URLs to movies in the Excel sheet by rank
  4. Visit each movie detail page and scrape the Budget field
  5. Write the budget value back into the existing 'Budget' column

Usage:
  pip install pandas openpyxl requests beautifulsoup4
  python ScrapeBudgetBoxOfficeMojo.py \
      --input  MovieListBoxOffice_WithTomatometer_Certified.xlsx \
      --output MovieListBoxOffice_WithBudget.xlsx
"""

import argparse
import time
import logging
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import load_workbook

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}

YEAR_URL = (
    'https://www.boxofficemojo.com/year/{year}/'
    '?grossesOption=totalGrosses&releaseScale=wide&sort=rank&sortDir=asc'
)


def fetch(url: str, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            logger.warning(f'Attempt {attempt+1}/{retries} failed for {url}: {e}')
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
    return None


def get_movie_links_for_year(year: int) -> list[tuple[int, str, str]]:
    """
    Returns list of (rank, title, detail_url) for all wide releases in a year.
    """
    url = YEAR_URL.format(year=year)
    logger.info(f'Fetching year page: {url}')
    r = fetch(url)
    if not r:
        logger.error(f'Could not fetch year page for {year}')
        return []

    soup = BeautifulSoup(r.content, 'html.parser')

    # The table rows contain rank in first td and a link with /release/ in the second td
    results = []
    table = soup.find('table')
    if not table:
        logger.error(f'No table found on year page for {year}')
        return []

    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < 2:
            continue
        # First cell = rank
        rank_text = cells[0].get_text(strip=True)
        try:
            rank = int(rank_text)
        except ValueError:
            continue

        # Find the /release/ link in the row
        link_tag = row.find('a', href=re.compile(r'/release/'))
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        href = link_tag['href'].split('?')[0]  # strip query params
        detail_url = 'https://www.boxofficemojo.com' + href

        results.append((rank, title, detail_url))

    logger.info(f'Found {len(results)} movies for {year}')
    return results


def scrape_budget(detail_url: str) -> str:
    """
    Visit a Box Office Mojo movie detail page and return the Budget value.
    Returns the raw string (e.g. '$250,000,000') or '' if not found.
    """
    r = fetch(detail_url)
    if not r:
        return ''

    soup = BeautifulSoup(r.content, 'html.parser')

    # Budget is in a <div> structure like:
    # <span class="...">Budget</span>  followed by  <span class="...">$250,000,000</span>
    # The exact class names vary, so search by text content
    for span in soup.find_all(['span', 'div']):
        if span.get_text(strip=True).lower() == 'budget':
            # The value is in the next sibling or parent's next sibling
            sibling = span.find_next_sibling()
            if sibling:
                val = sibling.get_text(strip=True)
                if val and val != '-':
                    return val
            # Try parent approach
            parent = span.parent
            if parent:
                # Look for a money-like value in the parent
                parent_text = parent.get_text(separator='|', strip=True)
                parts = [p.strip() for p in parent_text.split('|')]
                for i, p in enumerate(parts):
                    if p.lower() == 'budget' and i + 1 < len(parts):
                        val = parts[i + 1]
                        if val and val != '-':
                            return val

    # Fallback: search all text blocks for "Budget" label in summary sections
    summary_divs = soup.find_all('div', class_=re.compile(r'summary|money|title-summary', re.I))
    for div in summary_divs:
        text = div.get_text(separator='\n', strip=True)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().lower() == 'budget' and i + 1 < len(lines):
                val = lines[i + 1].strip()
                if val and val != '-':
                    return val

    return ''


def main():
    parser = argparse.ArgumentParser(description='Add Box Office Mojo budget data to movie Excel file')
    parser.add_argument(
    '--input',
    '-i',
    default='Tomatometer_Certified.xlsx',
    help='Input Excel file (.xlsx)'
)
    parser.add_argument('--output', '-o', default='Data_with_Budget.xlsx', help='Output Excel filename')
    parser.add_argument('--delay',  '-d', type=float, default=1.5, help='Delay between requests (seconds)')
    parser.add_argument('--year',   '-y', type=int, default=None,
                        help='Process only this year (2015-2019). Default: all years.')
    args = parser.parse_args()

    years = [args.year] if args.year else list(range(2015, 2020))

    # Load all sheets
    logger.info(f'Loading: {args.input}')
    sheets = pd.read_excel(args.input, sheet_name=None, dtype=str)

    for year in years:
        sheet_name = str(year)
        if sheet_name not in sheets:
            logger.warning(f'Sheet "{sheet_name}" not found in Excel, skipping')
            continue

        df = sheets[sheet_name]
        logger.info(f'\n=== Year {year}: {len(df)} rows ===')

        # Ensure Budget column exists
        if 'Budget' not in df.columns:
            df['Budget'] = ''

        # Get ranked movie links from Box Office Mojo
        movie_links = get_movie_links_for_year(year)
        if not movie_links:
            logger.error(f'No links found for {year}, skipping')
            continue

        # Build rank -> (title, url) lookup
        rank_to_info = {rank: (title, url) for rank, title, url in movie_links}

        # Match rows by Rank column
        rank_col = None
        for c in df.columns:
            if str(c).strip().lower() == 'rank':
                rank_col = c
                break

        if rank_col is None:
            logger.error(f'No "Rank" column in sheet {year}, skipping')
            continue

        for idx, row in df.iterrows():
            # Skip if budget already filled
            existing = str(row.get('Budget', '')).strip()
            if existing and existing not in ('-', 'nan', ''):
                logger.info(f'[{year}] Row {idx+1}: already has budget "{existing}", skipping')
                continue

            try:
                rank = int(float(str(row[rank_col]).strip()))
            except (ValueError, TypeError):
                continue

            if rank not in rank_to_info:
                logger.warning(f'[{year}] Rank {rank} not found in scraped links')
                continue

            title, detail_url = rank_to_info[rank]
            logger.info(f'[{year}] Rank {rank}: {title} -> {detail_url}')

            budget = scrape_budget(detail_url)
            df.at[idx, 'Budget'] = budget if budget else '-'
            logger.info(f'  Budget: {budget if budget else "(not found)"}')

            time.sleep(args.delay)

        sheets[sheet_name] = df

    # Save output
    logger.info(f'\nSaving to: {args.output}')
    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.info(f'✓ Done! Output: {args.output}')


if __name__ == '__main__':
    main()