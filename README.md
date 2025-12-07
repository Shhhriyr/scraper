# اسکرپر اخبار فارسی

این مخزن شامل یک ابزار جامع برای استخراج داده (Web Scraper) از وب‌سایت‌های خبری مختلف ایران و ویکی‌پدیا است.

## وب‌سایت‌های پشتیبانی شده

1.  **همشهری آنلاین** (`--hamshahri_scraper`)
2.  **کیهان** (`--kayhan_scraper`)
3.  **اطلاعات** (`--ettelaat_scraper`)
4.  **آسیا نیوز** (`--asianews_scraper`)
5.  **ویکی‌پدیای فارسی** (`--wiki_scraper`)

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

فایل `scraper.py` را با پرچم (Flag) مورد نظر اجرا کنید.

### آرگومان‌های عمومی

*   `--workers`: تعداد تردها (Thread) برای پردازش موازی (پیش‌فرض: ۵).
*   `--output`: نام فایل خروجی (مثلاً `my_data.xlsx`).

### ۱. اسکرپر همشهری
استخراج اخبار بر اساس شناسه (ID) صفحه.

```bash
python scraper.py --hamshahri_scraper --start 1000 --count 50
```
*   `--start`: شناسه صفحه شروع.
*   `--count`: تعداد صفحاتی که باید بررسی شوند.

### ۲. اسکرپر کیهان
استخراج اخبار بر اساس شناسه صفحه.

```bash
python scraper.py --kayhan_scraper --start 1 --count 20
```

### ۳. اسکرپر اطلاعات
استخراج آرشیو بر اساس تاریخ.

```bash
python scraper.py --ettelaat_scraper --days 3
```
*   `--days`: تعداد روزهای گذشته برای استخراج (پیش‌فرض: ۱).

### ۴. اسکرپر آسیا نیوز
استخراج لیست آرشیو و دانلود تصاویر.

```bash
python scraper.py --asianews_scraper --count 5
```
*   `--count`: تعداد صفحات لیست آرشیو برای بررسی.
*   تصاویر در پوشه `asianews_data/` ذخیره می‌شوند.

### ۵. اسکرپر ویکی‌پدیا
استخراج صفحات ویکی‌پدیای فارسی شروع از یک لیست خاص.

```bash
python scraper.py --wiki_scraper
```

## استفاده با داکر (Docker)

1.  ساخت ایمیج (Image):
    ```bash
    docker build -t persian-scraper .
    ```

2.  اجرای اسکرپر (اتصال یک Volume برای ذخیره داده‌ها):
    ```bash
    docker run -v $(pwd)/data:/app/data persian-scraper --hamshahri_scraper --start 100 --count 10 --output /app/data/hamshahri.xlsx
    ```
