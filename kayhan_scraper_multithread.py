import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from openpyxl import load_workbook
import concurrent.futures
import threading
import queue
from datetime import datetime
import jdatetime
import re

COLUMNS = ['Title', 'Link', 'Image', 'Description', 'Time', 'Gregorian_Date', 'Scraped_Date', 'Page', 'Subject', 'Full_Text']

MAX_WORKERS = 10
BATCH_SIZE = 100

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

def writer_thread_func(file_path, data_queue, stop_event):
    print("Writer Thread started...")
    
    while not stop_event.is_set() or not data_queue.empty():
        try:
            row_data = data_queue.get(timeout=1)
        except queue.Empty:
            continue
            
        if row_data is None:
            break
            
        if not os.path.exists(file_path):
            try:
                df = pd.DataFrame([row_data], columns=COLUMNS)
                df.to_excel(file_path, index=False)
            except Exception as e:
                print(f"Writer Error (Create): {e}")
        else:
            try:
                wb = load_workbook(file_path)
                ws = wb.active
                row_values = [row_data.get(col) for col in COLUMNS]
                ws.append(row_values)
                wb.save(file_path)
                wb.close()
            except Exception as e:
                print(f"Writer Error (Append): {e}")
        
        data_queue.task_done()
    
    print("Writer Thread finished.")

def process_page(page_id):
    url = f"https://kayhan.ir/fa/news/{page_id}"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            return page_id, None, f"Error: Status {response.status_code}"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        error_container = soup.find('div', class_='error_container')
        if error_container and "صفحه درخواستی شما موجود نمی باشد" in error_container.get_text():
            return page_id, None, "Not Found"
            
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
            return page_id, row, "Found"
        else:
            return page_id, None, "Empty Content"

    except Exception as e:
        return page_id, None, f"Exception: {e}"

def scrape_kayhan_news(start_page=1, output_file='kayhan_news_multithread.xlsx'):
    processed_ids = get_existing_ids(output_file)
    print(f"تعداد اخبار موجود در فایل: {len(processed_ids)}")
    
    data_queue = queue.Queue()
    stop_event = threading.Event()
    
    writer = threading.Thread(target=writer_thread_func, args=(output_file, data_queue, stop_event))
    writer.start()
    
    current_batch_start = start_page
    should_stop = False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        while not should_stop:
            pages_to_check = []
            for i in range(BATCH_SIZE):
                p_id = current_batch_start + i
                if p_id not in processed_ids:
                    pages_to_check.append(p_id)
            
            if not pages_to_check:
                current_batch_start += BATCH_SIZE
                print(f"دسته {current_batch_start-BATCH_SIZE} تا {current_batch_start-1} قبلاً کامل دریافت شده. پرش به دسته بعد...")
                continue

            print(f"بررسی دسته: {pages_to_check[0]} تا {pages_to_check[-1]} ({len(pages_to_check)} صفحه جدید)")

            future_to_page = {executor.submit(process_page, pid): pid for pid in pages_to_check}
            
            results_in_batch = 0
            errors_in_batch = 0
            
            for future in concurrent.futures.as_completed(future_to_page):
                page_id = future_to_page[future]
                try:
                    pid, data, status = future.result()
                    
                    if status == "Found":
                        data_queue.put(data)
                        processed_ids.add(pid)
                        print(f"[OK] صفحه {pid}: {data['Title'][:30]}... (تاریخ: {data['Gregorian_Date']})")
                        results_in_batch += 1
                    elif status == "Not Found":
                        errors_in_batch += 1
                    else:
                        print(f"[Skip] صفحه {pid}: {status}")
                        
                except Exception as exc:
                    print(f"Page {page_id} generated an exception: {exc}")
            
            if results_in_batch == 0 and errors_in_batch == len(pages_to_check):
                print("---")
                print(f"تمام {len(pages_to_check)} صفحه در این دسته موجود نبودند. توقف برنامه.")
                should_stop = True
            else:
                current_batch_start += BATCH_SIZE
                
    stop_event.set()
    writer.join()
    print("برنامه با موفقیت پایان یافت.")

if __name__ == "__main__":
    while True:
        print("Starting scraping cycle (Multi-thread)...")
        scrape_kayhan_news(start_page=1)
        print("Cycle finished. Waiting 6 hours before next run...")
        time.sleep(6 * 60 * 60)
