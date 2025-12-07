import argparse
import requests
import time
import os
import pandas as pd
from datetime import datetime
import json
import urllib.parse
import jdatetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import extraction modules
try:
    import hamshahri_scraper
except ImportError:
    print("Warning: hamshahri_scraper module not found.")

try:
    import kayhan_scraper
except ImportError:
    print("Warning: kayhan_scraper module not found.")

try:
    import ettelaat_scraper
except ImportError:
    print("Warning: ettelaat_scraper module not found.")

try:
    import asianews_paper
except ImportError:
    print("Warning: asianews_paper module not found.")

try:
    import scrape_wiki
except ImportError:
    print("Warning: scrape_wiki module not found.")

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

def fetch_url(url, timeout=10, headers=None):
    try:
        if not headers:
             headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=timeout, headers=headers)
        if response.status_code == 200:
            return response.text, response.status_code
        return None, response.status_code
    except Exception as e:
        # print(f"Request Error: {e}")
        return None, 0

def save_batch(results, output_file):
    if not results:
        return
    
    new_df = pd.DataFrame(results)
    # Ensure columns exist
    for col in COLUMNS:
        if col not in new_df.columns:
            new_df[col] = None
    new_df = new_df[COLUMNS]

    if os.path.exists(output_file):
        try:
            existing_df = pd.read_excel(output_file)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Remove duplicates
            if 'Link' in updated_df.columns:
                 updated_df.drop_duplicates(subset=['Link'], keep='last', inplace=True)
            elif 'Page' in updated_df.columns:
                 updated_df.drop_duplicates(subset=['Page'], keep='last', inplace=True)
            
        except Exception as e:
            print(f"Error reading existing file: {e}")
            updated_df = new_df
    else:
        updated_df = new_df
        
    updated_df.to_excel(output_file, index=False)
    print(f"Saved {len(results)} records to {output_file}.")

def process_hamshahri_page(page_id):
    url = f"https://www.hamshahrionline.ir/news/{page_id}"
    html, status = fetch_url(url)
    if html:
        data = hamshahri_scraper.parse_html(html, page_id, url)
        if data:
            print(f"[Hamshahri] Extracted: {data.get('Title', 'No Title')[:30]}")
            return data
    return None

def run_hamshahri(start, count, output, workers=5):
    print(f"--- Running Hamshahri Scraper (Start: {start}, Count: {count}, Workers: {workers}) ---")
    
    if start == 1 and os.path.exists(output):
        last_id = hamshahri_scraper.get_last_page_id(output)
        if last_id:
            start = last_id + 1
            print(f"Resuming from page {start}...")

    results = []
    end_page = start + count
    page_ids = range(start, end_page)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_page = {executor.submit(process_hamshahri_page, pid): pid for pid in page_ids}
        for future in as_completed(future_to_page):
            data = future.result()
            if data:
                results.append(data)

    if results:
        save_batch(results, output)
    else:
        print("No data extracted in this batch.")

def process_kayhan_page(page_id):
    url = f"https://kayhan.ir/fa/news/{page_id}"
    html, status = fetch_url(url, timeout=15)
    
    if html:
        data = kayhan_scraper.parse_html(html, page_id, url)
        if data and data != "404":
            print(f"[Kayhan] Extracted: {data.get('Title', 'No Title')[:30]}")
            return data
    return None

def run_kayhan(start, count, output, workers=5):
    print(f"--- Running Kayhan Scraper (Start: {start}, Count: {count}, Workers: {workers}) ---")
    
    results = []
    end_page = start + count
    page_ids = range(start, end_page)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_page = {executor.submit(process_kayhan_page, pid): pid for pid in page_ids}
        for future in as_completed(future_to_page):
            data = future.result()
            if data:
                results.append(data)

    if results:
        save_batch(results, output)
    else:
        print("No data extracted.")

def process_ettelaat_day(date_obj):
    day_results = []
    page = 1
    empty_streak = 0
    
    # We process pages sequentially within a day to respect pagination logic
    # But days are processed in parallel
    while empty_streak < 3:
        url = f"https://www.ettelaat.com/archive?pi={page}&ms=0&dy={date_obj.day}&mn={date_obj.month}&yr={date_obj.year}"
        html, status = fetch_url(url)
        
        if not html:
            break
            
        items = ettelaat_scraper.parse_archive_page(html)
        
        if not items:
            empty_streak += 1
            page += 1
            continue
        
        empty_streak = 0
        
        # Fetch article content for items in this page
        # We can also parallelize this inner loop if needed, but let's keep it simple first
        for item in items:
            link = item.get('Link')
            if link:
                art_html, art_status = fetch_url(link)
                if art_html:
                    details = ettelaat_scraper.parse_article_page(art_html, link)
                    if details:
                        item.update(details)
                        item['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        day_results.append(item)
        
        page += 1
    
    if day_results:
        print(f"[Ettelaat] {date_obj}: Extracted {len(day_results)} items.")
    return day_results

def run_ettelaat(days, output, workers=3):
    print(f"--- Running Ettelaat Scraper (Past {days} days, Workers: {workers}) ---")
    
    end_date = jdatetime.date.today()
    start_date = end_date - jdatetime.timedelta(days=days)
    
    dates_to_process = []
    current = start_date
    while current <= end_date:
        dates_to_process.append(current)
        current += jdatetime.timedelta(days=1)
    
    all_results = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_date = {executor.submit(process_ettelaat_day, d): d for d in dates_to_process}
        for future in as_completed(future_to_date):
            res = future.result()
            if res:
                all_results.extend(res)

    if all_results:
        save_batch(all_results, output)
    else:
        print("No data found.")

def process_asianews_archive(page_num, output_dir):
    url = f"https://asianews.ir/fa/archive?page={page_num}"
    html, status = fetch_url(url)
    
    if not html:
        return
        
    articles = asianews_paper.parse_archive_page(html)
    print(f"[AsiaNews] Page {page_num}: Found {len(articles)} articles.")
    
    for art in articles:
        link = art.get('link')
        if not link: continue
        
        art_html, art_status = fetch_url(link)
        
        if art_html:
            data = asianews_paper.parse_article_page(art_html, link)
            if data:
                folder_name = data.get('folder_name', 'untitled')
                save_path = os.path.join(output_dir, folder_name)
                if not os.path.exists(save_path):
                    try:
                        os.makedirs(save_path, exist_ok=True)
                    except:
                        pass
                    
                # Download images
                for idx, img_url in enumerate(data.get('image_urls', []), 1):
                    try:
                        r = requests.get(img_url, stream=True, timeout=10)
                        if r.status_code == 200:
                            fname = os.path.join(save_path, f"{idx}.jpg")
                            with open(fname, "wb") as f:
                                for chunk in r.iter_content(1024):
                                    f.write(chunk)
                    except Exception as e:
                        print(f"Error downloading image: {e}")

def run_asianews(count, output_dir="asianews_data", workers=5):
    print(f"--- Running AsiaNews Scraper (First {count} pages, Workers: {workers}) ---")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pages = range(1, count + 1)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_page = {executor.submit(process_asianews_archive, p, output_dir): p for p in pages}
        for future in as_completed(future_to_page):
            future.result() # We just wait for completion

def run_wiki(start_url, output_file="wiki_data.json", workers=5):
    print(f"--- Running Wiki Scraper ---")
    
    current_url = start_url
    if not current_url:
        current_url = "https://fa.wikipedia.org/w/index.php?title=%D9%88%DB%8C%DA%98%D9%87:%D8%AA%D9%85%D8%A7%D9%85_%D8%B5%D9%81%D8%AD%D9%87%E2%80%8C%D9%87%D8%A7&from=%21"

    max_pages = 5
    page_count = 0
    
    while current_url and page_count < max_pages:
        page_count += 1
        print(f"Processing Wiki List Page {page_count}")
        
        html, status = fetch_url(current_url)
        if not html:
            break
            
        data = scrape_wiki.parse_html(html, current_url)
        
        if data and data.get('type') == 'list':
            links = data.get('links', [])
            print(f"  Found {len(links)} links. Scraping content in parallel...")
            
            results = []
            
            # Parallel fetch content
            def fetch_content(item):
                link = item.get('link')
                item_html, _ = fetch_url(link)
                if item_html:
                    content_data = scrape_wiki.parse_html(item_html, link)
                    if content_data and content_data.get('type') == 'content':
                        return {
                            'Title': item.get('title'),
                            'Link': link,
                            'Full_Text': content_data.get('full_text'),
                            'Scraped_Date': datetime.now().isoformat()
                        }
                return None

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(fetch_content, item) for item in links]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        results.append(res)
            
            # Save results
            with open(output_file, "a", encoding="utf-8") as f:
                for r in results:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
            current_url = data.get('next_page')
            if not current_url:
                print("No next page.")
        else:
            print("Unexpected page type.")
            break

def main():
    parser = argparse.ArgumentParser(description="Unified Web Scraper Runner")
    
    parser.add_argument('--hamshahri_scraper', action='store_true', help='Run Hamshahri Scraper')
    parser.add_argument('--kayhan_scraper', action='store_true', help='Run Kayhan Scraper')
    parser.add_argument('--ettelaat_scraper', action='store_true', help='Run Ettelaat Scraper')
    parser.add_argument('--asianews_scraper', action='store_true', help='Run Asia News Scraper')
    parser.add_argument('--wiki_scraper', action='store_true', help='Run Wiki Scraper')
    
    parser.add_argument('--start', type=int, default=1, help='Start Page ID / Page Count')
    parser.add_argument('--count', type=int, default=10, help='Number of pages/items to scrape')
    parser.add_argument('--days', type=int, default=1, help='Number of past days to scrape (for Ettelaat)')
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads')
    parser.add_argument('--output', type=str, default=None, help='Output file name')

    args = parser.parse_args()

    if args.hamshahri_scraper:
        out_file = args.output if args.output else "hamshahri_news.xlsx"
        run_hamshahri(args.start, args.count, out_file, args.workers)

    elif args.kayhan_scraper:
        out_file = args.output if args.output else "kayhan_news.xlsx"
        run_kayhan(args.start, args.count, out_file, args.workers)

    elif args.ettelaat_scraper:
        out_file = args.output if args.output else "ettelaat_news.xlsx"
        run_ettelaat(args.days, out_file, args.workers)

    elif args.asianews_scraper:
        run_asianews(args.count, workers=args.workers)

    elif args.wiki_scraper:
        out_file = args.output if args.output else "wiki_data.json"
        run_wiki(None, out_file, args.workers)

    else:
        print("Please specify a scraper to run (e.g., --hamshahri_scraper).")

if __name__ == "__main__":
    main()
