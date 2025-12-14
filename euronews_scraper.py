from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://parsi.euronews.com"

def parse_html(html, page_id, url=None):
    """
    Parses the HTML content of a Euronews article.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Summary (Description)
    # Usually in <div class="c-article-standfirst"> or meta description
    summary = ""
    standfirst = soup.find(class_=lambda x: x and 'article-standfirst' in x)
    if standfirst:
        summary = standfirst.get_text(strip=True)
    
    if not summary:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            summary = meta_desc.get("content")

    # Body
    body_div = soup.find(class_=lambda x: x and 'article-content' in x)
    paragraphs = []
    if body_div:
        for p in body_div.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)
    
    full_text = "\n".join(paragraphs)

    # Time
    time_text = None
    gregorian_date = None
    
    # <time class="c-article-date" datetime="2025-12-14 10:09:03 +01:00">
    time_tag = soup.find("time")
    if time_tag:
        time_text = time_tag.get_text(strip=True)
        gregorian_date = time_tag.get("datetime")
        # Clean up Gregorian date if needed
        # 2025-12-14 10:09:03 +01:00 -> 2025-12-14 10:09:03
        if gregorian_date and '+' in gregorian_date:
             gregorian_date = gregorian_date.split('+')[0].strip()

    # Image
    image_url = None
    img_tag = soup.find("img", class_="c-article-media__img")
    if img_tag:
        image_url = img_tag.get("src")

    result = {
        "Title": title,
        "Link": url,
        "Description": summary,
        "Full_Text": full_text,
        "Page": page_id,
        "Subject": "Euronews",
        "Time": time_text,
        "Gregorian_Date": gregorian_date,
        "Image": image_url,
        "Scraped_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result
