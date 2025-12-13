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
        # Example: "شنبه ۲۲ آذر ۱۴۰۴ ساعت ۱۳:۱۹"
        # Remove day name if present
        parts = persian_date_str.split()
        
        # Look for day, month, year
        day, month, year, time_str = None, None, None, None
        
        for i, part in enumerate(parts):
            if part in MONTH_MAPPING:
                month = MONTH_MAPPING[part]
                if i > 0 and parts[i-1].isdigit():
                    day = int(parts[i-1])
                if i + 1 < len(parts) and parts[i+1].isdigit():
                    year = int(parts[i+1])
                break
        
        # If not found with simple logic, try regex
        if not (day and month and year):
            match = re.search(r'(\d{1,2})\s+([آ-ی]+)\s+(\d{4})', persian_date_str)
            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                year = int(match.group(3))
                month = MONTH_MAPPING.get(month_name)

        if day and month and year:
            # Handle time
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

def parse_html(html_content, page_id, url):
    """
    Parses the raw HTML content for akhbarbank news.
    Extracts text from <div id="doctextarea">.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize data dictionary
        data = {col: None for col in COLUMNS}
        data['Page'] = page_id
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Extract Title
        # User snippet: <h1 id="docDiv3TitrMain">...</h1>
        title_tag = soup.find('h1', id='docDiv3TitrMain')
        if not title_tag:
            title_tag = soup.find('h1') # Fallback
            
        if title_tag:
            data['Title'] = title_tag.get_text(strip=True)

        # 2. Extract Time
        # User snippet: <div id="docDiv3Date">شنبه ۲۲ آذر ۱۴۰۴ ساعت ۱۳:۱۹</div>
        time_div = soup.find('div', id='docDiv3Date')
        if time_div:
            data['Time'] = time_div.get_text(strip=True)
            if data['Time']:
                data['Gregorian_Date'] = convert_to_gregorian(data['Time'])

        # 3. Extract Description
        # User snippet: <div id="docDivLead1"><div id="docDivLead3"><div>...</div></div></div>
        desc_div = soup.find('div', id='docDivLead1')
        if desc_div:
             # Try deeper
             lead3 = desc_div.find('div', id='docDivLead3')
             if lead3:
                 data['Description'] = lead3.get_text(strip=True)
             else:
                 data['Description'] = desc_div.get_text(strip=True)

        # 4. Extract Content from <div id="doctextarea">
        content_div = soup.find('div', id='doctextarea')
        
        if content_div:
            # Full Text
            data['Full_Text'] = content_div.get_text(separator='\n', strip=True)
            
            # Try to find an image
            # Look for an image inside the content or main image
            img_tag = content_div.find('img')
            if not img_tag:
                 # Check for a main article image
                 img_tag = soup.find('img', class_='news_image') # Hypothetical common class, can be adjusted
            
            if img_tag:
                src = img_tag.get('src')
                if src:
                    if src.startswith('/'):
                        src = "https://www.akhbarbank.com" + src
                    data['Image'] = src

            # Return data if Full_Text exists
            if data['Full_Text']:
                # If no title found, maybe use first line of text?
                if not data['Title']:
                     lines = data['Full_Text'].split('\n')
                     if lines:
                         data['Title'] = lines[0][:100] # Use first line as title proxy

                return data
        
        return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
