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
        time_tag = soup.find('time')
        if time_tag:
            # Prefer text inside time tag as per user snippet example which has Persian date
            data['Time'] = time_tag.get_text(strip=True)
            
            # Also try to set Gregorian Date from datetime attribute if available
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                data['Gregorian_Date'] = datetime_attr

        # Return data only if we have at least a Title or Text
        if data['Title'] or data['Full_Text']:
            return data
            
        return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
