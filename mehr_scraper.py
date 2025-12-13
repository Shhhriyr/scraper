from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

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
