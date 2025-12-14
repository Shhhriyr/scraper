import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import argparse

def setup_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--start-maximized')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Try to ignore SSL errors
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_twitter_profile(username, count=10, headless=False, output_file=None):
    url = f"https://x.com/{username}"
    print(f"Opening {url}...")
    
    driver = setup_driver(headless)
    
    try:
        driver.get(url)
        
        # Wait for tweets to load
        print("Waiting for tweets to load...")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
        except:
            print("Timeout waiting for tweets. You might need to login manually.")
            # If not headless, give user time to login?
            if not headless:
                print("Please login in the browser window if prompted. Waiting 30 seconds...")
                time.sleep(30)
        
        tweets_data = []
        scrolled_height = 0
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while len(tweets_data) < count:
            # Parse current view
            soup = BeautifulSoup(driver.page_source, "html.parser")
            articles = soup.find_all("article")
            
            new_tweets_found = 0
            for article in articles:
                try:
                    # Tweet Text
                    text_div = article.find("div", {"data-testid": "tweetText"})
                    text = text_div.get_text(strip=True) if text_div else None
                    
                    # Time
                    time_tag = article.find("time")
                    timestamp = time_tag["datetime"] if time_tag else None
                    
                    # Link
                    # Find link to status
                    link_tag = article.find("a", href=lambda x: x and "/status/" in x)
                    link = f"https://x.com{link_tag['href']}" if link_tag else None
                    
                    # Image
                    img_tag = article.find("img", src=lambda x: x and "media" in x)
                    image = img_tag["src"] if img_tag else None

                    if text or link:
                        # Avoid duplicates
                        if not any(d['Link'] == link for d in tweets_data):
                            tweets_data.append({
                                "Title": text[:50] + "..." if text else "No Text", # Use start of text as title
                                "Full_Text": text,
                                "Link": link,
                                "Time": timestamp,
                                "Image": image,
                                "Source": "Twitter"
                            })
                            new_tweets_found += 1
                            print(f"Found tweet: {text[:30] if text else 'No Text'}...")
                except Exception as e:
                    continue
            
            if len(tweets_data) >= count:
                break
                
            # Scroll down
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
            # Check if reached bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height and new_tweets_found == 0:
                print("Reached end of page or no new tweets loading.")
                break
            last_height = new_height
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()
        
    print(f"Scraped {len(tweets_data)} tweets.")
    
    if output_file and tweets_data:
        df = pd.DataFrame(tweets_data)
        df.to_excel(output_file, index=False)
        print(f"Saved to {output_file}")
        
    return tweets_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter Scraper")
    parser.add_argument("--user", type=str, default="ManotoNews", help="Twitter username")
    parser.add_argument("--count", type=int, default=10, help="Number of tweets")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--output", type=str, default="twitter_data.xlsx", help="Output file")
    
    args = parser.parse_args()
    scrape_twitter_profile(args.user, args.count, args.headless, args.output)
