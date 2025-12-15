import requests
from bs4 import BeautifulSoup

URL = "https://www.iranintl.com/human-rights"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def inspect():
    print(f"Fetching {URL}...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"Error fetching: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    
    articles = soup.find_all("article")
    print(f"Found {len(articles)} articles.")
    
    for i, art in enumerate(articles[:5]):
        print(f"\n--- Article {i+1} ---")
        
        # Title
        title_tag = art.find(["h3", "h4", "h2"])
        if not title_tag:
             a_tag = art.find("a")
             title = a_tag.get_text(strip=True) if a_tag else "No Title"
        else:
            title = title_tag.get_text(strip=True)
            
        print(f"Title: {title}")
        
        # Link
        a_tag = art.find("a")
        link = "No Link"
        if a_tag and a_tag.get("href"):
            href = a_tag.get("href")
            if href.startswith("http"):
                link = href
            else:
                link = "https://www.iranintl.com" + href
        print(f"Link: {link}")
        
        # Summary
        p_tag = art.find("p")
        summary = p_tag.get_text(strip=True) if p_tag else "No Summary"
        print(f"Summary: {summary}")
        
        # Image
        img_tag = art.find("img")
        img = img_tag.get("src") if img_tag else "No Image"
        print(f"Image: {img}")
        
        # Date
        time_tag = art.find("time")
        date_str = time_tag.get_text(strip=True) if time_tag else "No Date"
        if time_tag and time_tag.get("datetime"):
            date_str += f" ({time_tag.get('datetime')})"
        print(f"Date: {date_str}")

if __name__ == "__main__":
    inspect()
