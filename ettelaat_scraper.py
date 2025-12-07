from bs4 import BeautifulSoup
import jdatetime

def parse_archive_page(html_content):
    """
    Parses the Ettelaat archive page.
    Returns: List of dictionaries containing item summary (Link, Title, etc.)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    news_items = soup.select("li.news")
    results = []

    for item in news_items:
        try:
            # Title & Link
            title_element = item.select_one(".desc h3 a")
            if title_element:
                title = title_element.get_text(strip=True)
                link = title_element.get('href', '')
            else:
                title = "No Title"
                link = ""
            
            # Image
            img_element = item.select_one("figure a img")
            img_src = img_element.get('src', '') if img_element else ""
            
            # Description
            desc_element = item.select_one(".desc p")
            description = desc_element.get_text(strip=True) if desc_element else ""
                
            # Time
            time_element = item.select_one(".desc time")
            news_time = time_element.get_text(strip=True) if time_element else ""

            if link:
                 if link.startswith('/'):
                    link = "https://www.ettelaat.com" + link

            results.append({
                'Title': title,
                'Link': link,
                'Image': img_src,
                'Description': description,
                'Time': news_time
            })
        except Exception as e:
            print(f"Error parsing item: {e}")

    return results

def parse_article_page(html_content, url):
    """
    Parses the Ettelaat article page.
    Returns: dictionary with Full_Text and Category (Subject)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract Category
        category = ""
        # Try to find the specific category link with itemprop="articleSection"
        cat_element = soup.select_one("li.breadcrumb-item a[itemprop='articleSection']")
        
        # Fallback: If not found by itemprop, try to grab the second item in breadcrumb (skipping 'Home')
        if not cat_element:
            breadcrumb_links = soup.select("li.breadcrumb-item a")
            if len(breadcrumb_links) >= 2:
                cat_element = breadcrumb_links[1]
        
        if cat_element:
            category = cat_element.get_text(strip=True)

        # Content Extraction
        content_div = soup.select_one("div.body")
        if not content_div:
            content_div = soup.select_one("div.item-text")
        if not content_div:
            content_div = soup.select_one("article")
        
        full_text = ""
        if content_div:
            full_text = content_div.get_text(separator="\n", strip=True)
        
        return {
            "Full_Text": full_text,
            "Subject": category
        }
            
    except Exception as e:
        print(f"Error parsing article {url}: {e}")
        return None