from bs4 import BeautifulSoup
from datetime import datetime
import jdatetime

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

def convert_persian_to_gregorian(persian_date_str):
    if not persian_date_str:
        return ""
    
    # نگاشت اعداد فارسی به انگلیسی
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    translation_table = str.maketrans(persian_digits, english_digits)
    clean_str = persian_date_str.translate(translation_table)
    
    # نگاشت ماه‌ها
    month_map = {
        'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3,
        'تیر': 4, 'مرداد': 5, 'شهریور': 6,
        'مهر': 7, 'آبان': 8, 'آذر': 9,
        'دی': 10, 'بهمن': 11, 'اسفند': 12
    }
    
    try:
        # نمونه فرمت: 13 مهر 1392 - 10:46
        # جدا کردن ساعت و تاریخ
        parts = clean_str.split('-')
        date_part = parts[0].strip()
        time_part = parts[1].strip() if len(parts) > 1 else "00:00"
        
        # پردازش بخش تاریخ
        date_elements = date_part.split()
        day = int(date_elements[0])
        month_name = date_elements[1]
        year = int(date_elements[2])
        
        month = month_map.get(month_name, 1)
        
        # پردازش بخش زمان
        time_elements = time_part.split(':')
        hour = int(time_elements[0])
        minute = int(time_elements[1])
        
        # تبدیل
        gregorian_date = jdatetime.datetime(year, month, day, hour, minute).togregorian()
        return gregorian_date.strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        # print(f"Error converting date '{persian_date_str}': {e}")
        return ""

def parse_html(html_content, page_id, url):
    """
    Parses the raw HTML content for Kayhan news.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        error_container = soup.find('div', class_='error_container')
        if error_container and "صفحه درخواستی شما موجود نمی باشد" in error_container.get_text():
            return "404" # Special marker for not found logic

        news_time = ""
        date_div = soup.find('div', class_='news_pdate_c')
        if date_div:
            for span in date_div.find_all('span'):
                span.decompose()
            news_time = date_div.get_text(strip=True)
        
        # تبدیل تاریخ
        gregorian_date = convert_persian_to_gregorian(news_time)
        
        category = ""
        cat_div = soup.find('div', class_='news_cat_c')
        if cat_div:
            for span in cat_div.find_all('span'):
                span.decompose()
            category = cat_div.get_text(strip=True)

        title = ""
        title_h1 = soup.find('h1', class_='title')
        if title_h1:
            title = title_h1.get_text(strip=True)
        
        description = ""
        subtitle_div = soup.find('div', class_='subtitle')
        if subtitle_div:
            description = subtitle_div.get_text(strip=True)
        
        full_text = ""
        body_div = soup.find('div', class_='body_news')
        if body_div:
            full_text = body_div.get_text(separator='\n', strip=True)
        
        img_src = ""
        if body_div:
            img_tag = body_div.find('img')
            if img_tag and img_tag.get('src'):
                img_src = img_tag.get('src')
                if img_src.startswith('/'):
                    img_src = "https://kayhan.ir" + img_src
        
        if not img_src:
            rutitr_div = soup.find('div', class_='rutitr')
            img_div = soup.find('div', class_='img_news')
            if img_div:
                img_tag = img_div.find('img')
                if img_tag:
                    img_src = img_tag.get('src')

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if title or full_text:
            row = {
                "Title": title,
                "Link": url,
                "Image": img_src,
                "Description": description,
                "Time": news_time,
                "Gregorian_Date": gregorian_date,
                "Scraped_Date": str(current_date),
                "Page": page_id,
                "Subject": category,
                "Full_Text": full_text
            }
            return row
        else:
            return None

    except Exception as e:
        print(f"Error parsing page {page_id}: {e}")
        return None
