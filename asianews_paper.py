import os
import requests
import re
from bs4 import BeautifulSoup
import jdatetime
from datetime import datetime

# دیکشنری تبدیل ماه فارسی به عدد
MONTH_MAPPING = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3,
    "تیر": 4, "مرداد": 5, "شهریور": 6,
    "مهر": 7, "آبان": 8, "آذر": 9,
    "دی": 10, "بهمن": 11, "اسفند": 12
}

def convert_to_gregorian(persian_date_str):
    try:
        # Normalize digits
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"
        translation_table = str.maketrans(persian_digits, english_digits)
        normalized_date = persian_date_str.translate(translation_table)
        
        # Check for YYYY/MM/DD format
        date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', normalized_date)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            
            hour, minute = 0, 0
            time_match = re.search(r'(\d{1,2}):(\d{1,2})', normalized_date)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
            
            g_date = jdatetime.date(year, month, day).togregorian()
            return datetime(g_date.year, g_date.month, g_date.day, hour, minute).strftime("%Y-%m-%d %H:%M:%S")

        # Fallback to text based month
        parts = re.split(r'\s+|[-]', normalized_date) # Split by space or dash
        day, month, year = None, None, None
        
        for i, part in enumerate(parts):
            if part in MONTH_MAPPING:
                month = MONTH_MAPPING[part]
                if i > 0 and parts[i-1].isdigit():
                    day = int(parts[i-1])
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    year = int(parts[i+1])
                break
        
        if day and month and year:
             hour, minute = 0, 0
             time_match = re.search(r'(\d{1,2}):(\d{1,2})', persian_date_str)
             if time_match:
                 hour = int(time_match.group(1))
                 minute = int(time_match.group(2))
                 
             g_date = jdatetime.date(year, month, day).togregorian()
             return datetime(g_date.year, g_date.month, g_date.day, hour, minute).strftime("%Y-%m-%d %H:%M:%S")
            
    except Exception as e:
        # print(f"Date conversion error: {e}")
        pass
    return None

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
        
    month_code = f"{MONTH_MAPPING.get(month_name, 0):02d}"
    
    return f"{year}{month_code}{day}"

def parse_archive_page(html_content):
    """
    Extracts article links from the archive page.
    Returns: List of dicts {link, date}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    # Changed from article.blog-post to .blog-post to be more generic (it is a div now)
    articles = soup.select(".blog-post")
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
    Returns: dict with title, folder_name (date), image_urls, full_text, etc.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    try:
        title_el = soup.select_one("h1.post-title.post-full-title")
        raw_title = title_el.get_text(strip=True) if title_el else ""
        title_text = re.sub(r'[<>:"/\\|?*]', '', raw_title).replace(" ", "_")
        
        # Date extraction
        folder_name = "untitled"
        persian_date = ""
        gregorian_date = None
        
        # Try to find date in page content first
        date_el = soup.select_one("span.blog-post-date, .post-date, .date, time")
        if date_el:
            persian_date = date_el.get_text(strip=True)
            gregorian_date = convert_to_gregorian(persian_date)

        # Fallback to title regex if no date found or needed for folder_name
        date_match = re.search(r'(\d+|[۰-۹]+)[\s_-]+(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)[\s_-]+(\d{4}|[۰-۹]{4})', title_text)
        
        if date_match:
            day, month_name, year = date_match.groups()
            folder_name = convert_date_to_folder_name(day, month_name, year)
            if not persian_date:
                persian_date = f"{day} {month_name} {year}"
                gregorian_date = convert_to_gregorian(persian_date)
        
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
                
        # Full Text Extraction
        full_text = ""
        text_selectors = ["article", ".post-content", ".entry-content", ".blog-post-content", "div.item-body"]
        for sel in text_selectors:
            content_el = soup.select_one(sel)
            if content_el:
                full_text = content_el.get_text(separator="\n", strip=True)
                break
                
        return {
            "title": title_text,
            "folder_name": folder_name,
            "image_urls": img_urls,
            "full_text": full_text,
            "time": persian_date,
            "gregorian_date": gregorian_date
        }
        
    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return None