from bs4 import BeautifulSoup
from datetime import datetime
import re
import jdatetime

MONTH_MAPPING = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3,
    "تیر": 4, "مرداد": 5, "شهریور": 6,
    "مهر": 7, "آبان": 8, "آذر": 9,
    "دی": 10, "بهمن": 11, "اسفند": 12
}

def convert_to_gregorian(persian_date_str):
    if not persian_date_str:
        return None
    try:
        # Normalize digits
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"
        translation_table = str.maketrans(persian_digits, english_digits)
        normalized_date = persian_date_str.translate(translation_table)
        
        # Regex to find day, month name, year, time
        # Example: 13 Tir 1403 - 08:38
        parts = re.split(r'\s+|[-،,]', normalized_date)
        day, month, year = None, None, None
        
        for i, part in enumerate(parts):
            if part in MONTH_MAPPING:
                month = MONTH_MAPPING[part]
                if i > 0 and parts[i-1].isdigit():
                    day = int(parts[i-1])
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    year = int(parts[i+1])
                elif i + 2 < len(parts) and parts[i+2].isdigit(): # Sometimes there is a dash or space
                     year = int(parts[i+2])
                break
        
        hour, minute = 0, 0
        time_match = re.search(r'(\d{1,2}):(\d{1,2})', normalized_date)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))

        if day and month and year:
            g_date = jdatetime.date(year, month, day).togregorian()
            return datetime(g_date.year, g_date.month, g_date.day, hour, minute).strftime("%Y-%m-%d %H:%M:%S")
            
    except Exception:
        pass
    return None

def parse_html(html, page_id, url=None):
    """
    Parses the HTML content of a Mashregh News page.
    """
    soup = BeautifulSoup(html, "html.parser")

    # عنوان
    title_tag = soup.find("h1", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # خلاصه (summary)
    summary_tag = soup.find("p", class_="summary")
    summary = summary_tag.get_text(strip=True) if summary_tag else ""

    # بدنه مقاله - همه <p> داخل articleBody
    body_div = soup.find("div", itemprop="articleBody")
    paragraphs = []
    if body_div:
        for p in body_div.find_all("p"):
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # فیلتر متن‌های خیلی کوتاه
                paragraphs.append(text)

    full_text = "\n".join(paragraphs)

    # Time extraction
    time_text = None
    gregorian_date = None
    
    # Method 1: Meta tag (Best for Gregorian)
    meta_date = soup.find("meta", property="article:published_time")
    if meta_date:
        gregorian_date = meta_date.get("content")
        
    # Method 2: Visible Persian Date
    # <div class="item-date">تاریخ انتشار: ۱۳ تیر ۱۴۰۳ - ۰۸:۳۸</div>
    date_div = soup.find("div", class_="item-date")
    if date_div:
        # Use get_text to handle nested spans
        time_text = date_div.get_text(strip=True).replace("تاریخ انتشار:", "").strip()
    
    # Fallback for Gregorian if meta tag failed
    if not gregorian_date and time_text:
        gregorian_date = convert_to_gregorian(time_text)
    
    # Return dictionary matching scraper.py columns
    result = {
        "Title": title,
        "Link": url,
        "Description": summary,
        "Full_Text": full_text,
        "Page": page_id,
        "Subject": "Mashregh",
        "Time": time_text,
        "Gregorian_Date": gregorian_date,
        "Scraped_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result
