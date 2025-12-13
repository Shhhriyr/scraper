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
                if i > 0 and parts[i-1].isdigit():
                    day = int(parts[i-1])
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    year = int(parts[i+1])
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
    Parses the raw HTML content for Tasnim News.
    Target URL structure example: https://www.tasnimnews.com/fa/news/1391/08/24/92
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize data dictionary
        data = {col: None for col in COLUMNS}
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Title (Usually h1.title or just h1)
        h1 = soup.find('h1', class_='title')
        if not h1:
            h1 = soup.find('h1')
        
        if h1:
            data['Title'] = h1.get_text(strip=True)

        # 2. Full Text (Usually in div.story or div.news-content)
        content_div = soup.find('div', class_='story')
        if not content_div:
             content_div = soup.find('div', class_='news-content')
        
        if content_div:
            # Extract paragraphs
            paragraphs = content_div.find_all('p')
            text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            
            # If no paragraphs found (sometimes text is directly in div)
            if not text_parts:
                full_text = content_div.get_text(separator='\n', strip=True)
            else:
                full_text = "\n".join(text_parts)
                
            data['Full_Text'] = full_text
            
            # Use first part as description if available
            if text_parts:
                data['Description'] = text_parts[0][:200] + "..."

        # 3. Image
        # Usually in div.news-image img or div.main-photo img
        img_tag = None
        img_div = soup.find('div', class_='news-image') or soup.find('div', class_='main-photo')
        if img_div:
            img_tag = img_div.find('img')
        
        # Fallback: look for image in content
        if not img_tag and content_div:
            img_tag = content_div.find('img')
            
        if img_tag:
            src = img_tag.get('src')
            if src:
                # Tasnim images are usually full URLs, but check for relative
                if src.startswith('/'):
                    src = "https://www.tasnimnews.com" + src
                data['Image'] = src

        # 4. Time
        # Usually in .time class (li, div, or span)
        time_tag = soup.find(class_='time') 
        
        if time_tag:
            # Extract text from the tag itself, but be careful of nested tags
            # Example: <li class="time">10 بهمن 1403 - 10:21<li class="service">...</li></li>
            # We want the direct text or text before child tags.
            
            # Get text node directly?
            # Or just get_text() and clean it?
            # get_text() will include "اخبار اجتماعی" etc.
            # Let's try to get the first text node.
            
            full_text = time_tag.get_text(" ", strip=True)
            # The inspection showed: 10 بهمن 1403 - 10:21 followed by service links.
            # The service links are siblings or children?
            # Inspection: <li class="time">TEXT<li class="service">...</li></li> 
            # This HTML looks malformed (li inside li without ul?). 
            # If so, BeautifulSoup might parse it as nested.
            
            # Let's try to get the text content of the element itself, excluding children.
            text = "".join([t for t in time_tag.contents if isinstance(t, str)]).strip()
            
            if not text:
                # Fallback: Split by common separators if get_text returns too much
                # But inspect output showed: <li class="time">10 بهمن 1403 - 10:21<li class="service">
                # This suggests the second li is NOT inside the first one in valid HTML, but maybe nested in source or soup fixed it?
                # Actually, in the inspection output: <li class="time">...<li class="service">...</li></li>
                # It looks like the service li IS inside the time li.
                text = time_tag.contents[0] if time_tag.contents else ""
                if not isinstance(text, str):
                    text = time_tag.get_text(strip=True)

            data['Time'] = text.strip()
            data['Gregorian_Date'] = convert_to_gregorian(data['Time'])

        # Return data if we have Title or Text
        if data['Title'] or data['Full_Text']:
            return data
            
        return None

    except Exception as e:
        print(f"Error parsing Tasnim page {url}: {e}")
        return None
