# Importing necessary libraries
import os
import pandas as pd
import numpy as np
import time
import nepali_datetime as nd
import datetime
from openpyxl import load_workbook

# Accessing to the website for data fetching
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Headless Chrome setup (works both locally and on GitHub Actions) ──────────
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# On GitHub Actions, chromedriver is pre-installed at /usr/bin/chromedriver
# Locally, webdriver_manager handles it automatically
import sys
if sys.platform == "linux":
    # GitHub Actions (Ubuntu)
    service = Service("/usr/bin/chromedriver")
else:
    # Local Mac/Windows — use webdriver_manager
    from webdriver_manager.chrome import ChromeDriverManager
    service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get("https://old.fcgo.gov.np/daily-budgetary-analysis")
WebDriverWait(driver, 10).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)

# ── Accessing the html element ─────────────────────────────────────────────────
table = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/div/article/div[2]/table")
rows = table.find_elements(By.TAG_NAME, "tr")

# fiscal_date (first element of first row)
first_row_cols = rows[0].find_elements(By.TAG_NAME, "th") + \
                 rows[0].find_elements(By.TAG_NAME, "td")
fiscal_date = first_row_cols[0].text

# Skip first and second row, extract last 5 columns
data = []
for row in rows[2:]:
    cols = row.find_elements(By.TAG_NAME, "td")
    values = [col.text for col in cols]
    if len(values) >= 5:
        data.append(values[-5:])

new_data = pd.DataFrame(data)
driver.quit()

# ── Extract dates from fiscal_date ────────────────────────────────────────────
nepali_date  = fiscal_date[6:16]
english_date = fiscal_date[18:28]
np_date      = nd.date(int(nepali_date[:4]), int(nepali_date[5:7]), int(nepali_date[8:10]))
nepali_date  = np_date
x            = np_date

english_date = datetime.datetime.strptime(english_date, "%Y-%m-%d").date()

fiscal_year = (
    f"{x.year}_{x.year+1-2000}" if x.month >= 4
    else f"{x.year-1}_{x.year-2000}"
)

day_of_year = (
    (x - nd.date(x.year, 4, 1)).days + 1
    if x.month >= 4
    else (x - nd.date(x.year - 1, 4, 1)).days + 1
)

day_of_week   = x.strftime("%A")
date_time_obj = [nepali_date, english_date, np_date, fiscal_year, day_of_year, day_of_week]

# ── Revenue list ───────────────────────────────────────────────────────────────
revenue_target           = new_data.iloc[0:6, 0].tolist()
revenue_upto_yesterday   = new_data.iloc[0:6, 1].tolist()
revenue_today            = new_data.iloc[0:6, 2].tolist()
revenue_upto_today       = new_data.iloc[0:6, 3].tolist()
revenue_percentage       = new_data.iloc[0:6, 4].tolist()
revenue_list             = revenue_target + revenue_upto_yesterday + revenue_today + revenue_upto_today + revenue_percentage

# ── Expenditure list ───────────────────────────────────────────────────────────
expenditure_target         = new_data.iloc[6:10, 0].tolist()
expenditure_upto_yesterday = new_data.iloc[6:10, 1].tolist()
expenditure_today          = new_data.iloc[6:10, 2].tolist()
expenditure_upto_today     = new_data.iloc[6:10, 3].tolist()
expenditure_percentage     = new_data.iloc[6:10, 4].tolist()
expenditure_list           = expenditure_target + expenditure_upto_yesterday + expenditure_today + expenditure_upto_today + expenditure_percentage

total_list = date_time_obj + revenue_list + expenditure_list

# ── Append to Excel and push back to repo ─────────────────────────────────────
EXCEL_FILE = "fiscal_dashboard_data.xlsx"

df = pd.read_excel(EXCEL_FILE)
df.loc[len(df)] = total_list
df['english_date'] = pd.to_datetime(df['english_date'], format='%Y-%m-%d')
df.drop_duplicates(subset=['english_date'], keep="first", inplace=True)
df.to_excel(EXCEL_FILE, index=False)

print(f"✅ Excel updated successfully for {english_date}")
