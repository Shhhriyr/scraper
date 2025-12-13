from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

def parse_html(html_content, page_id, url):
    """
    Parses the raw HTML content for Fararu news.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize data dictionary
        data = {col: None for col in COLUMNS}
        data['Page'] = page_id
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Title (Usually in h1)
        # Fararu usually puts title in <h1 class="title"> or similar
        h1 = soup.find('h1')
        if h1:
            data['Title'] = h1.get_text(strip=True)

        # 2. Body/Full Text
        # User specified: <div id="echo_detail">
        body_div = soup.find('div', id='echo_detail')
        if not body_div:
            # Fallback to previous logic
            body_div = soup.find('div', class_='body')
            if not body_div:
                 body_div = soup.find('div', class_='news-body')
        
        if body_div:
            # Extract paragraphs
            paragraphs = body_div.find_all('p')
            text_content = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # If no paragraphs, try getting direct text
            if not text_content:
                text_content = body_div.get_text(separator='\n', strip=True)
                
            data['Full_Text'] = text_content

        # 3. Subject / Category
        # User snippet: <ul class="breadcrumb_list"> ... <li><a ...>عمومی</a></li>
        breadcrumb = soup.find('ul', class_='breadcrumb_list')
        if breadcrumb:
            # Usually the last li or specific one. User showed "عمومی" in breadcrumb.
            # Let's take the last 'li' text or link text.
            lis = breadcrumb.find_all('li')
            if lis:
                last_li = lis[-1]
                data['Subject'] = last_li.get_text(strip=True).replace('/', '').strip()

        # 4. Description / Lead (Subtitle)
        # Often in <div class="subtitle"> or <div class="lead">
        subtitle_div = soup.find('div', class_='subtitle')
        if not subtitle_div:
            subtitle_div = soup.find('div', class_='lead')
            
        if subtitle_div:
            data['Description'] = subtitle_div.get_text(strip=True)
        elif data['Full_Text']:
             # Fallback: First 200 chars of text
             data['Description'] = data['Full_Text'][:200] + "..."

        # 5. Image
        # User snippet: <div class="primary_files"> <img fetchpriority="high" ...>
        # Priority: div.primary_files img[fetchpriority="high"] -> div.primary_files img -> div.body img
        img_tag = None
        primary_files = soup.find('div', class_='primary_files')
        if primary_files:
            img_tag = primary_files.find('img', attrs={'fetchpriority': 'high'})
            if not img_tag:
                img_tag = primary_files.find('img')
        
        if not img_tag and body_div:
            img_tag = body_div.find('img')
            
        if img_tag:
            src = img_tag.get('src')
            if src:
                if src.startswith('/'):
                    src = "https://fararu.com" + src
                data['Image'] = src

        # 6. Date/Time
        # User snippet: <time datetime="2024-01-14T19:13Z"> ۲۲:۴۳ - ۲۴ دی ۱۴۰۲ </time>
        # We need to extract this text.
        
        # Priority: prefer <time> that has Persian text (usually the second one if multiple)
        time_tags = soup.find_all('time')
        
        target_time_tag = None
        
        # Heuristic: pick the one with Persian characters if possible
        for tag in time_tags:
            text = tag.get_text(strip=True)
            if any("\u0600" <= c <= "\u06FF" for c in text): # Check for Persian/Arabic chars
                target_time_tag = tag
                break
        
        if not target_time_tag and time_tags:
            target_time_tag = time_tags[0]
            
        if target_time_tag:
            data['Time'] = target_time_tag.get_text(strip=True)
            
            # Get Gregorian from datetime attribute
            datetime_attr = target_time_tag.get('datetime')
            if datetime_attr:
                # Format: 2025-12-13T11:03:35+00:00
                # We want: YYYY-MM-DD HH:MM:SS
                try:
                    dt_obj = datetime.fromisoformat(datetime_attr)
                    data['Gregorian_Date'] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Handle older python versions or slightly different format (e.g. 'Z' at end)
                    if datetime_attr.endswith('Z'):
                        datetime_attr = datetime_attr[:-1] + '+00:00'
                    try:
                        dt_obj = datetime.fromisoformat(datetime_attr)
                        data['Gregorian_Date'] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        data['Gregorian_Date'] = datetime_attr # Keep original if parse fails

        # Return data only if we have at least a Title or Text
        if data['Title'] or data['Full_Text']:
            return data
            
        return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
