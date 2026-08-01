import os
import json
import re
import requests
from collections import Counter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

def setup_driver():
    """Sets up Chrome in headless mode with stealth and anti-paywall settings."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_articles(driver):
    """Scrapes the first 5 articles from the Opinion section."""
    driver.get("https://elpais.com/opinion/")

    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        ).click()
    except Exception:
        pass

    print("Fetching first 5 articles directly from homepage...")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.c")))
    article_elements = driver.find_elements(By.CSS_SELECTOR, "article.c")[:5]

    os.makedirs("images", exist_ok=True)
    articles_data = []

    for i, article in enumerate(article_elements):
        print(f"\n--- Processing Article {i+1}/5 ---")

        try:
            title = article.find_element(By.CSS_SELECTOR, "h2.c_t").text
        except Exception:
            title = "Title not found"

        try:
            content = article.find_element(By.CSS_SELECTOR, "p.c_d").text
        except Exception:
            content = "Content is empty or requires login"

        print(f"Title (ES): {title}")
        print(f"Content Snippet: {content[:100]}...")

        try:
            img_url = article.find_element(By.TAG_NAME, "img").get_attribute("src")
            if img_url:
                with open(f"images/article_{i+1}.jpg", 'wb') as f:
                    f.write(requests.get(img_url).content)
                print(f"Downloaded cover image: images/article_{i+1}.jpg")
        except Exception:
            pass

        articles_data.append({"title": title, "content": content})

    return articles_data

def translate_and_analyze(articles_data):
    """Translates titles to English and analyzes word frequency."""
    print("\n================ TRANSLATION ===================")
    translated_titles = []

    url = "https://google-translate113.p.rapidapi.com/api/v1/translator/text"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "google-translate113.p.rapidapi.com",
        "x-rapidapi-key": os.environ.get("RAPIDAPI_KEY")
    }

    for i, data in enumerate(articles_data):
        es_title = data["title"]
        en_title = es_title

        if es_title and es_title != "Title not found":
            try:
                payload = {"from": "es", "to": "en", "text": es_title}
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    en_title = response.json().get("trans", es_title)
            except Exception as e:
                print(f"Translation error: {e}")

        translated_titles.append(en_title)
        data["translated_title"] = en_title
        print(f"Article {i+1}:")
        print(f"Original:   {es_title}")
        print(f"Translated: {en_title}\n")

    # Analyze repeated words across all translated headers
    print("\n================ ANALYSIS ======================")
    all_text = " ".join(translated_titles).lower()
    words = re.findall(r'\b[a-z]+\b', all_text)
    word_counts = Counter(words)
    repeated_words = {word: count for word, count in word_counts.items() if count > 2}

    if repeated_words:
        print("Words repeated more than twice across all translated headers:")
        for word, count in repeated_words.items():
            print(f" - '{word}': {count} times")
    else:
        print("No words were repeated more than twice across the headers.")

    final_output = {
        "articles": articles_data,
        "analysis": {"repeated_words": repeated_words}
    }

    with open('scraped_articles_local.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    print("\nScraped text, translations, and analysis successfully saved to 'scraped_articles_local.json'!")

def main():
    driver = None
    try:
        driver = setup_driver()
        articles_data = scrape_articles(driver)
        translate_and_analyze(articles_data)
        print("\nLocal Execution Completed Successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
