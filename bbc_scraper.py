from bs4 import BeautifulSoup
import re

def parse_list_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    
    main_content = soup.find("main")
    if not main_content:
        return items

    list_items = main_content.find_all("li")
    
    for item in list_items:
        # Check if it has a headline
        h2_or_h3 = item.find(["h2", "h3"])
        if not h2_or_h3:
            continue
        
        title = h2_or_h3.get_text(strip=True)
        
        # Skip if title is short or looks like nav
        if len(title) < 5:
            continue

        # Link
        a_tag = item.find("a")
        link = "No Link"
        if a_tag and a_tag.get("href"):
            href = a_tag.get("href")
            if href.startswith("http"):
                link = href
            else:
                link = "https://www.bbc.com" + href
        
        # Time
        time_str = "No Time"
        time_tag = item.find("time")
        if time_tag:
            time_str = time_tag.get_text(strip=True)

        items.append({
            "Title": title,
            "Link": link,
            "Time": time_str,
            "Source": "BBC Persian"
        })
        
    return items

def parse_article_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    details = {}
    
    main_content = soup.find("main")
    if not main_content:
        return details
        
    # Full Text
    paragraphs = main_content.find_all("p")
    full_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
    details["Full_Text"] = full_text
    
    # Description (first paragraph)
    if paragraphs:
        details["Description"] = paragraphs[0].get_text(strip=True)
    
    # Image
    img = main_content.find("img")
    if img:
        details["Image"] = img.get("src")
        
    return details
