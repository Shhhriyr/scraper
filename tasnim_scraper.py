from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

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
        # Usually in div.time or similar
        time_tag = soup.find('div', class_='time') # Hypothetical common class
        if not time_tag:
            # Sometimes date is in headers
            time_tag = soup.find('span', class_='time')
            
        if time_tag:
            data['Time'] = time_tag.get_text(strip=True)

        # Return data if we have Title or Text
        if data['Title'] or data['Full_Text']:
            return data
            
        return None

    except Exception as e:
        print(f"Error parsing Tasnim page {url}: {e}")
        return None
