# اسکرپر اخبار فارسی

این مخزن شامل یک ابزار جامع برای استخراج داده (Web Scraper) از وب‌سایت‌های خبری مختلف ایران و ویکی‌پدیا است.

## ویژگی‌ها

*   **استخراج چندنخی (Multi-threading):** افزایش سرعت استخراج با پردازش موازی.
*   **استخراج کلمات کلیدی (Keyword Extraction):** استفاده از الگوریتم **TF-IDF** و کتابخانه **Hazm** برای استخراج خودکار ۱۰ کلمه کلیدی مهم از متن هر خبر.
*   **خروجی اکسل:** ذخیره داده‌ها در فایل اکسل با ستون‌های منظم.
*   **پشتیبانی از داکر:** قابلیت اجرا در محیط ایزوله کانتینر.

## وب‌سایت‌های پشتیبانی شده

1.  **همشهری آنلاین** (`--site hamshahri`)
2.  **کیهان** (`--site kayhan`)
3.  **اطلاعات** (`--site ettelaat`)
4.  **آسیا نیوز** (`--site asianews`)
5.  **ویکی‌پدیای فارسی** (`--site wiki`)
6.  **ایران آنلاین** (`--site inn`)
7.  **آرمان امروز** (`--site armandaily`)
8.  **اخبار بانک** (`--site banki`)
9.  **فرارو** (`--site fararu`)
10. **تسنیم** (`--site tasnim`)
11. **مهر** (`--site mehr`)

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

### ۶. اسکرپر ایران آنلاین (inn.ir)
استخراج اخبار بر اساس شناسه (ID) صفحه.
این اسکرپر تصویر خبر را از تگ `img` با ویژگی `fetchpriority="high"` و متن خبر را از تگ `div` با کلاس `content` استخراج می‌کند.

```bash
python scraper.py --site inn --start 43712 --count 10
```

### ۷. اسکرپر آرمان امروز (armandaily)
استخراج اخبار از لیست صفحات دسته‌بندی.
این اسکرپر از صفحه لیست (Pagination) شروع کرده و تمام لینک‌های اخبار موجود در هر صفحه را استخراج می‌کند.

```bash
python scraper.py --site armandaily --start 0 --count 5
```
*   `--start`: شماره صفحه شروع (معمولاً ۰ یا ۱).
*   `--count`: تعداد صفحات لیست که باید بررسی شوند.

### ۸. اسکرپر اخبار بانک (banki)
استخراج اخبار بر اساس شناسه (ID) صفحه.
این اسکرپر متن خبر را از تگ `div` با شناسه `doctextarea` استخراج می‌کند.

```bash
python scraper.py --site banki --start 102371 --count 10
```

### ۹. اسکرپر فرارو (fararu)
استخراج اخبار بر اساس شناسه (ID) صفحه.

```bash
python scraper.py --site fararu --start 931959 --count 10
```

### ۱۰. اسکرپر تسنیم (tasnim)
استخراج اخبار بر اساس شناسه (ID) صفحه.

```bash
python scraper.py --site tasnim --start 3470177 --count 10
```

### ۱۱. اسکرپر مهر (mehr)
استخراج اخبار بر اساس شناسه (ID) صفحه.

```bash
python scraper.py --site mehr --start 6687686 --count 10
```

## ستون‌های خروجی
فایل اکسل خروجی شامل ستون‌های زیر است:
*   `Title`: عنوان خبر
*   `Link`: لینک خبر
*   `Full_Text`: متن کامل
*   `Keywords`: کلمات کلیدی استخراج شده (۱۰ کلمه برتر با استفاده از TF-IDF)
*   `Gregorian_Date`: تاریخ میلادی
*   `Scraped_Date`: تاریخ استخراج
*   `Image`: لینک تصویر شاخص
*   `Description`: خلاصه یا پاراگراف اول

## استفاده با داکر (Docker)

1.  ساخت ایمیج (Image):
    ```bash
    docker build -t persian-scraper .
    ```

2.  اجرای اسکرپر (اتصال یک Volume برای ذخیره داده‌ها):
    ```bash
    docker run -v $(pwd)/data:/app/data persian-scraper --site inn --start 43712 --count 10 --output /app/data/inn.xlsx
    ```
