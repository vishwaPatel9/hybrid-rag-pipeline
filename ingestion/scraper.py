import os
import json
import uuid
import sys
import requests
import trafilatura
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def scrape_single_url(url):
    """
    Universal article scraper using trafilatura.
    Works on any news site, blog, or article URL — no site-specific CSS selectors needed.
    """
    article_id = str(uuid.uuid4())
    data = {
        "article_id": article_id,
        "url": url,
        "title": "",
        "author": "Unknown",
        "date": "Unknown",
        "body": "",
        "image_path": "",
        "source_domain": ""
    }

    try:
        # Download and extract content using trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"  [SKIP] Could not download: {url}")
            return None

        # Extract structured data (title, author, date, body, etc.)
        result = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            output_format='json',
            with_metadata=True
        )

        if not result:
            print(f"  [SKIP] trafilatura found no content: {url}")
            return None

        parsed = json.loads(result)
        data["title"] = parsed.get("title") or ""
        data["author"] = parsed.get("author") or "Unknown"
        data["date"] = parsed.get("date") or "Unknown"
        data["body"] = parsed.get("text") or ""

        # Extract domain from URL for provenance
        from urllib.parse import urlparse
        data["source_domain"] = urlparse(url).netloc

        print(f"  [OK] {data['title'][:60]}...")

    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return None

    return data if data["body"].strip() else None


def scrape_urls(urls, max_workers=5):
    """
    Scrape a list of article URLs in parallel.
    Returns a list of successfully scraped article dicts.
    """
    print(f"Scraping {len(urls)} URLs with {max_workers} workers...")
    articles = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(scrape_single_url, urls))

    for res in results:
        if res:
            articles.append(res)

    print(f"Successfully scraped {len(articles)}/{len(urls)} articles.")
    return articles


def main():
    """
    Main entry-point when run directly.
    Reads URLs from ingestion/urls.txt (one URL per line).
    """
    urls_file = os.path.join(BASE_DIR, "urls.txt")

    if not os.path.exists(urls_file):
        # Provide a helpful default if no urls.txt found
        print(f"No urls.txt found at {urls_file}.")
        print("Creating a sample urls.txt with example URLs...")
        sample_urls = [
            "https://elpais.com/opinion/",
            "https://www.bbc.com/news/articles/c4ngj32ky1xo",
            "https://www.theguardian.com/commentisfree/2024/aug/01/britain-riots-far-right",
        ]
        with open(urls_file, "w") as f:
            f.write("\n".join(sample_urls))
        print(f"Edit {urls_file} and re-run.\n")
        urls = sample_urls
    else:
        with open(urls_file, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"Loaded {len(urls)} URLs from {urls_file}")

    articles = scrape_urls(urls)

    out_path = os.path.join(BASE_DIR, "raw_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(articles)} articles to {out_path}")


if __name__ == "__main__":
    main()
