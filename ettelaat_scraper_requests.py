import requests
from bs4 import BeautifulSoup
import pandas as pd
import jdatetime
import os
import concurrent.futures
import glob
import time

# Directory for temporary daily files
DATA_DIR = "data_requests"
OUTPUT_FILE = "all_dataxlsx.xlsx"
PROCESSED_LINKS = set()

# Setup headers to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

def load_processed_links():
    """Load all previously scraped links to avoid duplicates."""
    global PROCESSED_LINKS
    print("Loading processed links...")
    
    # 1. Load from final output file if exists
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_excel(OUTPUT_FILE)
            if 'Link' in df.columns:
                initial_count = len(PROCESSED_LINKS)
                PROCESSED_LINKS.update(df['Link'].dropna().astype(str).tolist())
                print(f"Loaded {len(PROCESSED_LINKS) - initial_count} links from {OUTPUT_FILE}")
        except Exception as e:
            print(f"Error reading {OUTPUT_FILE}: {e}")

    # 2. Load from all daily files
    if os.path.exists(DATA_DIR):
        daily_files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
        for file in daily_files:
            try:
                df = pd.read_excel(file)
                if 'Link' in df.columns:
                    PROCESSED_LINKS.update(df['Link'].dropna().astype(str).tolist())
            except Exception as e:
                print(f"Error reading {file}: {e}")
    
    print(f"Total unique processed links loaded: {len(PROCESSED_LINKS)}")

def save_day_data(day_data, date_obj):
    """Save daily data to a separate Excel file."""
    if not day_data:
        return

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    filename = f"news_{date_obj.year}_{date_obj.month}_{date_obj.day}.xlsx"
    file_path = os.path.join(DATA_DIR, filename)
    
    try:
        df = pd.DataFrame(day_data)
        df.to_excel(file_path, index=False)
        print(f"[{date_obj}] Saved {len(day_data)} records to {filename}")
    except Exception as e:
        print(f"[{date_obj}] Error saving file: {e}")

def combine_all_data():
    """Combine all daily files into one final Excel file."""
    print("Combining all daily data...")
    if not os.path.exists(DATA_DIR):
        print("No data directory found.")
        return

    all_files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
    if not all_files:
        print("No data files found to combine.")
        return

    dfs = []
    for file in all_files:
        try:
            df = pd.read_excel(file)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        if 'Link' in combined_df.columns:
            before_count = len(combined_df)
            combined_df.drop_duplicates(subset=['Link', 'Title'], keep='last', inplace=True)
            after_count = len(combined_df)
            if before_count > after_count:
                print(f"Removed {before_count - after_count} duplicate records.")
        
        combined_df.to_excel(OUTPUT_FILE, index=False)
        print(f"Successfully saved total {len(combined_df)} records to {OUTPUT_FILE}")
    else:
        print("No valid data found in files.")

def get_news_from_page(url, retries=3):
    """Fetch page content using requests."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                # Enforce UTF-8 to avoid Mojibake on list pages too
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                news_items = soup.select("li.news")
                if news_items:
                    return news_items
            elif response.status_code == 404:
                 # Page definitely doesn't exist
                 return []
            
            # If not successful, wait and retry
            time.sleep(1)
        except Exception as e:
            print(f"   Error accessing {url}: {e}")
            time.sleep(1)
            
    return []

def get_article_details(url):
    """Fetch full text content and category from the article page."""
    if not url:
        return "", ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Enforce UTF-8 to fix Mojibake
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract Category
            category = ""
            # Try to find the specific category link with itemprop="articleSection"
            cat_element = soup.select_one("li.breadcrumb-item a[itemprop='articleSection']")
            
            # Fallback: If not found by itemprop, try to grab the second item in breadcrumb (skipping 'Home')
            if not cat_element:
                breadcrumb_links = soup.select("li.breadcrumb-item a")
                if len(breadcrumb_links) >= 2:
                    cat_element = breadcrumb_links[1]
            
            if cat_element:
                category = cat_element.get_text(strip=True)

            # Based on common structure, main content is often in a specific div or article tag
            # Adjust selector based on actual site structure. 
            # Common guess: div.body, div.content, article, etc.
            # Let's try to find the main content area.
            
            # Strategy 1: Look for 'div.body' (common in Iranian news sites)
            content_div = soup.select_one("div.body")
            
            # Strategy 2: Look for 'div.item-text'
            if not content_div:
                content_div = soup.select_one("div.item-text")
                
            # Strategy 3: Look for 'article' tag
            if not content_div:
                content_div = soup.select_one("article")
            
            full_text = ""
            if content_div:
                # Get text and clean it up
                full_text = content_div.get_text(separator="\n", strip=True)
            
            return full_text, category
            
    except Exception as e:
        print(f"Error fetching details from {url}: {e}")
    
    return "", ""

def extract_news_data(news_items, current_date, page):
    """Extract data from BeautifulSoup elements."""
    data_list = []
    for item in news_items:
        try:
            # Title & Link
            title_element = item.select_one(".desc h3 a")
            if title_element:
                title = title_element.get_text(strip=True)
                link = title_element.get('href', '')
            else:
                title = "No Title"
                link = ""
            
            # Image
            img_element = item.select_one("figure a img")
            img_src = img_element.get('src', '') if img_element else ""
            
            # Description
            desc_element = item.select_one(".desc p")
            description = desc_element.get_text(strip=True) if desc_element else ""
                
            # Time
            time_element = item.select_one(".desc time")
            news_time = time_element.get_text(strip=True) if time_element else ""
            
            # Fetch Full Text and Category
            full_text = ""
            category = ""
            if link:
                # Handle relative URLs
                if link.startswith('/'):
                    link = "https://www.ettelaat.com" + link

                # Check if link is already processed
                if link in PROCESSED_LINKS:
                    # print(f"Skipping already processed link: {link}")
                    continue
                    
                # print(f"   Fetching details for: {title[:30]}...")
                full_text, category = get_article_details(link)
                
                # Mark as processed immediately to handle duplicates within the same run
                PROCESSED_LINKS.add(link)

            record = {
                "Title": title,
                "Link": link,
                "Image": img_src,
                "Description": description,
                "Time": news_time,
                "Scraped_Date": str(current_date),
                "Page": page,
                "Subject": category,
                "Full_Text": full_text
            }
            data_list.append(record)
        except Exception as e:
            print(f"Error extracting item: {e}")
            continue
    return data_list

def get_page_signature(news_items):
    """Generate a signature for the page content to detect loops."""
    sig = []
    for item in news_items:
        # fast extraction for signature
        link_el = item.select_one(".desc h3 a")
        if link_el:
            sig.append(link_el.get('href', ''))
    return tuple(sig)

def process_day(date_obj):
    """Process a single day."""
    day_data = []
    print(f"Starting processing for date: {date_obj}")
    
    # Check for existing daily file to avoid losing data if we skip duplicates
    filename = f"news_{date_obj.year}_{date_obj.month}_{date_obj.day}.xlsx"
    file_path = os.path.join(DATA_DIR, filename)
    
    if os.path.exists(file_path):
        try:
            existing_df = pd.read_excel(file_path)
            day_data = existing_df.to_dict('records')
            print(f"[{date_obj}] Loaded {len(day_data)} existing records from {filename}")
        except Exception as e:
            print(f"[{date_obj}] Error loading existing file {filename}: {e}")
    
    try:
        page = 1
        empty_streak = 0
        MAX_EMPTY_STREAK = 3
        
        identical_streak = 0
        MAX_IDENTICAL_STREAK = 5
        last_signature = None
        
        while True:
            url = f"https://www.ettelaat.com/archive?pi={page}&ms=0&dy={date_obj.day}&mn={date_obj.month}&yr={date_obj.year}"
            
            # 1. Check page
            news_items = get_news_from_page(url, retries=3)
            
            if news_items:
                # Check for identical pages loop
                current_signature = get_page_signature(news_items)
                if current_signature and current_signature == last_signature:
                    identical_streak += 1
                    print(f"[{date_obj}] Page {page} is identical to previous ({identical_streak}/{MAX_IDENTICAL_STREAK})")
                    if identical_streak >= MAX_IDENTICAL_STREAK:
                        print(f"[{date_obj}] Detected infinite loop or duplicate pages. Moving to next day.")
                        break
                else:
                    identical_streak = 0
                    last_signature = current_signature

                print(f"[{date_obj}] Found {len(news_items)} items on Page {page}")
                empty_streak = 0
                extracted = extract_news_data(news_items, date_obj, page)
                day_data.extend(extracted)
            else:
                empty_streak += 1
                print(f"[{date_obj}] Page {page} is empty. Streak: {empty_streak}")
                if empty_streak >= MAX_EMPTY_STREAK:
                    break
            
            page += 1
            # Be polite to the server
            time.sleep(0.5)
            
    except Exception as e:
        print(f"[{date_obj}] Critical Error: {e}")
    finally:
        if day_data:
            save_day_data(day_data, date_obj)
            print(f"[{date_obj}] Finished. Saved {len(day_data)} items.")
        else:
            print(f"[{date_obj}] Finished. No items found.")

def scrape_ettelaat_multithreaded_requests():
    # Range of dates
    start_date = jdatetime.date(1402, 1, 1)
    end_date = jdatetime.date.today()
    
    dates_to_process = []
    current = start_date
    while current <= end_date:
        dates_to_process.append(current)
        current += jdatetime.timedelta(days=1)
    
    # Higher concurrency is possible with requests vs selenium
    MAX_WORKERS = 10
    
    # Load previously processed links
    load_processed_links()
    
    print(f"Starting requests-based scraping for {len(dates_to_process)} days with {MAX_WORKERS} workers.")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(process_day, dates_to_process)

    combine_all_data()

if __name__ == "__main__":
    scrape_ettelaat_multithreaded_requests()
