from bs4 import BeautifulSoup
import urllib.parse

def parse_html(html_content, url):
    """
    Parses the wiki page content.
    Returns:
        - items: List of dictionaries (extracted content from redirects)
        - next_page: URL of the next page (if any)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = "https://fa.wikipedia.org"
        items = []

        # Part 1: Extract content if this is a content page (logic from original fetch_page_content)
        # Note: The original scraper logic was: 
        # 1. Visit list page
        # 2. For each link, visit it and extract content (fetch_page_content)
        # 3. Find next list page
        
        # We need to support two modes or the caller handles the crawling.
        # Since scraper.py handles requests, scraper.py needs to know:
        # "Is this a list page? If so, give me links to visit."
        # "Is this a content page? If so, give me the content."
        
        # But wait, the original script was "crawl the list of all pages, and for each item in the list, fetch its content".
        # That means scraper.py needs to:
        # 1. Fetch List Page
        # 2. Parse List Page -> Get Content Links + Next List Page
        # 3. For each Content Link -> Fetch & Parse Content
        
        # So we need two parse functions or one that returns structure.
        
        body_div = soup.find("div", class_="mw-allpages-body")
        extracted_links = []
        next_link = None
        
        if body_div:
            # It's a list page
            chunks = body_div.find_all(class_="mw-allpages-chunk")
            for chunk in chunks:
                redirect_items = chunk.find_all("li", class_="allpagesredirect")
                for item in redirect_items:
                    link = item.find("a")
                    if link:
                        title = link.get('title', '')
                        href = link.get('href', '')
                        full_link = urllib.parse.urljoin(base_url, href)
                        extracted_links.append({'title': title, 'link': full_link})

            # Find next page link
            nav_div = soup.find("div", class_="mw-allpages-nav")
            if nav_div:
                links = nav_div.find_all("a")
                for link in links:
                    if "صفحهٔ بعد" in link.get_text():
                        next_link = urllib.parse.urljoin(base_url, link.get("href"))
                        break
            
            if not next_link:
                 links = soup.find_all("a")
                 for link in links:
                     if "صفحهٔ بعد" in link.get_text():
                         next_link = urllib.parse.urljoin(base_url, link.get("href"))
                         break

            return {
                'type': 'list',
                'links': extracted_links,
                'next_page': next_link
            }

        else:
            # Maybe it's a content page?
            # Original logic for content extraction:
            content_div = soup.find("div", id="mw-content-text")
            paragraphs = []
            
            if content_div:
                parser_output = content_div.find("div", class_="mw-parser-output")
                if parser_output:
                    paragraphs = parser_output.find_all("p", recursive=False)
                else:
                    paragraphs = content_div.find_all("p")
            
            if not paragraphs:
                paragraphs = soup.find_all("p")
                
            full_text = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            return {
                'type': 'content',
                'full_text': full_text
            }

    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None