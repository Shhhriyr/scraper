import requests
from bs4 import BeautifulSoup
import re

def inspect_bbc(url):
    print(f"Inspecting: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Try to find news items
        # BBC structure often uses <ul> with specific classes or <article> tags
        # Based on common BBC structure, we look for promotional items
        
        # Strategy 1: Look for standard promo list items
        # BBC uses styled components, so classes are random-looking (e.g. bbc-18ybbvj)
        # But usually they are inside a main region.
        
        main_content = soup.find("main")
        if not main_content:
            print("No <main> tag found.")
            return

        items = main_content.find_all("li")
        print(f"Total <li> items found in <main>: {len(items)}")
        
        count = 0
        for item in items:
            # Check if it has a headline
            h2_or_h3 = item.find(["h2", "h3"])
            if not h2_or_h3:
                continue
            
            title = h2_or_h3.get_text(strip=True)
            
            # Skip if title is short or looks like nav
            if len(title) < 5:
                continue

            # Link
            a_tag = item.find("a")
            link = "No Link"
            if a_tag and a_tag.get("href"):
                link = a_tag.get("href")
                if not link.startswith("http"):
                    link = "https://www.bbc.com" + link
            
            # Summary - usually in a p tag, but might be nested
            summary = "No Summary"
            p_tag = item.find("p")
            if p_tag:
                summary = p_tag.get_text(strip=True)
            
            # Time - <time> tag
            time_str = "No Time"
            time_tag = item.find("time")
            if time_tag:
                time_str = time_tag.get_text(strip=True)

            print("-" * 40)
            print(f"Classes: {item.get('class')}")
            print(f"Title: {title}")
            print(f"Link: {link}")
            print(f"Summary: {summary}")
            print(f"Time: {time_str}")
            
            count += 1
            if count >= 10:
                break
        
        # Check pagination
        print("=" * 40)
        print("Pagination Check:")
        nav = soup.find("nav", attrs={"aria-label": re.compile(r"Pagination|صفحه", re.I)})
        if nav:
            print("Pagination nav found.")
            next_page = nav.find("a", attrs={"aria-label": re.compile(r"Next|بعدی", re.I)}) or \
                        nav.find("span", string=re.compile(r"بعدی")) # Sometimes it's a span if active?
            
            # Look for any link with page=2
            page_links = nav.find_all("a", href=re.compile(r"page="))
            for pl in page_links:
                print(f"Page link: {pl.get('href')}")
        else:
            print("No Pagination nav found.")
            # Fallback search for any ?page= link
            page_links = soup.find_all("a", href=re.compile(r"\?page="))
            print(f"Found {len(page_links)} links with ?page=")
            for pl in page_links[:3]:
                 print(f"Page link: {pl.get('href')}")
            
    except Exception as e:
        print(f"Error: {e}")

def inspect_article(url):
    print(f"Inspecting Article: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        main_content = soup.find("main")
        if not main_content:
            print("No <main> found.")
            return

        # Title
        h1 = main_content.find("h1")
        print(f"H1: {h1.get_text(strip=True) if h1 else 'No H1'}")
        
        # Text
        # BBC articles usually use blocks. <p> tags inside blocks.
        paragraphs = main_content.find_all("p")
        print(f"Found {len(paragraphs)} paragraphs.")
        
        full_text = "\n".join([p.get_text(strip=True) for p in paragraphs])
        print("First 200 chars of text:")
        print(full_text[:200])
        
        # Image
        img = main_content.find("img")
        print(f"Image: {img.get('src') if img else 'No Image'}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with Iran topic
    # inspect_bbc("https://www.bbc.com/persian/topics/ckdxnwvwwjnt")
    inspect_article("https://www.bbc.com/persian/articles/c14vr3dklddo")
