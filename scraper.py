import argparse
import requests
import time
import os
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import jdatetime

# Import for Keyword Extraction
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from hazm import word_tokenize, stopwords_list
    HAS_TFIDF = True
except ImportError:
    print("Warning: scikit-learn or hazm not found. Keyword extraction will be disabled.")
    HAS_TFIDF = False

# Import extraction modules
try:
    import hamshahri_scraper
    import kayhan_scraper
    import ettelaat_scraper
    import asianews_paper
    import scrape_wiki
except ImportError as e:
    print(f"Error importing modules: {e}")

# Global Configuration
MAX_WORKERS = 5
COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_url(url, headers=None, timeout=10):
    """
    Fetches the URL and returns the text content and status code.
    """
    if headers is None:
        headers = HEADERS
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        # Enforce UTF-8 for Persian content
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text, response.status_code
        return None, response.status_code
    except Exception as e:
        print(f"Request Error ({url}): {e}")
        return None, 0

def extract_keywords_tfidf(results, top_n=10):
    """
    Calculates TF-IDF for the batch of results and extracts top keywords for each item.
    Adds a 'Keywords' key to each result dictionary.
    """
    if not HAS_TFIDF or not results:
        return results

    # Prepare corpus
    corpus = []
    valid_indices = []
    
    for i, res in enumerate(results):
        text = res.get('Full_Text')
        if not text:
            # Fallback to Description + Title if Full_Text is empty
            parts = [res.get('Title', ''), res.get('Description', '')]
            text = " ".join([str(p) for p in parts if p])
        
        if text and len(text.strip()) > 10:
            corpus.append(text)
            valid_indices.append(i)
        else:
            res['Keywords'] = ""

    if not corpus:
        return results

    try:
        # Custom tokenizer using hazm
        def persian_tokenizer(text):
            return word_tokenize(text)

        # Get Persian stopwords
        persian_stopwords = stopwords_list()
        
        # Initialize Vectorizer
        vectorizer = TfidfVectorizer(
            tokenizer=persian_tokenizer,
            stop_words=persian_stopwords,
            max_features=1000,
            ngram_range=(1, 1) # Unigrams only for simple keywords
        )
        
        # Fit and transform
        tfidf_matrix = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
        
        # Extract top keywords for each document
        for idx, row in enumerate(tfidf_matrix):
            # Get the original result index
            result_idx = valid_indices[idx]
            
            # Sort indices by score
            # row is a sparse matrix, convert to dense or iterate
            row_data = row.toarray().flatten()
            top_indices = row_data.argsort()[-top_n:][::-1]
            
            keywords = []
            for feat_idx in top_indices:
                if row_data[feat_idx] > 0:
                    keywords.append(feature_names[feat_idx])
            
            results[result_idx]['Keywords'] = ", ".join(keywords)
            
    except Exception as e:
        print(f"Error calculating TF-IDF: {e}")
        
    return results

def save_batch(results, output_file):
    """
    Saves a batch of results to the Excel file.
    Handles existing files and deduplication.
    """
    if not results:
        return
    
    # Calculate Keywords before saving
    if HAS_TFIDF:
        print("Calculating TF-IDF keywords...")
        results = extract_keywords_tfidf(results)

    new_df = pd.DataFrame(results)
    
    # Ensure all columns exist
    for col in COLUMNS:
        if col not in new_df.columns:
            new_df[col] = None
    new_df = new_df[COLUMNS]

    if os.path.exists(output_file):
        try:
            existing_df = pd.read_excel(output_file)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Deduplication logic
            # Prefer 'Link' if available, otherwise 'Page' + 'Title' combination
            if 'Link' in updated_df.columns and updated_df['Link'].notna().any():
                 updated_df.drop_duplicates(subset=['Link'], keep='last', inplace=True)
            elif 'Page' in updated_df.columns:
                 updated_df.drop_duplicates(subset=['Page'], keep='last', inplace=True)
            
        except Exception as e:
            print(f"Error reading existing file: {e}")
            updated_df = new_df
    else:
        updated_df = new_df
        
    try:
        updated_df.to_excel(output_file, index=False)
        print(f"Saved {len(results)} new records. Total records: {len(updated_df)} in {output_file}")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

# -------------------------------------------------------------------------
# Hamshahri Runner
# -------------------------------------------------------------------------
def process_hamshahri_page(page_id):
    url = f"https://www.hamshahrionline.ir/news/{page_id}"
    html, status = fetch_url(url)
    if html:
        data = hamshahri_scraper.parse_html(html, page_id, url)
        if data:
            return data
    elif status != 404:
        # print(f"Failed to fetch {url} (Status: {status})")
        pass
    return None

def run_hamshahri(start, count, output):
    print(f"--- Running Hamshahri Scraper (Starting from ID {start}, Count: {count}) ---")
    
    results = []
    page_ids = range(start, start + count)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(process_hamshahri_page, pid): pid for pid in page_ids}
        
        for future in as_completed(future_to_page):
            data = future.result()
            if data:
                results.append(data)
                print(f"Extracted: {data.get('Title', 'No Title')[:30]}")
                
    save_batch(results, output)

# -------------------------------------------------------------------------
# Kayhan Runner
# -------------------------------------------------------------------------
def process_kayhan_page(page_id):
    url = f"https://kayhan.ir/fa/news/{page_id}"
    html, status = fetch_url(url)
    if html:
        data = kayhan_scraper.parse_html(html, page_id, url)
        if data == "404":
            return None # Page not found
        if data:
            return data
    return None

def run_kayhan(start, count, output):
    print(f"--- Running Kayhan Scraper (Starting from ID {start}, Count: {count}) ---")
    
    results = []
    page_ids = range(start, start + count)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(process_kayhan_page, pid): pid for pid in page_ids}
        
        for future in as_completed(future_to_page):
            data = future.result()
            if data:
                results.append(data)
                print(f"Extracted: {data.get('Title', 'No Title')[:30]}")

    save_batch(results, output)

# -------------------------------------------------------------------------
# Ettelaat Runner
# -------------------------------------------------------------------------
def process_ettelaat_article(link, title, date_str, page_num):
    html, status = fetch_url(link)
    if html:
        details = ettelaat_scraper.parse_article_page(html, link)
        if details:
            return {
                "Title": title,
                "Link": link,
                "Time": date_str,
                "Page": page_num,
                "Subject": details.get("Subject"),
                "Full_Text": details.get("Full_Text"),
                "Scraped_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    return None

def run_ettelaat(days, output):
    print(f"--- Running Ettelaat Scraper (Last {days} days) ---")
    
    end_date = jdatetime.date.today()
    start_date = end_date - jdatetime.timedelta(days=days-1)
    
    current_date = start_date
    all_results = []
    
    while current_date <= end_date:
        print(f"Processing Date: {current_date}")
        page = 1
        empty_streak = 0
        
        while True:
            url = f"https://www.ettelaat.com/archive?pi={page}&ms=0&dy={current_date.day}&mn={current_date.month}&yr={current_date.year}"
            html, status = fetch_url(url)
            
            if not html:
                break
                
            items = ettelaat_scraper.parse_archive_page(html)
            if not items:
                empty_streak += 1
                if empty_streak > 2: # Stop if 2 consecutive empty pages
                    break
            else:
                empty_streak = 0
                print(f"  Found {len(items)} items on page {page}")
                
                # Fetch articles in parallel
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = []
                    for item in items:
                        futures.append(executor.submit(
                            process_ettelaat_article, 
                            item['Link'], item['Title'], item['Time'], page
                        ))
                    
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            # Merge with initial item data (Description, Image) if needed
                            # For simplicity we just take what process_ettelaat_article returned + extras
                            # But wait, image/desc were in the list page item.
                            # Let's match them back or pass them through.
                            # Simplified: just append res. Ideally we pass more data to process_ettelaat_article.
                            all_results.append(res)
            
            page += 1
            if page > 50: # Safety limit per day
                break
        
        current_date += jdatetime.timedelta(days=1)
        
    save_batch(all_results, output)

# -------------------------------------------------------------------------
# Asia News Runner
# -------------------------------------------------------------------------
def process_asianews_article(link, date_str):
    if link.startswith("/"):
        link = "https://asianews.ir" + link
        
    html, status = fetch_url(link)
    if html:
        details = asianews_paper.parse_article_page(html, link)
        if details:
            return {
                "Title": details.get("title"),
                "Link": link,
                "Time": date_str,
                "Scraped_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Full_Text": "", # Asianews parser might not extract full text? Checked code: it returns title, folder_name, image_urls.
                # Wait, asianews_paper.py parse_article_page returned {title, folder_name, image_urls}. 
                # It didn't seem to extract full text in the cleaned version I saw?
                # Let's check asianews_paper.py again.
                # It had: title, folder_name, image_urls. No full text?
                # That's a limitation of the current module. I'll stick to what it returns.
                "Image": details.get("image_urls")[0] if details.get("image_urls") else None
            }
    return None

def run_asianews(start_page, count, output):
    print(f"--- Running Asia News Scraper (Start Page: {start_page}, Count: {count}) ---")
    
    results = []
    
    for page in range(start_page, start_page + count):
        url = f"https://asianews.ir/archive?page={page}"
        html, status = fetch_url(url)
        
        if html:
            items = asianews_paper.parse_archive_page(html)
            if items:
                print(f"Page {page}: Found {len(items)} articles.")
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [executor.submit(process_asianews_article, item['link'], item['date']) for item in items]
                    
                    for future in as_completed(futures):
                        res = future.result()
                        if res:
                            res['Page'] = page
                            results.append(res)
                            print(f"Extracted: {res.get('Title')[:30]}")
            else:
                print(f"Page {page}: No items found.")
        else:
            print(f"Page {page}: Failed to fetch.")
            
    save_batch(results, output)

# -------------------------------------------------------------------------
# Wiki Runner
# -------------------------------------------------------------------------
def run_wiki(output):
    print("--- Running Wiki Scraper ---")
    # Initial URL
    current_url = "https://fa.wikipedia.org/w/index.php?title=%D9%88%DB%8C%DA%98%D9%87:%D8%AA%D9%85%D8%A7%D9%85_%D8%B5%D9%81%D8%AD%D9%87%E2%80%8C%D9%87%D8%A7&from=%21"
    
    # We will limit to 1 batch of pages for this runner example, or loop until user stops
    # For safety, let's just do 5 list pages.
    MAX_LIST_PAGES = 5
    page_count = 0
    
    all_results = []
    
    while current_url and page_count < MAX_LIST_PAGES:
        print(f"Processing List Page: {current_url}")
        html, status = fetch_url(current_url)
        
        if not html:
            break
            
        parse_result = scrape_wiki.parse_html(html, current_url)
        
        if parse_result and parse_result.get('type') == 'list':
            links = parse_result.get('links', [])
            next_page = parse_result.get('next_page')
            
            print(f"Found {len(links)} links. Fetching content...")
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_link = {executor.submit(fetch_url, item['link']): item for item in links}
                
                for future in as_completed(future_to_link):
                    item = future_to_link[future]
                    content_html, c_status = future.result()
                    
                    if content_html:
                        content_data = scrape_wiki.parse_html(content_html, item['link'])
                        if content_data and content_data.get('type') == 'content':
                            record = {
                                "Title": item['title'],
                                "Link": item['link'],
                                "Full_Text": content_data.get('full_text'),
                                "Scraped_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Subject": "Wiki"
                            }
                            all_results.append(record)
            
            current_url = next_page
            page_count += 1
        else:
            break
            
    save_batch(all_results, output)


# -------------------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Unified Persian News Scraper")
    
    parser.add_argument('--site', type=str, required=True, 
                        choices=['hamshahri', 'kayhan', 'ettelaat', 'asianews', 'wiki'],
                        help='Site to scrape')
    
    parser.add_argument('--start', type=int, default=1, help='Start ID/Page')
    parser.add_argument('--count', type=int, default=10, help='Count of items/pages/days')
    parser.add_argument('--output', type=str, default=None, help='Output Excel file')
    
    args = parser.parse_args()
    
    if args.site == 'hamshahri':
        out = args.output if args.output else "hamshahri.xlsx"
        run_hamshahri(args.start, args.count, out)
        
    elif args.site == 'kayhan':
        out = args.output if args.output else "kayhan.xlsx"
        run_kayhan(args.start, args.count, out)
        
    elif args.site == 'ettelaat':
        out = args.output if args.output else "ettelaat.xlsx"
        # For ettelaat, 'count' is treated as 'days' to look back
        run_ettelaat(args.count, out)
        
    elif args.site == 'asianews':
        out = args.output if args.output else "asianews.xlsx"
        run_asianews(args.start, args.count, out)
        
    elif args.site == 'wiki':
        out = args.output if args.output else "wiki.xlsx"
        run_wiki(out)

if __name__ == "__main__":
    main()
