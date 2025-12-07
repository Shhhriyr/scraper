# Persian News Scraper

This repository contains a unified web scraper for various Iranian news websites and Wikipedia.

## Supported Websites

1.  **Hamshahri Online** (`--hamshahri_scraper`)
2.  **Kayhan** (`--kayhan_scraper`)
3.  **Ettelaat** (`--ettelaat_scraper`)
4.  **Asia News** (`--asianews_scraper`)
5.  **Wikipedia (Persian)** (`--wiki_scraper`)

## Prerequisites

*   Python 3.8+
*   See `requirements.txt` for python dependencies.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd scraper
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run `scraper.py` with the desired flag.

### Common Arguments

*   `--workers`: Number of parallel threads (default: 5).
*   `--output`: Custom output filename (e.g., `my_data.xlsx`).

### 1. Hamshahri Scraper
Scrapes news pages by ID.

```bash
python scraper.py --hamshahri_scraper --start 1000 --count 50
```
*   `--start`: Starting Page ID.
*   `--count`: Number of pages to check.

### 2. Kayhan Scraper
Scrapes news pages by ID.

```bash
python scraper.py --kayhan_scraper --start 1 --count 20
```

### 3. Ettelaat Scraper
Scrapes archives by date.

```bash
python scraper.py --ettelaat_scraper --days 3
```
*   `--days`: Number of past days to scrape (default: 1).

### 4. Asia News Scraper
Scrapes the archive list and downloads images.

```bash
python scraper.py --asianews_scraper --count 5
```
*   `--count`: Number of archive list pages to traverse.
*   Images are saved in `asianews_data/`.

### 5. Wikipedia Scraper
Scrapes Persian Wikipedia pages starting from a list.

```bash
python scraper.py --wiki_scraper
```

## Docker Usage

1.  Build the image:
    ```bash
    docker build -t persian-scraper .
    ```

2.  Run a scraper (mount a volume to save data):
    ```bash
    docker run -v $(pwd)/data:/app/data persian-scraper --hamshahri_scraper --start 100 --count 10 --output /app/data/hamshahri.xlsx
    ```
