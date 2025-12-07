import requests
from bs4 import BeautifulSoup
import time
import argparse
import pandas as pd
import concurrent.futures
import threading
import os
from datetime import datetime

print_lock = threading.Lock()

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

def get_last_page_id(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            if not df.empty:
                if 'Page' in df.columns:
                    return int(df['Page'].max())
                # Fallback for old column name
                elif 'Page ID' in df.columns:
                    return int(df['Page ID'].max())
                elif 'page_id' in df.columns:
                    return int(df['page_id'].max())
        except Exception as e:
            with print_lock:
                print(f"Error reading existing file: {e}")
    return None

def scrape_page(page_id):
    base_url = "https://www.hamshahrionline.ir/news/"
    url = f"{base_url}{page_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h1', class_='title')
        if not title_tag:
            return None

        # Initialize data dictionary
        data = {col: None for col in COLUMNS}
        
        data['Page'] = page_id
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        breadcrumb = soup.find('ol', class_='breadcrumb')
        if breadcrumb:
            items = breadcrumb.find_all('li', class_='breadcrumb-item')
            if len(items) > 1:
                link = items[1].find('a')
                if link:
                    data['Subject'] = link.get_text(strip=True)
                else:
                    data['Subject'] = items[1].get_text(strip=True)
        
        if title_tag:
            data['Title'] = title_tag.get_text(strip=True)
            
        intro_tag = soup.find(class_='introtext')
        if intro_tag:
            data['Description'] = intro_tag.get_text(strip=True)
            
        body_tag = soup.find(class_='item-body')
        if body_tag:
            data['Full_Text'] = body_tag.get_text(strip=True)

        # Try to find main image
        item_img = soup.find(class_='item-img')
        if item_img:
            img = item_img.find('img')
            if img and img.get('src'):
                data['Image'] = img.get('src')
            
        date_div = soup.find('div', class_='item-date')
        if date_div:
            date_span = date_div.find('span')
            if date_span:
                date_text = date_span.get_text(strip=True)
                data['Gregorian_Date'] = date_text
                # Attempt to extract time if present (e.g., "Date - Time")
                if '-' in date_text:
                    parts = date_text.split('-')
                    if len(parts) > 1:
                        data['Time'] = parts[-1].strip()
                
        with print_lock:
             print(f"Scraped page {page_id}: {str(data['Title'])[:30]}...")
             
        return data
        
    except Exception as e:
        with print_lock:
            print(f"Error scraping page {page_id}: {e}")
        return None

def scrape_hamshahri_multithread(start_page_arg, count, output_file, max_workers=5, loop_mode=True):
    
    while True:
        last_id = get_last_page_id(output_file)
        if last_id is not None:
            start_page = last_id + 1
            print(f"Found existing data. Resuming from page {start_page}...")
        else:
            start_page = start_page_arg
            print(f"No existing data found. Starting from {start_page}...")

        data = []
        end_page = start_page + count
        page_ids = range(start_page, end_page)
        
        print(f"Starting multithreaded scrape from {start_page} to {end_page - 1} with {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {executor.submit(scrape_page, page_id): page_id for page_id in page_ids}
            
            for future in concurrent.futures.as_completed(future_to_page):
                page_id = future_to_page[future]
                try:
                    result = future.result()
                    if result:
                        data.append(result)
                except Exception as exc:
                    with print_lock:
                        print(f"Page {page_id} generated an exception: {exc}")
                    
        if data:
            data.sort(key=lambda x: x["Page"])
            new_df = pd.DataFrame(data)
            new_df = new_df[COLUMNS]
            
            if os.path.exists(output_file):
                try:
                    existing_df = pd.read_excel(output_file)
                    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                    
                    # Drop duplicates based on 'Page' column
                    if 'Page' in updated_df.columns:
                        updated_df.drop_duplicates(subset=['Page'], keep='last', inplace=True)
                    elif 'Page ID' in updated_df.columns:
                         updated_df.drop_duplicates(subset=['Page ID'], keep='last', inplace=True)
                    elif 'page_id' in updated_df.columns:
                         updated_df.drop_duplicates(subset=['page_id'], keep='last', inplace=True)
                         
                except Exception as e:
                    print(f"Error reading existing Excel file: {e}. Creating new one.")
                    updated_df = new_df
            else:
                updated_df = new_df

            updated_df.to_excel(output_file, index=False)
            print(f"\nSaved {len(data)} new records to {output_file}. Total records: {len(updated_df)}")
        else:
            print("\nNo new data found in this batch.")

        if not loop_mode:
            break
        
        print("Batch finished. Waiting 6 hours for the next run...")
        time.sleep(6 * 3600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multithreaded Scrape Hamshahri Online news.")
    parser.add_argument("--start", type=int, default=934000, help="Starting page ID")
    parser.add_argument("--count", type=int, default=50, help="Number of pages to scrape per batch")
    parser.add_argument("--output", type=str, default="hamshahri_news_mt.xlsx", help="Output Excel file")
    parser.add_argument("--workers", type=int, default=10, help="Number of threads")
    parser.add_argument("--no-loop", action="store_true", help="Disable continuous scraping")
    
    args = parser.parse_args()
    
    # If --no-loop is passed, loop_mode becomes False
    scrape_hamshahri_multithread(args.start, args.count, args.output, args.workers, not args.no_loop)
