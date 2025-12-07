# اسکرپر اخبار فارسی

این مخزن شامل یک ابزار جامع برای استخراج داده (Web Scraper) از وب‌سایت‌های خبری مختلف ایران و ویکی‌پدیا است.

## وب‌سایت‌های پشتیبانی شده

1.  **همشهری آنلاین** (`--site hamshahri`)
2.  **کیهان** (`--site kayhan`)
3.  **اطلاعات** (`--site ettelaat`)
4.  **آسیا نیوز** (`--site asianews`)
5.  **ویکی‌پدیای فارسی** (`--site wiki`)

## پیش‌نیازها

*   Python 3.8+
*   وابستگی‌های پایتون موجود در `requirements.txt`.

## نصب

1.  کلون کردن مخزن:
    ```bash
    git clone https://github.com/Shhhriyr/scraper.git
    cd scraper
    ```

2.  نصب وابستگی‌ها:
    ```bash
    pip install -r requirements.txt
    ```

## نحوه استفاده

فایل `scraper.py` را با پارامتر `--site` اجرا کنید.

### ۱. اسکرپر همشهری
استخراج اخبار بر اساس شناسه (ID) صفحه.

```bash
python scraper.py --site hamshahri --start 1000 --count 50
```
*   `--start`: شناسه صفحه شروع.
*   `--count`: تعداد صفحاتی که باید بررسی شوند.
*   `--output`: نام فایل خروجی (اختیاری).

### ۲. اسکرپر کیهان
استخراج اخبار بر اساس شناسه صفحه.

```bash
python scraper.py --site kayhan --start 1 --count 20
```

### ۳. اسکرپر اطلاعات
استخراج آرشیو بر اساس تاریخ.

```bash
python scraper.py --site ettelaat --count 3
```
*   `--count`: در اینجا به معنی تعداد روزهای گذشته برای بررسی است (مثلاً ۳ روز اخیر).

### ۴. اسکرپر آسیا نیوز
استخراج لیست آرشیو.

```bash
python scraper.py --site asianews --start 1 --count 5
```
*   `--start`: شماره صفحه شروع آرشیو.
*   `--count`: تعداد صفحات آرشیو برای بررسی.

### ۵. اسکرپر ویکی‌پدیا
استخراج صفحات ویکی‌پدیای فارسی شروع از لیست تمام صفحات.

```bash
python scraper.py --site wiki
```

## استفاده با داکر (Docker)

1.  ساخت ایمیج (Image):
    ```bash
    docker build -t persian-scraper .
    ```

2.  اجرای اسکرپر (اتصال یک Volume برای ذخیره داده‌ها):
    ```bash
    docker run -v $(pwd)/data:/app/data persian-scraper --site hamshahri --start 100 --count 10 --output /app/data/hamshahri.xlsx
    ```
