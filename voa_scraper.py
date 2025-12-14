import requests
from bs4 import BeautifulSoup
from datetime import datetime
import jdatetime

BASE_URL = "https://ir.voanews.com"

def parse_article_page(html, url):
    """
    Parses the article page to extract full text and other details.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Title
    title_tag = soup.find("h1", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else None
    
    # Body
    # VOA articles usually use <div class="wsw"> for content
    content_div = soup.find("div", class_="wsw")
    if not content_div:
         content_div = soup.find("div", id="article-content")
         
    paragraphs = []
    if content_div:
        for p in content_div.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)
    
    full_text = "\n".join(paragraphs)
    
    # Time/Date (Detailed)
    # <time datetime="2025-12-13T18:30:00+03:30">
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
    items = soup.find_all("li", class_="archive-list__item")
    
    articles = []
    for item in items:
        try:
            # Link
            link_tag = item.find("a", class_="img-wrap")
            if not link_tag:
                continue
            
            href = link_tag.get("href")
            full_link = BASE_URL + href if href.startswith("/") else href
            
            # Title
            title_tag = item.find("h4", class_="media-block__title")
            title = title_tag.get_text(strip=True) if title_tag else None
            
            # Date (Persian usually)
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
                "Date": date_text, # Original Persian Date text
                "Description": summary,
                "Image": img_src,
                "Source": "VOA Farsi"
            })
            
        except Exception as e:
            # print(f"Error parsing item: {e}")
            continue
            
    return articles
