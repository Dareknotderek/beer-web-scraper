import argparse
import requests
from bs4 import BeautifulSoup
import json
import logging
import time
from urllib.parse import urljoin

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURE LOGGING
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS & DEFAULTS
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.93 Safari/537.36"
)
REQUEST_TIMEOUT = 10  # seconds
RETRY_DELAY = 3  # seconds between retries
MAX_RETRIES = 3  # number of times to retry a failed request

# ──────────────────────────────────────────────────────────────────────────────
# FUNCTIONS FOR REQUESTS WITH RETRIES
# ──────────────────────────────────────────────────────────────────────────────
def fetch_url(session, url):
    """
    Fetch the given URL using the provided session.
    Retries up to MAX_RETRIES on failure, with a delay between attempts.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logging.debug(f"Fetching URL (attempt {attempt}): {url}")
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts.")
                return None

# ──────────────────────────────────────────────────────────────────────────────
# RECIPE EXTRACTION LOGIC
# ──────────────────────────────────────────────────────────────────────────────
def extract_recipe(post):
    """
    Given a BeautifulSoup tag for a single recipe post, extract structured data.
    Returns a dict or None if mandatory fields are missing.
    """
    try:
        title_tag = post.find("div", class_="recipe-title")
        author_tag = post.find("div", class_="recipe-author")
        date_tag = post.find("div", class_="recipe-date")
        ingr_tag = post.find("div", class_="recipe-ingredients")
        instr_tag = post.find("div", class_="recipe-instructions")

        if not (title_tag and author_tag and date_tag and ingr_tag and instr_tag):
            logging.debug("One or more mandatory fields missing; skipping this post.")
            return None

        # Basic text fields
        title = title_tag.get_text(strip=True)
        author = author_tag.get_text(strip=True)
        date = date_tag.get_text(strip=True)

        # Attempt to split ingredients into a list of lines, if line breaks are present
        ingredients = []
        for line in ingr_tag.stripped_strings:
            ingredients.append(line)
        # Same for instructions
        instructions = []
        for line in instr_tag.stripped_strings:
            instructions.append(line)

        return {
            "title": title,
            "author": author,
            "date": date,
            "ingredients": ingredients,
            "instructions": instructions,
        }

    except Exception as e:
        logging.error(f"Error parsing a recipe post: {e}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# PAGINATION: FIND “NEXT PAGE” LINK (if any)
# ──────────────────────────────────────────────────────────────────────────────
def find_next_page(soup, base_url):
    """
    If pagination is present, detect a “next page” link and return its full URL.
    This assumes a link or button with rel="next" or a class named 'next-page'.
    """
    # Try rel="next"
    link = soup.find("a", rel="next")
    if link and link.get("href"):
        return urljoin(base_url, link["href"])

    # Fallback: look for a link with a recognizable class or text
    next_btn = soup.find("a", class_="next-page")
    if next_btn and next_btn.get("href"):
        return urljoin(base_url, next_btn["href"])

    # Fallback: look for literal text “Next” (case-insensitive) in a link
    for a in soup.find_all("a"):
        if a.get_text(strip=True).lower() in ("next", "more"):
            href = a.get("href")
            if href:
                return urljoin(base_url, href)

    return None

# ──────────────────────────────────────────────────────────────────────────────
# MAIN SCRAPING LOOP
# ──────────────────────────────────────────────────────────────────────────────
def scrape_recipes(start_url):
    """
    Scrape all recipe posts starting from start_url, following pagination if present.
    Returns a list of recipe dicts.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    current_url = start_url
    all_recipes = []

    while current_url:
        logging.info(f"Scraping page: {current_url}")
        response = fetch_url(session, current_url)
        if response is None:
            break

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all recipe posts on this page
        recipe_posts = soup.find_all("div", class_="recipe-post")
        logging.info(f"Found {len(recipe_posts)} posts on this page.")

        for post in recipe_posts:
            recipe = extract_recipe(post)
            if recipe:
                all_recipes.append(recipe)

        # Check for next page
        next_page = find_next_page(soup, current_url)
        if next_page and next_page != current_url:
            current_url = next_page
            # Respectful delay to avoid hammering the server
            time.sleep(1)
        else:
            current_url = None

    return all_recipes

# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT / ARGPARSE
# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Scrape homebrew recipes from a forum and save to JSON."
    )
    parser.add_argument(
        "url",
        help="Starting URL of the recipe listing page (e.g., https://www.example.com/recipes)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="homebrew_recipes.json",
        help="Path to output JSON file (default: homebrew_recipes.json)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_url = args.url
    output_path = args.output

    logging.info("Starting scraper...")
    recipes = scrape_recipes(start_url)
    logging.info(f"Scraped a total of {len(recipes)} recipes.")

    # Save as JSON
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved recipes to: {output_path}")
    except IOError as e:
        logging.error(f"Failed to write JSON file: {e}")

if __name__ == "__main__":
    main()
