import os
import requests
import re
from bs4 import BeautifulSoup

# دیکشنری تبدیل ماه فارسی به عدد
MONTH_MAPPING = {
    "فروردین": "01", "اردیبهشت": "02", "خرداد": "03",
    "تیر": "04", "مرداد": "05", "شهریور": "06",
    "مهر": "07", "آبان": "08", "آذر": "09",
    "دی": "10", "بهمن": "11", "اسفند": "12"
}

def convert_date_to_folder_name(day, month_name, year):
    # تبدیل اعداد فارسی به انگلیسی اگر وجود داشته باشد
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    translation_table = str.maketrans(persian_digits, english_digits)
    
    day = day.translate(translation_table)
    year = year.translate(translation_table)
    
    # اضافه کردن صفر قبل از روز اگر تک رقمی باشد
    if len(day) == 1:
        day = "0" + day
        
    month_code = MONTH_MAPPING.get(month_name, "00")
    
    return f"{year}{month_code}{day}"

def parse_archive_page(html_content):
    """
    Extracts article links from the archive page.
    Returns: List of dicts {link, date}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = soup.select("article.blog-post")
    results = []
    
    for art in articles:
        try:
            link_el = art.select_one("h2.blog-post-title a")
            if not link_el: continue
            
            link = link_el.get("href")
            
            date_el = art.select_one("span.blog-post-date")
            date_text = date_el.get_text(strip=True).replace(" ", "-") if date_el else ""
            
            results.append({"link": link, "date": date_text})
        except Exception:
            pass
            
    return results

def parse_article_page(html_content, url):
    """
    Extracts data from article page.
    Returns: dict with title, folder_name (date), image_urls
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    try:
        title_el = soup.select_one("h1.post-title.post-full-title")
        raw_title = title_el.get_text(strip=True) if title_el else ""
        title_text = re.sub(r'[<>:"/\\|?*]', '', raw_title).replace(" ", "_")
        
        # Date extraction from title
        folder_name = "untitled"
        date_match = re.search(r'(\d+|[۰-۹]+)[\s_-]+(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)[\s_-]+(\d{4}|[۰-۹]{4})', title_text)
        
        if date_match:
            day, month_name, year = date_match.groups()
            folder_name = convert_date_to_folder_name(day, month_name, year)
        
        # Image extraction
        imgs = []
        selectors = ["article img", ".post-content img", ".entry-content img", ".blog-post-content img", "div.item-body img"]
        
        found_imgs = []
        for sel in selectors:
            found_imgs = soup.select(sel)
            if found_imgs:
                break
        
        img_urls = []
        for img in found_imgs:
            src = img.get("src")
            if src:
                if src.startswith("/"):
                    src = "https://asianews.ir" + src
                img_urls.append(src)
                
        return {
            "title": title_text,
            "folder_name": folder_name,
            "image_urls": img_urls
        }
        
    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return None