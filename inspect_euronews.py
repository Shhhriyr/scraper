import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://parsi.euronews.com"

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

def inspect_year(year):
    url = f"{BASE_URL}/{year}"
    html = fetch(url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")
    
    # Find all day links in the calendar
    # User provided: <a class="c-archives-link" href="/2010/11/03" ...>
    day_links = []
    for a in soup.find_all("a", class_="c-archives-link"):
        href = a.get("href")
        if href:
            day_links.append(href)
            
    print(f"Found {len(day_links)} active days in {year}.")
    
    if day_links:
        # Inspect the first day found
        first_day_url = BASE_URL + day_links[0]
        inspect_day(first_day_url)
    else:
        print("No days found. Saving HTML to debug...")
        with open("debug_euronews.html", "w", encoding="utf-8") as f:
            f.write(html)

def inspect_day(url):
    html = fetch(url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")
    
    # Find article links
    # Usually in a list. Need to find the structure.
    # Euronews archive day page usually lists articles.
    # Let's look for standard article links.
    print(f"\nInspecting Day: {url}")
    
    article_links = []
    # Common Euronews article link patterns might be inside <article> or specific classes
    # We'll dump some links to analyze or try to find 'h3' > 'a' often used in listings
    
    # Extract expected date parts from url
    # url = https://parsi.euronews.com/2010/11/03
    expected_parts = []
    if BASE_URL in url:
        try:
            path_only = url.replace(BASE_URL, "").strip('/')
            expected_parts = path_only.split('/') # ['2010', '11', '03']
        except:
            pass

    # Let's grab all links and filter for typical article patterns (usually contains /20xx/mm/dd/title)
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and "/20" in href:
             path = href
             if path.startswith("http"):
                 path = path.replace(BASE_URL, "")
                 if path.startswith("http"): continue
                 
             parts = path.strip('/').split('/')
             
             # Check if it is an article (has slug after date)
             # Date parts are 3. If prefix exists, we need to be careful.
             
             match_found = False
             if expected_parts and len(expected_parts) == 3:
                 try:
                     date_idx = -1
                     for i in range(len(parts)-2):
                         if parts[i] == expected_parts[0] and parts[i+1] == expected_parts[1] and parts[i+2] == expected_parts[2]:
                             date_idx = i
                             break
                     
                     if date_idx != -1:
                         # Check if there is something after date
                         if len(parts) > date_idx + 3 and parts[-1] not in ['video', 'program']:
                             match_found = True
                 except:
                     pass
             
             if match_found:
                 full_link = BASE_URL + path if path.startswith('/') else BASE_URL + '/' + path
                 if full_link not in article_links:
                     article_links.append(full_link)
             else:
                 # Debug rejected ones only if they contain the date but failed structure check
                 if expected_parts and "/".join(expected_parts) in path:
                      print(f"Rejected (structure mismatch): {path}")
    
    # Better heuristic: Look for article titles in the archive list
    # Usually <div class="m-object__body"> <h3> <a ...>
    
    print(f"Found {len(article_links)} potential articles.")
    
    return article_links

def inspect_article(url):
    html = fetch(url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")
    print(f"\nInspecting Article: {url}")
    
    # Title
    title = soup.find("h1")
    print(f"Title: {title.get_text(strip=True) if title else 'Not Found'}")
    
    # Time
    # <time class="c-article-date" ...> or similar
    time_tag = soup.find("time")
    print(f"Time: {time_tag.get_text(strip=True) if time_tag else 'Not Found'} (Datetime: {time_tag.get('datetime') if time_tag else 'N/A'})")
    
    # Body
    # Usually <div class="c-article-content"> or ID "js-article-content"
    body = soup.find(class_=lambda x: x and 'article-content' in x)
    if body:
        print(f"Body found. Length: {len(body.get_text(strip=True))}")
        print(f"Sample: {body.get_text(strip=True)[:100]}...")
    else:
        print("Body not found.")

if __name__ == "__main__":
    import sys
    # Test specific day
    if len(sys.argv) > 1:
        day = sys.argv[1]
    else:
        day = "2010/11/03"

    url = f"{BASE_URL}/{day}"
    print(f"Inspecting Day: {url}")
    articles = inspect_day(url)
    print(f"Found {len(articles)} potential articles.")
    for a in articles:
        print(f" - {a}")
    
    if articles:
        print(f"Inspecting first article: {articles[0]}")
        inspect_article(articles[0])
