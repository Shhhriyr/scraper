import requests
from bs4 import BeautifulSoup
from datetime import datetime
import jdatetime

BASE_URL = "https://www.iranintl.com"

def parse_article_page(html, url):
    """
    Parses the article page to extract full text and other details.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Title
    title_tag = soup.find(["h1"])
    title = title_tag.get_text(strip=True) if title_tag else None
    
    # Body
    # Content is usually in article tag, paragraphs
    article_body = soup.find("article")
    paragraphs = []
    
    if article_body:
        # Sometimes content is in a specific div inside article
        # We generally look for all p tags in article that are not metadata
        for p in article_body.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)
    
    full_text = "\n".join(paragraphs)
    
    # Date/Time
    time_tag = soup.find("time")
    gregorian_date = None
    time_str = None
    
    if time_tag:
        if time_tag.get("datetime"):
            gregorian_date = time_tag.get("datetime").split("T")[0]
        time_str = time_tag.get_text(strip=True)

    return {
        "Full_Text": full_text,
        "Gregorian_Date": gregorian_date,
        "Time": time_str
    }

def parse_list_page(html):
    """
    Parses the list page to extract article metadata.
    """
    soup = BeautifulSoup(html, "html.parser")
    articles_html = soup.find_all("article")
    
    articles = []
    for art in articles_html:
        try:
            # Title
            title_tag = art.find(["h3", "h4", "h2"])
            if not title_tag:
                 a_tag = art.find("a")
                 title = a_tag.get_text(strip=True) if a_tag else None
            else:
                title = title_tag.get_text(strip=True)
            
            if not title:
                continue

            # Link
            a_tag = art.find("a")
            if not a_tag or not a_tag.get("href"):
                continue
                
            href = a_tag.get("href")
            full_link = href if href.startswith("http") else BASE_URL + href
            
            # Summary
            p_tag = art.find("p")
            summary = p_tag.get_text(strip=True) if p_tag else None
            
            # Image
            img_tag = art.find("img")
            img_src = img_tag.get("src") if img_tag else None
            
            # Date
            time_tag = art.find("time")
            date_text = time_tag.get_text(strip=True) if time_tag else None
            
            articles.append({
                "Title": title,
                "Link": full_link,
                "Date": date_text,
                "Description": summary,
                "Image": img_src,
                "Source": "Iran International"
            })
            
        except Exception as e:
            continue
            
    return articles
