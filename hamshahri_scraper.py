import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import argparse
import os
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

def get_last_page_id(file_path):
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            if not df.empty:
                if 'Page' in df.columns:
                    return int(df['Page'].max())
                # Fallback for old column name
                elif 'page_id' in df.columns:
                    return int(df['page_id'].max())
        except Exception as e:
            print(f"Error reading existing file: {e}")
    return None

def parse_html(html_content, page_id, url):
    """
    Parses the raw HTML content and extracts data.
    Returns a dictionary of data or None if extraction fails/invalid.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title_tag = soup.find('h1', class_='title')
        if not title_tag:
            # print(f"Page {page_id}: No title found (likely 404 or invalid page)")
            return None

        # Initialize data dictionary with all columns set to None
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
        
        return data

    except Exception as e:
        print(f"Page {page_id}: Error parsing - {e}")
        return None

def scrape_page(page_id):
    url = f"https://www.hamshahrionline.ir/news/{page_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Page {page_id}: HTTP {response.status_code}")
            return None
            
        data = parse_html(response.text, page_id, url)
        if data:
             print(f"Page {page_id}: Scraped successfully - {str(data['Title'])[:30]}...")
        return data

    except Exception as e:
        print(f"Page {page_id}: Error - {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Scrape Hamshahri Online news.")
    parser.add_argument("--start", type=int, default=1, help="Starting page ID")
    parser.add_argument("--count", type=int, default=50, help="Number of pages to scrape per batch")
    parser.add_argument("--output", type=str, default="hamshahri_news.xlsx", help="Output Excel file")
    parser.add_argument("--no-loop", action="store_true", help="Disable continuous scraping")
    
    args = parser.parse_args()
    loop_mode = not args.no_loop
    
    while True:
        last_id = get_last_page_id(args.output)
        if last_id is not None:
            start_page = last_id + 1
            print(f"Found existing data. Resuming from page {start_page}...")
        else:
            start_page = args.start
            print(f"No existing data found. Starting from {start_page}...")
        
        results = []
        end_page = start_page + args.count
        
        print(f"Scraping {args.count} pages starting from {start_page}...")
        
        for page_id in range(start_page, end_page):
            data = scrape_page(page_id)
            if data:
                results.append(data)
            time.sleep(0.5)
            
        if results:
            new_df = pd.DataFrame(results)
            # Reorder columns to match COLUMNS definition
            new_df = new_df[COLUMNS]
            
            if os.path.exists(args.output):
                try:
                    existing_df = pd.read_excel(args.output)
                    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                    
                    # Drop duplicates based on 'Page' column
                    if 'Page' in updated_df.columns:
                        updated_df.drop_duplicates(subset=['Page'], keep='last', inplace=True)
                    elif 'page_id' in updated_df.columns:
                         # Handle legacy column name if present
                         updated_df.drop_duplicates(subset=['page_id'], keep='last', inplace=True)
                         
                except Exception as e:
                    print(f"Error reading existing Excel file: {e}. Creating new one.")
                    updated_df = new_df
            else:
                updated_df = new_df
                
            updated_df.to_excel(args.output, index=False)
            print(f"Saved {len(results)} new records to {args.output}. Total records: {len(updated_df)}")
        else:
            print("No new data found in this batch.")
            
        if not loop_mode:
            break
            
        print("Batch finished. Waiting 1 hours for the next run...")
        time.sleep(1 * 3600)

if __name__ == "__main__":
    main()
