import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://ir.voanews.com"

def fetch(url):
    print(f"Fetching {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None

def inspect_list(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("li", class_="archive-list__item")
    
    print(f"Found {len(items)} items in list.")
    
    articles = []
    for item in items:
        try:
            # Link & Title
            link_tag = item.find("a", class_="img-wrap")
            if not link_tag:
                continue
                
            href = link_tag.get("href")
            full_link = BASE_URL + href if href.startswith("/") else href
            
            title_tag = item.find("h4", class_="media-block__title")
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Date
            date_tag = item.find("span", class_="date")
            date_text = date_tag.get_text(strip=True) if date_tag else None
            
            # Summary
            p_tag = item.find("p", class_="perex")
            summary = p_tag.get_text(strip=True) if p_tag else None
            
            # Image
            img_tag = item.find("img")
            img_src = img_tag.get("src") if img_tag else None
            if img_tag and img_tag.get("data-src"):
                img_src = img_tag.get("data-src")
                
            articles.append({
                "Title": title,
                "Link": full_link,
                "Date": date_text,
                "Summary": summary,
                "Image": img_src
            })
            
        except Exception as e:
            print(f"Error parsing item: {e}")
            continue
            
    return articles

def inspect_article(url):
    html = fetch(url)
    if not html:
        return None
        
    soup = BeautifulSoup(html, "html.parser")
    print(f"\nInspecting Article: {url}")
    
    # Body extraction logic (Standard VOA structure usually)
    # Usually in <div class="wsw"> or <div class="content-floater">
    
    # Try finding the main content div
    content_div = soup.find("div", class_="wsw")
    if not content_div:
         content_div = soup.find("div", id="article-content")
    
    full_text = ""
    if content_div:
        paragraphs = [p.get_text(strip=True) for p in content_div.find_all("p")]
        full_text = "\n".join(paragraphs)
        print(f"Body found. Length: {len(full_text)}")
        print(f"Sample: {full_text[:100]}...")
    else:
        print("Body NOT found (Check structure).")
        
    return full_text

if __name__ == "__main__":
    # Test Main Page
    start_url = "https://ir.voanews.com/iran-news"
    html = fetch(start_url)
    if html:
        articles = inspect_list(html)
        print(f"\nFirst 3 articles found:")
        for a in articles[:3]:
            print(f" - {a['Title']} ({a['Date']})")
            
        if articles:
            # Test Article Extraction on the first one
            inspect_article(articles[0]['Link'])
            
    # Test Pagination URL (Simulating Load More)
    print("\nTesting Pagination (Page 1)...")
    page_url = "https://ir.voanews.com/iran-news?p=1"
    html_page = fetch(page_url)
    if html_page:
        articles_p = inspect_list(html_page)
        print(f"Found {len(articles_p)} items on Page 1.")
