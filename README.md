# Homebrew Recipe Scraper

A robust, configurable Python tool for scraping homebrew recipes from a forum, with support for pagination, retries, structured output, and logging.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Command-Line Arguments](#command-line-arguments)
7. [Output Format](#output-format)
8. [Customization](#customization)
9. [Error Handling & Logging](#error-handling--logging)
10. [Contributing](#contributing)

---

## Overview

This scraper navigates a homebrewing forum’s recipe section (including paginated pages), extracts structured data (title, author, date, ingredients, instructions) from each post, and saves the results to a JSON file. It employs retries, respectful delays, and a realistic User-Agent string to maximize reliability and minimize the chance of being blocked.

---

## Features

* **Command-Line Interface**
  Configure start URL, output file path, and verbosity via arguments.
* **Session with Custom Headers**
  Uses a persistent `requests.Session` with a modern User-Agent.
* **Automatic Retries**
  Retries failed HTTP requests up to three times, with delays between attempts.
* **Pagination Support**
  Detects “next page” links (via `rel="next"`, `.next-page` CSS class, or link text “Next/More”) and follows them automatically.
* **Structured Data Extraction**
  Parses ingredients and instructions into lists of lines (instead of raw blobs of text).
* **Logging**
  Detailed logs for each page scraped, including number of posts found, retry attempts, and parsing errors.
* **Respectful Delay**
  A short `time.sleep(1)` between pages to avoid hammering the server.
* **Graceful Error Handling**
  Skips any post missing mandatory fields rather than crashing. Catches file-write errors when exporting JSON.
* **UTF-8 Encoding**
  Ensures proper handling of non-ASCII characters when saving JSON.

---

## Requirements

* Python 3.7 or higher
* The following Python libraries:

  * `requests`
  * `beautifulsoup4`

You can install dependencies with:

```bash
pip install requests beautifulsoup4
```

---

## Installation

1. **Clone the repository** (or copy the script file):

   ```bash
   git clone https://github.com/yourusername/homebrew-recipe-scraper.git
   cd homebrew-recipe-scraper
   ```
2. **Make sure dependencies are installed**:

   ```bash
   pip install requests beautifulsoup4
   ```
3. **Ensure the main script is executable** (if using Unix/macOS):

   ```bash
   chmod +x scrape_recipes.py
   ```

---

## Usage

```bash
python scrape_recipes.py <START_URL> [OPTIONS]
```

* `<START_URL>`
  The URL of the first page listing forum recipes (e.g., `https://www.example-homebrewing-forum.com/recipes`).

* **Options**

  * `-o, --output <FILE>`
    Path to the output JSON file. Defaults to `homebrew_recipes.json`.
  * `-v, --verbose`
    Enable debug-level logging for detailed trace information.

**Example:**

```bash
python scrape_recipes.py https://www.example-homebrewing-forum.com/recipes \
                         -o my_recipes.json \
                         --verbose
```

This command:

1. Starts scraping at `https://www.example-homebrewing-forum.com/recipes`.
2. Outputs the results to `my_recipes.json`.
3. Prints debug logs to the console.

---

## Command-Line Arguments

| Argument              | Description                                                                | Default                 |
| --------------------- | -------------------------------------------------------------------------- | ----------------------- |
| `<START_URL>`         | (Positional) Starting URL of the recipe listing page.                      | N/A                     |
| `-o, --output <FILE>` | Path to the JSON file where scraped recipes will be saved.                 | `homebrew_recipes.json` |
| `-v, --verbose`       | Activate debug logging (shows detailed internal steps and retry attempts). | Disabled                |

---

## Output Format

The script produces a JSON array containing one object per recipe. Each recipe object has the following structure:

```jsonc
[
  {
    "title": "Example Recipe Title",
    "author": "Username123",
    "date": "2025-05-29",
    "ingredients": [
      "10 lbs Pale Malt",
      "1 lb Crystal Malt 60L",
      "1 oz Cascade Hops @ 60 min",
      "1 oz Cascade Hops @ 15 min"
    ],
    "instructions": [
      "Mash grains at 152°F for 60 minutes.",
      "Sparge with 170°F water.",
      "Boil for 60 minutes, adding hops as scheduled.",
      "Chill wort to 68°F and pitch yeast."
    ]
  },
  ...
]
```

* **title**: The recipe’s title (string).
* **author**: The forum username who posted the recipe (string).
* **date**: The date string as shown on the post (string).
* **ingredients**: A list of ingredient lines (array of strings).
* **instructions**: A list of instruction lines (array of strings).

---

## Customization

1. **Adjusting CSS Selectors**
   If your forum’s markup uses different classes or HTML tags, update the `extract_recipe(post)` function accordingly. For example:

   ```python
   title_tag = post.find("h2", class_="post-title")
   ```

   or

   ```python
   ingr_list_items = ingr_tag.find_all("li")
   ingredients = [li.get_text(strip=True) for li in ingr_list_items]
   ```

2. **Handling Additional Fields**
   To scrape images, ratings, or tags:

   * Locate the appropriate tag(s) in `extract_recipe()`.
   * Add new keys to the returned dictionary:

     ```python
     recipe["rating"] = post.find("span", class_="rating").get_text(strip=True)
     recipe["image_url"] = post.find("img", class_="recipe-image")["src"]
     ```

3. **Modifying Pagination Logic**

   * If your forum uses a different pattern (e.g., `?page=2` query parameter), adapt `find_next_page()` to detect and construct the “next page” URL accordingly.
   * For JavaScript-driven pagination, consider using a headless browser (e.g., Selenium) or an API (if available).

4. **Export Formats**

   * To output CSV instead of JSON, import Python’s `csv` module and write rows accordingly in the `main()` function.
   * To insert directly into a database, replace the JSON-dump block with your database client logic.

---

## Error Handling & Logging

* **Network/Timeout Errors**

  * The `fetch_url()` function retries up to 3 times (with a 3-second delay) before giving up.
  * If a page consistently fails, the scraper logs an error and moves on to stop the loop.

* **Missing Fields**

  * If a mandatory field (title, author, date, ingredients, or instructions) is missing, `extract_recipe()` returns `None` and the post is skipped (no crash).

* **Logging Levels**

  * **INFO** (default): Logs each page URL, number of posts found, and final summary.
  * **DEBUG** (when `-v`/`--verbose` is used): Detailed traces of HTTP attempts, retries, parsing decisions, and any missing-field warnings.

* **Output File Errors**

  * If writing to the JSON file fails (e.g., due to permissions), an error is logged instead of a silent failure.

---

## Contributing

1. **Fork this repository** and create a new branch for your feature or bugfix.
2. Write clear, concise commit messages describing your changes.
3. Update the `README.md` or documentation if you add new functionality.
4. Submit a pull request with your proposed changes.

Please adhere to the existing coding style—particularly around logging, function docstrings, and error handling.
