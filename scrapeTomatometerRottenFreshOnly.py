"""scrapeTomatometer.py
Read an Excel file, scrape Rotten Tomatoes tomatometer ratings for movies, and export enhanced Excel file.

Usage:
  pip install pandas openpyxl requests beautifulsoup4
  python scrapeTomatometer.py --input MovieListBoxOffice.xlsx --output MovieListBoxOffice_WithTomatometer.xlsx

Outputs an Excel file with all original data plus a new 'Tomatometer' column in each sheet.
"""

import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_release_column(df) -> Optional[str]:
    """Find the 'Release' column (case-insensitive) in a dataframe."""
    for c in df.columns:
        if str(c).strip().lower() == 'release':
            return c
    return None


def parse_percentage(score_text: Optional[str]) -> Optional[float]:
    """Extract a numeric percentage from a Tomatometer score string."""
    if not score_text:
        return None

    cleaned = str(score_text).strip().replace('%', '')
    try:
        return float(cleaned)
    except ValueError:
        return None


def classify_tomatometer(score_text: Optional[str]) -> str:
    """Classify a movie as Fresh or Rotten using the 60% Tomatometer cutoff."""
    percentage = parse_percentage(score_text)
    if percentage is None:
        return 'Unknown'
    return 'Fresh' if percentage >= 60 else 'Rotten'


def get_tomatometer_score(movie_name: str, max_retries: int = 3) -> Optional[Dict[str, str]]:
    """
    Scrape ONLY the tomatometer score, review count, and icon status for a given movie from Rotten Tomatoes.
    Returns a dict with 'percentage', 'reviews', and 'icon' keys, or None if not found.
    
    Icon status:
    - "Fresh" (60%+)
    - "Rotten" (<60%)
    """
    if not movie_name or str(movie_name).strip() == '':
        return None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    search_url = f"https://www.rottentomatoes.com/search?search={urllib.parse.quote(str(movie_name))}"
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Searching for '{movie_name}'...")
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for search result containers
            search_containers = soup.find_all('a', class_=lambda x: x and 'search-page-media-row' in x)
            
            if not search_containers:
                # Fallback: look for any /m/ links in search results area
                results_section = soup.find('div', class_=lambda x: x and 'search' in str(x).lower())
                if results_section:
                    search_containers = results_section.find_all('a', href=lambda x: x and '/m/' in x)
            
            if not search_containers:
                logger.warning(f"No search results found for '{movie_name}'")
                return None
            
            # Get the first relevant result
            movie_link = None
            for container in search_containers:
                link = container.get('href', '')
                if link and '/m/' in link:
                    movie_link = link
                    break
            
            if not movie_link:
                logger.warning(f"Could not extract movie link for '{movie_name}'")
                return None
            
            if not movie_link.startswith('http'):
                movie_link = 'https://www.rottentomatoes.com' + movie_link
            
            logger.info(f"Found link: {movie_link}")
            
            # Fetch the movie page
            time.sleep(0.5)
            movie_response = requests.get(movie_link, headers=headers, timeout=10)
            movie_response.raise_for_status()
            
            movie_soup = BeautifulSoup(movie_response.content, 'html.parser')
            
            # Find tomatometer percentage (critics-score slot)
            critics_score = movie_soup.find('rt-text', {'slot': 'critics-score'})
            tomatometer_percent = None
            if critics_score:
                tomatometer_percent = critics_score.get_text(strip=True)
            
            # Find review count (critics-reviews slot)
            critics_reviews = movie_soup.find('rt-link', {'slot': 'critics-reviews'})
            review_count = None
            if critics_reviews:
                review_count = critics_reviews.get_text(strip=True)
            
            # Find icon status (certified + sentiment)
            icon_status = classify_tomatometer(tomatometer_percent)

            # Verify we found the tomatometer (not audience score or error page)
            if not tomatometer_percent:
                logger.warning(f"Could not find tomatometer percentage for '{movie_name}'")
                return None
            
            logger.info(f"✓ '{movie_name}': {tomatometer_percent} ({review_count}) - {icon_status}")
            
            return {
                'percentage': tomatometer_percent,
                'reviews': review_count if review_count else 'N/A',
                'icon': icon_status
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for '{movie_name}': {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            logger.error(f"Unexpected error for '{movie_name}': {e}")
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Add Rotten Tomatoes tomatometer ratings to movie Excel data')
    parser.add_argument('--input', '-i', required=True, help='Input Excel file (.xlsx)')
    parser.add_argument('--output', '-o', default='MovieListBoxOffice_WithTomatometer.xlsx', help='Output Excel filename')
    parser.add_argument('--delay', '-d', type=float, default=1.5, help='Delay between requests (seconds)')
    args = parser.parse_args()

    # Load all sheets into a dictionary of dataframes
    logger.info(f"Loading Excel file: {args.input}")
    sheets_dict = pd.read_excel(args.input, sheet_name=None)
    logger.info(f"Found {len(sheets_dict)} sheets: {list(sheets_dict.keys())}")
    
    # Process each sheet
    for sheet_name, df in sheets_dict.items():
        logger.info(f"\n=== Processing Sheet: {sheet_name} ===")
        
        # Find Release column
        release_col = get_release_column(df)
        if release_col is None:
            logger.warning(f"No 'Release' column found in sheet '{sheet_name}', skipping")
            continue
        
        # Initialize Tomatometer, Reviews, and Icon columns
        df['Tomatometer'] = ''
        df['Tomatometer Reviews'] = ''
        df['Tomatometer Icon'] = ''
        
        # Scrape tomatometer for each movie
        for idx, movie_name in enumerate(df[release_col], 1):
            total = len(df)
            logger.info(f"\n[{sheet_name}: {idx}/{total}]")
            
            result = get_tomatometer_score(movie_name)
            if result:
                df.at[idx - 1, 'Tomatometer'] = result.get('percentage', '')
                df.at[idx - 1, 'Tomatometer Reviews'] = result.get('reviews', '')
                df.at[idx - 1, 'Tomatometer Icon'] = result.get('icon', '')
            
            time.sleep(args.delay)
        
        # Update the dataframe in the dict
        sheets_dict[sheet_name] = df
    
    # Export to Excel
    logger.info(f"\nExporting to Excel: {args.output}")
    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    logger.info(f"✓ Successfully exported to {args.output}")


if __name__ == '__main__':
    main()
