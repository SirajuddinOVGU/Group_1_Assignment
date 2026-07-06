#Web scraping process:
#Read movie list from input Excel file
#Scrape Tomatometer, Review Count from Rotten Tomatoes
#Scrape Budget from Box Office Mojo movie detail pages
#For movies still missing Budget, search Wikipedia as fallback
#Export all data to output Excel file

import re
import time
import logging
import urllib.parse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_FILE  = '/workspaces/Group_1_Assignment/Outputs&ExcelFiles/1DataFromBoxOfficeMojo.xlsx'
OUTPUT_FILE = '/workspaces/Group_1_Assignment/Outputs&ExcelFiles/2DataAfterWebScraping.xlsx'
DELAY       = 1.5  # seconds between requests
# ─────────────────────────────────────────────────────────────────────────────

RT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BOM_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}

WIKI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; movie-budget-research/1.0)',
    'Accept-Language': 'en-US,en;q=0.9',
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_release_column(df) -> Optional[str]:
    #Find the 'Release' column (case-insensitive) in a dataframe.
    for c in df.columns:
        if str(c).strip().lower() == 'release':
            return c
    return None


def is_missing(val) -> bool:
    return str(val).strip() in ('-', '', 'nan', 'N/A', 'Not Found', 'None')


def fetch(url: str, headers: dict, retries: int = 3, delay: float = 2.0) -> Optional[requests.Response]:
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            logger.warning(f'Attempt {attempt+1}/{retries} failed for {url}: {e}')
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
    return None


# ── Rotten Tomatoes ──────────────────────────────────────────────────────────

def parse_percentage(score_text: Optional[str]) -> Optional[float]:
    #Extract a numeric percentage from a Tomatometer score string.
    if not score_text:
        return None
    cleaned = str(score_text).strip().replace('%', '')
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_review_count(review_text: Optional[str]) -> Optional[int]:
    #Extract the numeric review count from review count text.
    if not review_text:
        return None
    cleaned = str(review_text).strip().replace(' Reviews', '').replace(' Review', '')
    cleaned = ''.join(c for c in cleaned if c.isdigit())
    try:
        return int(cleaned) if cleaned else None
    except ValueError:
        return None


def extract_movie_slug(movie_link: str) -> Optional[str]:
    #Extract the movie slug from a Rotten Tomatoes movie URL.
    if '/m/' not in movie_link:
        return None
    parts = movie_link.split('/m/')
    if len(parts) < 2:
        return None
    slug = parts[1].strip('/')
    return slug.split('?')[0]


def count_top_critics_reviews(movie_slug: str, headers: Dict[str, str]) -> int:
    #Scrape the Top Critics page and count actual rendered review cards.
    #Stop counting once we reach 5 (requirement met).
    #Returns the count (capped at 5 if found).
    if not movie_slug:
        return 0
    top_critics_url = f"https://www.rottentomatoes.com/m/{movie_slug}/reviews/top-critics"
    try:
        logger.info(f"Checking Top Critics page: {top_critics_url}")
        response = requests.get(top_critics_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        review_cards = soup.find_all(['review-card', 'div'], class_=lambda x: x and 'review' in str(x).lower())
        count = 0
        for card in review_cards:
            if card.name == 'review-card' or (card.name == 'div' and 'review' in str(card.get('class', '')).lower()):
                count += 1
                if count >= 5:
                    logger.info(f"Found at least 5 Top Critics reviews for {movie_slug}")
                    return 5
        logger.info(f"Found {count} Top Critics reviews for {movie_slug}")
        return count
    except Exception as e:
        logger.error(f"Error checking Top Critics page for {movie_slug}: {e}")
        return 0


def classify_tomatometer(score_text: Optional[str], review_count_text: Optional[str] = None,
                         movie_slug: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> str:
    #Classify a movie as Rotten, Fresh or Certified Fresh.
    #- Rotten: < 60%
    #- Fresh: 60-74%
    #- Certified Fresh: at least 75% with 80+ reviews, and 5+ Top Critics reviews, if not it is still Fresh
    percentage = parse_percentage(score_text)
    if percentage is None:
        return 'Unknown'
    if percentage < 60:
        return 'Rotten'
    if percentage < 75:
        return 'Fresh'
    review_count = parse_review_count(review_count_text)
    if review_count is None or review_count < 80:
        return 'Fresh'
    if movie_slug and headers:
        top_critics_count = count_top_critics_reviews(movie_slug, headers)
        if top_critics_count >= 5:
            return 'Certified Fresh'
    return 'Fresh'


def get_tomatometer_score(movie_name: str, max_retries: int = 3) -> Optional[Dict[str, str]]:
    #Scrape ONLY the tomatometer score and review count for a given movie from Rotten Tomatoes.
    #Returns a dict with 'percentage', 'reviews', and 'slug' keys, or None if not found.
    if not movie_name or str(movie_name).strip() == '':
        return None
    search_url = f"https://www.rottentomatoes.com/search?search={urllib.parse.quote(str(movie_name))}"
    for attempt in range(max_retries):
        try:
            logger.info(f"Searching RT for '{movie_name}'...")
            response = requests.get(search_url, headers=RT_HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            search_containers = soup.find_all('a', class_=lambda x: x and 'search-page-media-row' in x)
            if not search_containers:
                results_section = soup.find('div', class_=lambda x: x and 'search' in str(x).lower())
                if results_section:
                    search_containers = results_section.find_all('a', href=lambda x: x and '/m/' in x)
            if not search_containers:
                logger.warning(f"No RT search results for '{movie_name}'")
                return None
            movie_link = None
            for container in search_containers:
                link = container.get('href', '')
                if link and '/m/' in link:
                    movie_link = link
                    break
            if not movie_link:
                logger.warning(f"Could not extract RT movie link for '{movie_name}'")
                return None
            if not movie_link.startswith('http'):
                movie_link = 'https://www.rottentomatoes.com' + movie_link
            logger.info(f"Found RT link: {movie_link}")
            movie_slug = extract_movie_slug(movie_link)
            time.sleep(0.5)
            movie_response = requests.get(movie_link, headers=RT_HEADERS, timeout=10)
            movie_response.raise_for_status()
            movie_soup = BeautifulSoup(movie_response.content, 'html.parser')
            critics_score = movie_soup.find('rt-text', {'slot': 'critics-score'})
            tomatometer_percent = None
            if critics_score:
                tomatometer_percent = critics_score.get_text(strip=True)
            critics_reviews = movie_soup.find('rt-link', {'slot': 'critics-reviews'})
            review_count = None
            if critics_reviews:
                review_count = critics_reviews.get_text(strip=True)
            if not tomatometer_percent:
                logger.warning(f"Could not find tomatometer percentage for '{movie_name}'")
                return None
            logger.info(f"✓ '{movie_name}': {tomatometer_percent} ({review_count})")
            return {
                'percentage': tomatometer_percent,
                'reviews': review_count if review_count else 'N/A',
                'slug': movie_slug
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"RT request error for '{movie_name}': {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            logger.error(f"RT unexpected error for '{movie_name}': {e}")
    return None


# ── Extracting Box Office Mojo Budget ───────────────────────────────────────────────────

BOM_YEAR_URL = (
    'https://www.boxofficemojo.com/year/{year}/'
    '?grossesOption=totalGrosses&releaseScale=wide&sort=rank&sortDir=asc'
)


def get_movie_links_for_year(year: int) -> list:
    """Returns list of (rank, title, detail_url) for all wide releases in a year."""
    url = BOM_YEAR_URL.format(year=year)
    logger.info(f'Fetching BOM year page: {url}')
    r = fetch(url, BOM_HEADERS)
    if not r:
        logger.error(f'Could not fetch BOM year page for {year}')
        return []
    soup = BeautifulSoup(r.content, 'html.parser')
    results = []
    table = soup.find('table')
    if not table:
        logger.error(f'No table found on BOM year page for {year}')
        return []
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < 2:
            continue
        rank_text = cells[0].get_text(strip=True)
        try:
            rank = int(rank_text)
        except ValueError:
            continue
        link_tag = row.find('a', href=re.compile(r'/release/'))
        if not link_tag:
            continue
        title = link_tag.get_text(strip=True)
        href = link_tag['href'].split('?')[0]
        detail_url = 'https://www.boxofficemojo.com' + href
        results.append((rank, title, detail_url))
    logger.info(f'Found {len(results)} movies for {year} on BOM')
    return results


def scrape_budget_from_bom(detail_url: str) -> str:
    """Visit a Box Office Mojo movie detail page and return the Budget value."""
    r = fetch(detail_url, BOM_HEADERS)
    if not r:
        return ''
    soup = BeautifulSoup(r.content, 'html.parser')
    for span in soup.find_all(['span', 'div']):
        if span.get_text(strip=True).lower() == 'budget':
            sibling = span.find_next_sibling()
            if sibling:
                val = sibling.get_text(strip=True)
                if val and val != '-':
                    return val
            parent = span.parent
            if parent:
                parent_text = parent.get_text(separator='|', strip=True)
                parts = [p.strip() for p in parent_text.split('|')]
                for i, p in enumerate(parts):
                    if p.lower() == 'budget' and i + 1 < len(parts):
                        val = parts[i + 1]
                        if val and val != '-':
                            return val
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


# ── Extracting Wikipedia Budget If Needed ────────────────────────────────────────────────

def search_wikipedia(title: str, year: Optional[int] = None) -> Optional[str]:
    """Search Wikipedia and return the URL of the best matching film article."""
    query = f'{title} {year} film' if year else f'{title} film'
    search_url = (
        'https://en.wikipedia.org/w/api.php'
        f'?action=query&list=search&srsearch={urllib.parse.quote(query)}'
        '&format=json&srlimit=5'
    )
    for attempt in range(3):
        try:
            resp = requests.get(search_url, headers=WIKI_HEADERS, timeout=15)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                logger.warning(f'Wikipedia rate limited — waiting {wait}s...')
                time.sleep(wait)
                continue
            resp.raise_for_status()
            results = resp.json().get('query', {}).get('search', [])
            if not results:
                return None
            norm_title = title.lower().strip()
            for r in results:
                r_title = r['title'].lower()
                if norm_title in r_title and 'film' in r_title:
                    return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(r['title'].replace(' ', '_'))}"
            first = results[0]['title']
            return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(first.replace(' ', '_'))}"
        except requests.HTTPError:
            raise
        except Exception as e:
            logger.warning(f'Wikipedia search failed: {e}')
            return None
    logger.warning('Wikipedia search failed after retries.')
    return None


def scrape_budget_from_wikipedia(url: str) -> Optional[str]:
    """Fetch a Wikipedia film article and extract Budget from the infobox."""
    try:
        resp = requests.get(url, headers=WIKI_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f'Wikipedia page fetch failed: {e}')
        return None
    soup = BeautifulSoup(resp.content, 'html.parser')
    infobox = soup.find('table', class_=re.compile(r'infobox'))
    if not infobox:
        logger.warning('No infobox found on Wikipedia page.')
        return None
    for row in infobox.find_all('tr'):
        header = row.find('th')
        data   = row.find('td')
        if not header or not data:
            continue
        header_text = header.get_text(strip=True).lower()
        if 'budget' in header_text:
            raw = data.get_text(strip=True)
            match = re.search(r'\$[\d,]+', raw)
            if match:
                return match.group()
            match = re.search(r'\$\s*([\d.]+)\s*[-–]?\s*([\d.]+)?\s*million', raw, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                return f'${int(amount * 1_000_000):,}'
    logger.warning('Budget row not found in Wikipedia infobox.')
    return None


def get_budget_from_wikipedia(title: str, year: Optional[int] = None) -> Optional[str]:
    wiki_url = search_wikipedia(title, year)
    if not wiki_url:
        return None
    logger.info(f'  Wikipedia: {wiki_url}')
    time.sleep(0.3)
    return scrape_budget_from_wikipedia(wiki_url)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    logger.info(f'Loading: {INPUT_FILE}')
    df = pd.read_excel(INPUT_FILE)
    logger.info(f'Loaded {len(df)} rows')

    release_col = get_release_column(df)
    if release_col is None:
        logger.error("No 'Release' column found. Please check your column names.")
        return

    # ── Step 1: Scrape from Rotten Tomatoes ───────────────────────────────────────
    logger.info('\n=== Step 1: Scraping Rotten Tomatoes ===')

    df['Tomatometer'] = ''
    df['Tomatometer Reviews'] = ''
    df['Tomatometer Icon'] = ''

    total = len(df)
    for idx, movie_name in enumerate(df[release_col], 1):
        logger.info(f'\n[RT {idx}/{total}] {movie_name}')
        result = get_tomatometer_score(movie_name)
        if result:
            percentage = result.get('percentage', '')
            reviews    = result.get('reviews', '')
            movie_slug = result.get('slug')
            df.at[idx - 1, 'Tomatometer']         = percentage
            df.at[idx - 1, 'Tomatometer Reviews'] = reviews
            df.at[idx - 1, 'Tomatometer Icon']    = classify_tomatometer(percentage, reviews, movie_slug, RT_HEADERS)
        time.sleep(DELAY)

    # ── Step 2: Scrape Budget from Box Office Mojo ───────────────────────────
    logger.info('\n=== Step 2: Scraping Budget from Box Office Mojo ===')

    if 'Budget' not in df.columns:
        df['Budget'] = ''

    year_col = next((c for c in df.columns if str(c).strip().lower() == 'year'), None)
    rank_col = next((c for c in df.columns if str(c).strip().lower() == 'rank'), None)

    if rank_col and year_col:
        # Build a lookup: {year: {rank: (title, detail_url)}}
        bom_lookup = {}
        for year in range(2015, 2020):
            links = get_movie_links_for_year(year)
            bom_lookup[year] = {rank: (title, url) for rank, title, url in links}

        for idx, row in df.iterrows():
            existing = str(row.get('Budget', '')).strip()
            if existing and not is_missing(existing):
                logger.info(f'Row {idx+1}: budget already present, skipping BOM')
                continue
            try:
                year = int(float(str(row[year_col]).strip()))
                rank = int(float(str(row[rank_col]).strip()))
            except (ValueError, TypeError):
                continue
            if year not in bom_lookup or rank not in bom_lookup[year]:
                logger.warning(f'Row {idx+1}: rank {rank} not found in BOM for {year}')
                continue
            title, detail_url = bom_lookup[year][rank]
            logger.info(f'[BOM] {title} -> {detail_url}')
            budget = scrape_budget_from_bom(detail_url)
            df.at[idx, 'Budget'] = budget if budget else '-'
            logger.info(f'  Budget: {budget if budget else "(not found)"}')
            time.sleep(DELAY)
    else:
        logger.warning('No Rank or Year column found — skipping BOM budget scrape.')

    # ── Step 3: Wikipedia fallback for still-missing budgets ─────────────────
    logger.info('\n=== Step 3: Wikipedia fallback for missing budgets ===')

    missing_mask = df['Budget'].apply(is_missing)
    logger.info(f'Movies still missing budget: {missing_mask.sum()}')

    for idx in df[missing_mask].index:
        title = str(df.at[idx, release_col]).strip()
        year  = None
        if year_col:
            try:
                year = int(df.at[idx, year_col])
            except (ValueError, TypeError):
                pass
        logger.info(f'\n[Wiki] {title} ({year})')
        budget = get_budget_from_wikipedia(title, year)
        if budget:
            df.at[idx, 'Budget'] = budget
            logger.info(f'  ✓ {budget}')
        else:
            logger.warning('  ✗ Budget not found on Wikipedia either.')
        time.sleep(DELAY)

    # ── Export ────────────────────────────────────────────────────────────────
    logger.info(f'\nExporting to: {OUTPUT_FILE}')
    df.to_excel(OUTPUT_FILE, index=False)
    logger.info('✓ Done!')


if __name__ == '__main__':
    main()