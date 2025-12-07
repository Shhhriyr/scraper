from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

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
                data['Gregorian_Date'] = date_text
                # Attempt to extract time if present (e.g., "Date - Time")
                if '-' in date_text:
                    parts = date_text.split('-')
                    if len(parts) > 1:
                        data['Time'] = parts[-1].strip()
        
        return data

    except Exception as e:
        print(f"Page {page_id}: Error parsing - {e}")
        return None
