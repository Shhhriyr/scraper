from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

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

        # Return data only if we found something useful (Title or Text)
        if data['Title'] or data['Full_Text']:
            return data
        
        return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
