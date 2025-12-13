# Test Inn
Write-Host "Testing Inn..."
python scraper.py --site inn --start 43716 --count 2 --output test_inn.xlsx

# Test Mehr
Write-Host "Testing Mehr..."
python scraper.py --site mehr --start 6687686 --count 2 --output test_mehr.xlsx

# Test Ettelaat
Write-Host "Testing Ettelaat..."
python scraper.py --site ettelaat --count 1 --output test_ettelaat.xlsx

# Test Banki
Write-Host "Testing Banki..."
python scraper.py --site banki --start 102371 --count 2 --output test_banki.xlsx

# Test Asia News
Write-Host "Testing Asia News..."
python scraper.py --site asianews --start 1 --count 1 --output test_asianews.xlsx

# Test Armandaily
Write-Host "Testing Armandaily..."
python scraper.py --site armandaily --start 0 --count 1 --output test_armandaily.xlsx
