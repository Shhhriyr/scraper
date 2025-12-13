from bs4 import BeautifulSoup
from datetime import datetime
import jdatetime
import re

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

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
        
        # Check for YYYY/MM/DD format (e.g. 1402-11-29 or 1402/11/29)
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
        parts = persian_date_str.split()
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
        pass
    return None

def parse_html(html_content, page_id, url):
    """
    Parses the raw HTML content for Mehr News.
    URL Pattern: https://www.mehrnews.com/news/{page}
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize data dictionary
        data = {col: None for col in COLUMNS}
        data['Link'] = url
        data['Page'] = page_id
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Header Section (item-header)
        header = soup.find(class_='item-header')
        if header:
            # Title
            # Usually h1 with class 'title' or just h1 inside header
            h1 = header.find('h1')
            if h1:
                data['Title'] = h1.get_text(strip=True)
            
            # Date/Time
            # Look for item-date inside header
            date_tag = header.find(class_='item-date')
            if date_tag:
                data['Time'] = date_tag.get_text(strip=True)
                if data['Time']:
                    data['Gregorian_Date'] = convert_to_gregorian(data['Time'])
            
            # Description / Summary
            summary = header.find(class_='item-summary')
            if summary:
                data['Description'] = summary.get_text(strip=True)

        # 2. Body Section (item-body)
        body = soup.find(class_='item-body')
        if body:
            # Full Text
            # Extract text from paragraphs
            text_parts = []
            paragraphs = body.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    text_parts.append(text)
            
            if not text_parts:
                # Fallback: get all text if no p tags
                data['Full_Text'] = body.get_text(separator='\n', strip=True)
            else:
                data['Full_Text'] = "\n".join(text_parts)

            # Image
            # Try to find image in body or item-img
            img_tag = body.find('img')
            if img_tag:
                src = img_tag.get('src')
                if src:
                    data['Image'] = src
        
        # Fallback for Image: sometimes it's in a separate 'item-img' div outside item-body
        if not data['Image']:
            img_div = soup.find(class_='item-img')
            if img_div:
                img = img_div.find('img')
                if img:
                    data['Image'] = img.get('src')

        # Return data if we have at least a Title
        if data['Title']:
            return data
            
        return None

    except Exception as e:
        print(f"Error parsing Mehr page {page_id}: {e}")
        return None
