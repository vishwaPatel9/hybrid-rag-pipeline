El Pais Opinion Scraper

This is a web scraper that pulls the top 5 articles from the El Pais Opinion section, translates the titles to English, and does a quick word frequency check. 

You can run it locally using headless Chrome or on BrowserStack across 5 different browsers and devices at the same time.

How it works

The script opens the site and auto-clicks the cookie consent popup. To avoid triggering anti-bot protections, it scrapes the titles, text snippets, and cover images directly from the homepage cards rather than clicking into individual articles. It then translates the titles using Google Translate via RapidAPI and counts any English words repeated more than twice. The final output is saved to a JSON file.

Tech stack

It uses Python 3, Selenium, Requests, and python-dotenv. WebDriver Manager handles the ChromeDriver setup automatically.

Setup

Run pip install selenium webdriver-manager requests python-dotenv 
You will need a .env file in the same folder containing your BROWSERSTACK_USERNAME, BROWSERSTACK_ACCESS_KEY, and RAPIDAPI_KEY. Just make sure Chrome is installed on your computer for the local run.

Running the code

For local execution, run python main.py. It runs invisibly in the background and saves the results to scraped_articles_local.json. 

For BrowserStack, run python browserstack_test.py. This uses ThreadPoolExecutor to run 5 sessions in parallel across Windows, macOS, Android, and iOS devices.

Design notes

I disabled JavaScript for Chrome and Firefox to bypass the El Pais paywall. Safari doesn't let you disable JS via Selenium options, so that workaround only applies to the other browsers.

I also used textContent instead of the standard text property when extracting data. Mobile Safari sometimes returns empty strings for elements scrolled out of the visible viewport, and this fixes that issue.

Finally, the local headless Chrome uses stealth settings like a real user-agent to avoid getting flagged as a bot.
