import cloudscraper

scraper = cloudscraper.create_scraper()
try:
    response = scraper.get("https://x.com/ManotoNews")
    print(f"Status Code: {response.status_code}")
    print(f"Content Sample: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
