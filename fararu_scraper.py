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
        # Fararu content is often in <div class="body"> or <div class="news-body">
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

        # 3. Description / Lead (Subtitle)
        # Often in <div class="subtitle"> or <div class="lead">
        subtitle_div = soup.find('div', class_='subtitle')
        if not subtitle_div:
            subtitle_div = soup.find('div', class_='lead')
            
        if subtitle_div:
            data['Description'] = subtitle_div.get_text(strip=True)
        elif data['Full_Text']:
             # Fallback: First 200 chars of text
             data['Description'] = data['Full_Text'][:200] + "..."

        # 4. Image
        # Usually main image is in <div class="main_photo"> img or similar
        # Or look for the first image in body
        img_tag = None
        main_photo_div = soup.find('div', class_='main_photo')
        if main_photo_div:
            img_tag = main_photo_div.find('img')
        
        if not img_tag and body_div:
            img_tag = body_div.find('img')
            
        if img_tag:
            src = img_tag.get('src')
            if src:
                if src.startswith('/'):
                    src = "https://fararu.com" + src
                data['Image'] = src

        # 5. Date/Time
        # Usually in <div class="publish_time"> or header date
        time_span = soup.find('span', class_='publish_time') # hypothetical
        if not time_span:
             # Check header date
             pass 
             # (We can improve this if we inspect specific Fararu structure, 
             # but for now we leave it empty or scrape what's easy)

        # Return data only if we have at least a Title or Text
        if data['Title'] or data['Full_Text']:
            return data
            
        return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
