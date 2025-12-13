from bs4 import BeautifulSoup
from datetime import datetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text', 'Keywords']

def parse_archive_page(html_content):
    """
    Parses the archive/category page to extract article links.
    Target: class="archive_posts plus_h_post" -> class="plus_post_ftl" -> a[href]
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    # Based on inspection:
    # <article class="archive_posts plus_h_post">
    #   ...
    #   <footer>
    #     <a class="plus_post_ftl" href="...">...</a>
    #   </footer>
    # </article>
    
    posts = soup.find_all(class_="archive_posts")
    
    for post in posts:
        # The 'a' tag itself has the class "plus_post_ftl"
        # We search for 'a' with this class inside the post
        ftl_link = post.find('a', class_="plus_post_ftl")
        
        if ftl_link and ftl_link.get('href'):
            links.append(ftl_link.get('href'))
            
    return links

def parse_article_page(html_content, url):
    """
    Parses the article page to extract details.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {col: None for col in COLUMNS}
        data['Link'] = url
        data['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Title: h1
        h1 = soup.find('h1')
        if h1:
            data['Title'] = h1.get_text(strip=True)
            
        # Image: fetchpriority="high"
        # User example: <img ... fetchpriority="high" ...>
        img_tag = soup.find('img', attrs={'fetchpriority': 'high'})
        
        # Fallback if not found (standard WP post image)
        if not img_tag:
            img_tag = soup.find('img', class_='wp-post-image')
            
        if img_tag:
            data['Image'] = img_tag.get('src')
            
        # Full Text
        # User example: <p style="text-align: justify;">
        # We try to find the main content container first.
        # Common WP classes: 'entry-content', 'post-content', 'td-post-content'
        
        content_div = soup.find(class_='entry-content') or \
                      soup.find(class_='post-content') or \
                      soup.find('article')
        
        text_parts = []
        
        if content_div:
            # Extract paragraphs from the content div
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                text_parts.append(p.get_text(strip=True))
        else:
            # Fallback based on user hint: p style="text-align: justify;"
            # We look for p tags that look like content
            all_ps = soup.find_all('p')
            for p in all_ps:
                # Check style or just length
                style = p.get('style', '').lower()
                text = p.get_text(strip=True)
                if 'text-align: justify' in style or len(text) > 50:
                    text_parts.append(text)
                    
        data['Full_Text'] = "\n".join([t for t in text_parts if t])
        
        # Description (first paragraph)
        if text_parts:
            data['Description'] = text_parts[0][:200] + "..."
            
        if data['Title']:
            return data
        return None

    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return None
