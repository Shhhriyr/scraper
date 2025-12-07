import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from openpyxl import load_workbook
from datetime import datetime
import jdatetime
import re

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

def get_existing_ids(file_path):
    if not os.path.exists(file_path):
        return set()
    try:
        df = pd.read_excel(file_path)
        if 'Page' in df.columns:
            return set(df['Page'].tolist())
        elif 'Page ID' in df.columns:
             return set(df['Page ID'].tolist())
        return set()
    except Exception as e:
        print(f"هشدار: نتوانست فایل موجود را بخواند ({e}). فرض بر این است که فایل خالی است.")
        return set()

def append_to_excel(file_path, data_dict):
    if not os.path.exists(file_path):
        df = pd.DataFrame([data_dict], columns=COLUMNS)
        df.to_excel(file_path, index=False)
    else:
        try:
            wb = load_workbook(file_path)
            ws = wb.active
            row_values = [data_dict.get(col) for col in COLUMNS]
            ws.append(row_values)
            wb.save(file_path)
            wb.close()
        except Exception as e:
            print(f"خطا در ذخیره ردیف در اکسل: {e}")

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

def scrape_kayhan_news(start_page=1, output_file='kayhan_news.xlsx'):
    processed_ids = get_existing_ids(output_file)
    print(f"تعداد اخبار موجود در فایل: {len(processed_ids)}")
    
    current_page = start_page
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 100
    
    print(f"شروع استخراج اطلاعات از صفحه {start_page}...")
    
    while consecutive_errors < MAX_CONSECUTIVE_ERRORS:
        if current_page in processed_ids:
            current_page += 1
            continue

        url = f"https://kayhan.ir/fa/news/{current_page}"
        
        try:
            response = requests.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"خطا در دریافت صفحه {current_page}: Status Code {response.status_code}")
                consecutive_errors += 1
                current_page += 1
                continue
            
            data = parse_html(response.text, current_page, url)
            
            if data == "404":
                 consecutive_errors += 1
                 print(f"صفحه {current_page} موجود نیست. (تعداد خطاهای متوالی: {consecutive_errors})")
            elif data:
                 consecutive_errors = 0
                 append_to_excel(output_file, data)
                 processed_ids.add(current_page)
                 print(f"صفحه {current_page} ذخیره شد: {data['Title'][:30]}... (تاریخ: {data['Gregorian_Date']})")
            else:
                 # Empty content but page loaded
                 print(f"صفحه {current_page} محتوای خبری نداشت.")
                 
        except Exception as e:
            print(f"خطای سیستمی در صفحه {current_page}: {e}")
        
        current_page += 1
    
    print("پایان استخراج.")

if __name__ == "__main__":
    while True:
        print("Starting scraping cycle...")
        scrape_kayhan_news(start_page=1)
        print("Cycle finished. Waiting 6 hours before next run...")
        time.sleep(6 * 60 * 60)
