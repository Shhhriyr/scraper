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
        # Example: "۱۸:۱۸ - ۱۴۰۲/۱۱/۲۹"
        # Need to handle this format specifically if it differs from Arman/Banki
        
        # Normalize digits
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"
        translation_table = str.maketrans(persian_digits, english_digits)
        normalized_date = persian_date_str.translate(translation_table)
        
        # Check for YYYY/MM/DD format
        date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', normalized_date)
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

        # Fallback to text based month if format is different
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
    Parses the raw HTML content for inn.ir news.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize data dictionary
        data = {col: None for col in COLUMNS}
        data['Page'] = page_id
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Extract Content
        # User specified: <div class="content">...</div>
        content_div = soup.find('div', class_='content')
        if content_div:
            data['Full_Text'] = content_div.get_text(separator='\n', strip=True)
            
            # Try to find description (often the first paragraph or intro)
            # This is optional but good to have
            first_p = content_div.find('p')
            if first_p:
                data['Description'] = first_p.get_text(strip=True)

        # 2. Extract Title and Image
        # Strategy: Find h1 for title, then find image with alt==title or fetchpriority="high"
        
        title_tag = soup.find('h1')
        if title_tag:
            data['Title'] = title_tag.get_text(strip=True)
        
        # User snippet: <img ... alt="شماره ۱۰ پرسپولیس کیست؟" loading="eager" fetchpriority="high">
        # We look for image with fetchpriority="high" or loading="eager" or matching title
        img_tag = soup.find('img', attrs={'fetchpriority': 'high'})
        if not img_tag:
            img_tag = soup.find('img', attrs={'loading': 'eager'})
        
        if not img_tag and data['Title']:
            # Fallback: find image with alt containing title
            img_tag = soup.find('img', alt=data['Title'])
            
        if img_tag:
            src = img_tag.get('src')
            if src:
                # Handle relative URLs if any (though user snippet had absolute)
                if src.startswith('/'):
                    src = "https://inn.ir" + src
                data['Image'] = src
            
            # If title wasn't found in h1, maybe use alt?
            if not data['Title']:
                data['Title'] = img_tag.get('alt')

        # 3. Extract Date/Time
        # Look for <time class="date"> inside <div class="details">
        # User snippet: <div class="details"> ... <time class="date" datetime="...">...</time> ... </div>
        details_div = soup.find('div', class_='details')
        if details_div:
            time_tag = details_div.find('time', class_='date')
            if time_tag:
                data['Time'] = time_tag.get_text(strip=True)
                # If text is empty, try datetime attribute
                if not data['Time']:
                    data['Time'] = time_tag.get('datetime')
        
        # Fallback if details div not found but time tag exists globally
        if not data['Time']:
             time_tag = soup.find('time', class_='date')
             if time_tag:
                 data['Time'] = time_tag.get_text(strip=True)
                 
        if data['Time']:
            data['Gregorian_Date'] = convert_to_gregorian(data['Time'])

        # Return data only if we found something useful (Title or Text)
        if data['Title'] or data['Full_Text']:
            return data
        
        return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
