from bs4 import BeautifulSoup
from datetime import datetime
import jdatetime
import re

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

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
        parts = re.split(r'\s+|[-،,]', normalized_date)
        day, month, year = None, None, None
        
        for i, part in enumerate(parts):
            if part in MONTH_MAPPING:
                month = MONTH_MAPPING[part]
                # Look around for day and year
                # Usually Day Month Year or Year Month Day
                # Scan neighbors
                if i > 0 and parts[i-1].isdigit():
                    day = int(parts[i-1])
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    year = int(parts[i+1])
                # If not found immediately, look further? 
                # For Hamshahri: "پنجشنبه 24 آبان 1403" -> parts: [پنجشنبه, 24, آبان, 1403]
                break
        
        if day and month and year:
             hour, minute = 0, 0
             time_match = re.search(r'(\d{1,2}):(\d{1,2})', normalized_date)
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
    Parses the raw HTML content and extracts data.
    Returns a dictionary of data or None if extraction fails/invalid.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title_tag = soup.find('h1', class_='title')
        if not title_tag:
            # print(f"Page {page_id}: No title found (likely 404 or invalid page)")
            return None

        # Initialize data dictionary with all columns set to None
        data = {col: None for col in COLUMNS}
        
        data['Page'] = page_id
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        breadcrumb = soup.find('ol', class_='breadcrumb')
        if breadcrumb:
            items = breadcrumb.find_all('li', class_='breadcrumb-item')
            if len(items) > 1:
                link = items[1].find('a')
                if link:
                    data['Subject'] = link.get_text(strip=True)
                else:
                    data['Subject'] = items[1].get_text(strip=True)

        if title_tag:
            data['Title'] = title_tag.get_text(strip=True)

        intro_tag = soup.find(class_='introtext')
        if intro_tag:
            data['Description'] = intro_tag.get_text(strip=True)

        body_tag = soup.find(class_='item-body')
        if body_tag:
            data['Full_Text'] = body_tag.get_text(strip=True)

        # Try to find main image
        item_img = soup.find(class_='item-img')
        if item_img:
            img = item_img.find('img')
            if img and img.get('src'):
                data['Image'] = img.get('src')

        date_div = soup.find('div', class_='item-date')
        if date_div:
            date_span = date_div.find('span')
            if date_span:
                date_text = date_span.get_text(strip=True)
                data['Time'] = date_text
                data['Gregorian_Date'] = convert_to_gregorian(date_text)
        
        return data

    except Exception as e:
        print(f"Page {page_id}: Error parsing - {e}")
        return None
