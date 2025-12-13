from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

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

        # Extract Content from <div id="doctextarea">
        content_div = soup.find('div', id='doctextarea')
        
        if content_div:
            # Extract Title if available (usually in a specific h tag, but looking at previous code it just got text)
            # Let's try to find a title, usually it's in a header class.
            # But based on the previous code, it only extracted text content.
            # We will try to improve it by finding a title if possible.
            # Often news sites have h1 for title.
            title_tag = soup.find('h1')
            if title_tag:
                data['Title'] = title_tag.get_text(strip=True)
            
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
