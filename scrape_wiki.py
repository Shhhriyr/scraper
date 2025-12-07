import json
import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import os

def parse_html(html_content, url):
    """
    Parses the wiki page content.
    Returns:
        - items: List of dictionaries (extracted content from redirects)
        - next_page: URL of the next page (if any)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = "https://fa.wikipedia.org"
        items = []

        # Part 1: Extract content if this is a content page (logic from original fetch_page_content)
        # Note: The original scraper logic was: 
        # 1. Visit list page
        # 2. For each link, visit it and extract content (fetch_page_content)
        # 3. Find next list page
        
        # We need to support two modes or the caller handles the crawling.
        # Since scraper.py handles requests, scraper.py needs to know:
        # "Is this a list page? If so, give me links to visit."
        # "Is this a content page? If so, give me the content."
        
        # But wait, the original script was "crawl the list of all pages, and for each item in the list, fetch its content".
        # That means scraper.py needs to:
        # 1. Fetch List Page
        # 2. Parse List Page -> Get Content Links + Next List Page
        # 3. For each Content Link -> Fetch & Parse Content
        
        # So we need two parse functions or one that returns structure.
        
        body_div = soup.find("div", class_="mw-allpages-body")
        extracted_links = []
        next_link = None
        
        if body_div:
            # It's a list page
            chunks = body_div.find_all(class_="mw-allpages-chunk")
            for chunk in chunks:
                redirect_items = chunk.find_all("li", class_="allpagesredirect")
                for item in redirect_items:
                    link = item.find("a")
                    if link:
                        title = link.get('title', '')
                        href = link.get('href', '')
                        full_link = urllib.parse.urljoin(base_url, href)
                        extracted_links.append({'title': title, 'link': full_link})

            # Find next page link
            nav_div = soup.find("div", class_="mw-allpages-nav")
            if nav_div:
                links = nav_div.find_all("a")
                for link in links:
                    if "صفحهٔ بعد" in link.get_text():
                        next_link = urllib.parse.urljoin(base_url, link.get("href"))
                        break
            
            if not next_link:
                 links = soup.find_all("a")
                 for link in links:
                     if "صفحهٔ بعد" in link.get_text():
                         next_link = urllib.parse.urljoin(base_url, link.get("href"))
                         break

            return {
                'type': 'list',
                'links': extracted_links,
                'next_page': next_link
            }

        else:
            # Maybe it's a content page?
            # Original logic for content extraction:
            content_div = soup.find("div", id="mw-content-text")
            paragraphs = []
            
            if content_div:
                parser_output = content_div.find("div", class_="mw-parser-output")
                if parser_output:
                    paragraphs = parser_output.find_all("p", recursive=False)
                else:
                    paragraphs = content_div.find_all("p")
            
            if not paragraphs:
                paragraphs = soup.find_all("p")
                
            full_text = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            return {
                'type': 'content',
                'full_text': full_text
            }

    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None


def load_state(state_file):
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_state(state_file, current_url, last_title):
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump({"current_url": current_url, "last_title": last_title}, f)

def main():
    # Step 1: Define the starting URL
    start_url = "https://fa.wikipedia.org/w/index.php?title=%D9%88%DB%8C%DA%98%D9%87:%D8%AA%D9%85%D8%A7%D9%85_%D8%B5%D9%81%D8%AD%D9%87%E2%80%8C%D9%87%D8%A7&from=%21"
    base_url = "https://fa.wikipedia.org"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    output_filename = "wiki_data.json"
    state_filename = "scrape_state.json"
    
    current_url = start_url
    last_processed_title = None
    
    # Load state if exists
    state = load_state(state_filename)
    if state:
        current_url = state.get("current_url", start_url)
        last_processed_title = state.get("last_title")
        print(f"Resuming from URL: {current_url}")
        if last_processed_title:
            print(f"Last processed title: {last_processed_title}")
    
    page_count = 0
    
    # Initialize JSON file if not exists or if starting fresh (and file is empty/invalid)
    if not os.path.exists(output_filename) or os.path.getsize(output_filename) == 0:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("[\n")
        first_record = True
    else:
        # File exists, we are appending. 
        # Need to check if we need a comma. Assume yes if not empty and not just "["
        first_record = False 
        # Note: This simple append logic assumes the file was left in a state where we can append.
        # If the file was properly closed with "]", we would need to remove the "]" first.
        # For robustness, let's check the last char.
        try:
            with open(output_filename, 'rb+') as f:
                f.seek(0, os.SEEK_END)
                pos = f.tell()
                if pos > 1:
                    f.seek(pos - 1)
                    last_char = f.read(1)
                    if last_char == b']':
                        # Remove the closing bracket to append more
                        f.seek(pos - 1)
                        f.truncate()
                        # Also check if we need a comma
                        f.seek(pos - 2) # rough check, might need better logic
                        # Ideally we just ensure we write a comma if needed
        except Exception as e:
            print(f"Warning checking output file: {e}")

    # For demonstration, I'll limit the loop to avoid infinite run during development
    # Remove the break condition for full run
    # max_pages = 1 # Reduced to 1 for demo as fetching content takes time
    # max_links_per_page = 5 # Limit links per page for testing speed, remove for production

    skip_mode = True if last_processed_title else False

    while current_url:
        page_count += 1
        print(f"Processing page {page_count}: {current_url}")
        
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            break

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the container
        body_div = soup.find("div", class_="mw-allpages-body")
        
        if body_div:
            # Find chunks
            chunks = body_div.find_all(class_="mw-allpages-chunk")
            links_found_on_page = 0
            
            for chunk in chunks:
                # Find list items with class "allpagesredirect"
                redirect_items = chunk.find_all("li", class_="allpagesredirect")
                for item in redirect_items:
                    link = item.find("a")
                    if link:
                        title = link.get('title', '')
                        
                        # If in skip mode, check if we reached the last processed title
                        if skip_mode:
                            if title == last_processed_title:
                                print(f"Found last processed title '{title}'. Resuming extraction after this.")
                                skip_mode = False
                            continue
                            
                        href = link.get('href', '')
                        full_link = urllib.parse.urljoin(base_url, href)
                        
                        print(f"  Scraping content for: {title}")
                        full_text = fetch_page_content(full_link, headers)
                        
                        # Populate data structure
                        record = {
                            'Title': title,
                            'Link': full_link,
                            'Image': None,          # Placeholder
                            'Description': None,    # Placeholder
                            'Time': None,           # Placeholder
                            'Gregorian_Date': None, # Placeholder
                            'Scraped_Date': datetime.datetime.now().isoformat(),
                            'Page': page_count,
                            'Subject': 'Wikipedia Redirect', 
                            'Full_Text': full_text
                        }
                        
                        # Append to JSON file immediately
                        with open(output_filename, "a", encoding="utf-8") as f:
                            if not first_record:
                                f.write(",\n")
                            json.dump(record, f, ensure_ascii=False, indent=4)
                        
                        first_record = False
                        links_found_on_page += 1
                        
                        # Save state after every successful scrape
                        save_state(state_filename, current_url, title)
                        
                        # Optional: Limit links for testing
                        # if max_links_per_page and links_found_on_page >= max_links_per_page:
                        #     print(f"  Reached limit of {max_links_per_page} links for this page (testing mode).")
                        #     break
                # if max_links_per_page and links_found_on_page >= max_links_per_page:
                #     break
            
            print(f"  Processed {links_found_on_page} links on this page.")
        else:
            print("  Could not find div with class 'mw-allpages-body'")

        # Find next page link
        next_link = None
        nav_div = soup.find("div", class_="mw-allpages-nav")
        if nav_div:
            links = nav_div.find_all("a")
            for link in links:
                if "صفحهٔ بعد" in link.get_text():
                    next_link = link.get("href")
                    break
        
        if not next_link:
             links = soup.find_all("a")
             for link in links:
                 if "صفحهٔ بعد" in link.get_text():
                     next_link = link.get("href")
                     break

        if next_link:
            current_url = urllib.parse.urljoin(base_url, next_link)
            print(f"  Next page found. Continuing...")
            # If we finished the page and found the title (skip_mode is False), we proceed normally.
            # If we finished the page and DID NOT find the title (skip_mode is True), something is wrong 
            # or the title was on a previous page (shouldn't happen with correct state saving).
            # We'll save the new page URL in state but keep last_title (which is weird).
            # Better approach: If we move to next page, we definitely stop skipping because 
            # last_title must have been on the previous page (the one we just processed).
            if skip_mode:
                 print("Warning: Last processed title not found on the expected page. Disabling skip mode for next page.")
                 skip_mode = False
                 
            # Update state to new page, reset last_title so we start from beginning of next page if crashed
            save_state(state_filename, current_url, None)
            
        else:
            print("  No next page link found. Finished.")
            current_url = None
            
        # Check limit
        # if page_count >= max_pages:
        #     print(f"Limit of {max_pages} pages reached for demo.")
        #     break

    # Close JSON array
    with open(output_filename, "a", encoding="utf-8") as f:
        f.write("\n]")
    
    # Clear state file on successful completion
    if os.path.exists(state_filename):
        os.remove(state_filename)
        
    print(f"Done. Saved records to {output_filename}")

if __name__ == "__main__":
    main()