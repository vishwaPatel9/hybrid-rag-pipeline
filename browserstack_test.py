import os
import json
import re
import requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

BROWSERSTACK_USERNAME = os.environ.get("BROWSERSTACK_USERNAME")
BROWSERSTACK_ACCESS_KEY = os.environ.get("BROWSERSTACK_ACCESS_KEY")

if not BROWSERSTACK_USERNAME or not BROWSERSTACK_ACCESS_KEY:
    print("ERROR: Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in your .env file!")
    exit(1)

URL = "https://hub-cloud.browserstack.com/wd/hub"

def get_bstack_options(browser_name, os_name, os_version, device_name=None):
    """Builds BrowserStack capabilities for a given browser/device."""
    bstack_options = {
        "os": os_name,
        "osVersion": os_version,
        "sessionName": f"El Pais Scraping - {browser_name} on {os_name}",
        "buildName": "BrowserStack Technical Assignment",
        "projectName": "El Pais Project",
        "userName": BROWSERSTACK_USERNAME,
        "accessKey": BROWSERSTACK_ACCESS_KEY,
        "debug": "true"
    }

    if device_name:
        bstack_options["deviceName"] = device_name
        bstack_options["realMobile"] = "true"

    if browser_name.lower() == "chrome":
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})
    elif browser_name.lower() == "firefox":
        options = FirefoxOptions()
        options.set_preference("javascript.enabled", False)
    elif browser_name.lower() == "safari":
        options = SafariOptions()
    else:
        options = ChromeOptions()

    options.set_capability('bstack:options', bstack_options)
    options.set_capability('browserName', browser_name)
    if not device_name:
        options.set_capability('browserVersion', 'latest')
    return options

# 5 parallel browser/device combinations
capabilities_list = [
    get_bstack_options("Chrome", "Windows", "11"),
    get_bstack_options("Firefox", "Windows", "10"),
    get_bstack_options("Safari", "OS X", "Sonoma"),
    get_bstack_options("Chrome", "android", "13.0", "Samsung Galaxy S23"),
    get_bstack_options("Safari", "ios", "17", "iPhone 15 Pro")
]

def run_session(options):
    """Runs scraping, translation, and analysis on a single BrowserStack device."""
    driver = None
    bstack_config = options.to_capabilities()
    platform = bstack_config['bstack:options'].get('deviceName') or bstack_config['bstack:options'].get('os')
    print(f"Starting execution on: {platform} - {bstack_config.get('browserName')}")

    try:
        driver = webdriver.Remote(command_executor=URL, options=options)
        driver.get("https://elpais.com/opinion/")

        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            ).click()
        except Exception:
            pass

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.c")))
        article_elements = driver.find_elements(By.CSS_SELECTOR, "article.c")[:5]

        articles_data = []
        os.makedirs("images", exist_ok=True)

        for i, article in enumerate(article_elements):
            # textContent works on mobile Safari where .text returns empty for off-screen elements
            try:
                title = article.find_element(By.CSS_SELECTOR, "h2.c_t").get_attribute("textContent").strip()
            except Exception:
                title = "Title not found"

            try:
                content = article.find_element(By.CSS_SELECTOR, "p.c_d").get_attribute("textContent").strip()
            except Exception:
                content = "Content is empty or requires login"

            if not title:
                title = "Title not found"
            if not content:
                content = "Content is empty or requires login"

            try:
                img_url = article.find_element(By.TAG_NAME, "img").get_attribute("src")
                if img_url:
                    with open(f"images/{platform}_article_{i+1}.jpg", 'wb') as f:
                        f.write(requests.get(img_url).content)
            except Exception:
                pass

            articles_data.append({"title": title, "content": content})

        # Translation
        api_url = "https://google-translate113.p.rapidapi.com/api/v1/translator/text"
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": "google-translate113.p.rapidapi.com",
            "x-rapidapi-key": os.environ.get("RAPIDAPI_KEY")
        }

        translated_titles = []
        for d in articles_data:
            es_title = d["title"]
            en_title = es_title
            if es_title and es_title != "Title not found":
                try:
                    payload = {"from": "es", "to": "en", "text": es_title}
                    response = requests.post(api_url, headers=headers, json=payload)
                    if response.status_code == 200:
                        en_title = response.json().get("trans", es_title)
                except Exception as e:
                    print(f"Translation error: {e}")
            translated_titles.append(en_title)
            d["translated_title"] = en_title

        # Word frequency analysis on translated titles
        all_text = " ".join(translated_titles).lower()
        words = re.findall(r'\b[a-z]+\b', all_text)
        word_counts = Counter(words)
        repeated_words = {w: c for w, c in word_counts.items() if c > 2}

        final_output = {
            "articles": articles_data,
            "analysis": {"repeated_words": repeated_words}
        }

        safe_platform = "".join([c if c.isalnum() else "_" for c in platform])
        with open(f'scraped_articles_{safe_platform}.json', 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=4)

        driver.execute_script('browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Scraping and Translation successful!"}}')
        return {"platform": platform, "browser": bstack_config.get("browserName"), "repeated_words": repeated_words}

    except Exception as e:
        if driver:
            driver.execute_script(f'browserstack_executor: {{"action": "setSessionStatus", "arguments": {{"status":"failed", "reason": "Error occurred!"}} }}')
        print(f"Execution Failed on {platform}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def main():
    print("Starting BrowserStack Parallel Execution...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(run_session, capabilities_list))

    print("\n================ FINAL RESULTS ===================")
    for res in results:
        if res:
            print(f"[{res['platform']} - {res['browser']}]: Repeated words -> {res['repeated_words']}")

if __name__ == "__main__":
    main()
