# %%
# Importing necessary libraries
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import nepali_datetime as nd
import datetime
from openpyxl import load_workbook

# %%
# Accessing to the website for data fetching
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
chrome_options = Options()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.get("https://old.fcgo.gov.np/daily-budgetary-analysis")
WebDriverWait(driver, 10).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)

# %%
# Accessing the html element and storing the data in the specified variable
table = driver.find_element(By.XPATH,"/html/body/div[1]/div/div/div/div/article/div[2]/table")
rows = table.find_elements(By.TAG_NAME, "tr")

# --- Step 1: fiscal_date (first element of first row) ---
first_row_cols = rows[0].find_elements(By.TAG_NAME, "th") + \
                 rows[0].find_elements(By.TAG_NAME, "td")

fiscal_date = first_row_cols[0].text
# --- Step 2: skip first and second row, extract last 5 columns ---
data = []
for row in rows[2:]:  # skip first 2 rows
    cols = row.find_elements(By.TAG_NAME, "td")
    values = [col.text for col in cols]
    if len(values) >= 5:
        data.append(values[-5:])  # last 5 elements
# --- Step 3: create dataframe ---
new_data = pd.DataFrame(data)
# Now quit the driver
driver.quit()

# %%
# for extracting dates from fiscal_date value
nepali_date = fiscal_date[6:16]
english_date = fiscal_date[18:28]
np_date = nd.date(int(nepali_date[:4]), int(nepali_date[5:7]), int(nepali_date[8:10]))
nepali_date = np_date
x= np_date
# for converting to english date
english_date = datetime.datetime.strptime(english_date, "%Y-%m-%d").date()

# for fiscal year
fiscal_year = f"{x.year}_{x.year+1-2000}" if x.month >= 4 else f"{x.year-1}_{x.year-2000}"

# for day of the year
day_of_year = (
    (x - nd.date(x.year, 4, 1)).days + 1
    if x.month >= 4
    else (x - nd.date(x.year - 1, 4, 1)).days + 1)
# for day of the week
day_of_week = x.strftime("%A")
date_time_obj = [nepali_date, english_date,np_date, fiscal_year, day_of_year, day_of_week]

# %%
# for generating revenue_list
revenue_target = new_data.iloc[0:6, 0].tolist()
revenue_upto_yesterday = new_data.iloc[0:6, 1].tolist()
revenue_today = new_data.iloc[0:6, 2].tolist()
revenue_upto_today = new_data.iloc[0:6, 3].tolist()
revenue_percentage = new_data.iloc[0:6, 4].tolist()
revenue_list = revenue_target + revenue_upto_yesterday + revenue_today + revenue_upto_today + revenue_percentage

# for generating expenditure_list
expenditure_target = new_data.iloc[6:10, 0].tolist()    
expenditure_upto_yesterday = new_data.iloc[6:10, 1].tolist()
expenditure_today = new_data.iloc[6:10, 2].tolist()
expenditure_upto_today = new_data.iloc[6:10, 3].tolist()
expenditure_percentage = new_data.iloc[6:10, 4].tolist()
expenditure_list = expenditure_target + expenditure_upto_yesterday + expenditure_today + expenditure_upto_today + expenditure_percentage

# for generating total_list. total_list should have 56 elements in it.
total_list = date_time_obj + revenue_list + expenditure_list

# %%
# now append this total_list to the excel file
df = pd.read_excel("fiscal_dashboard_data.xlsx")
df.loc[len(df)] = total_list
# Define function to convert nepali date string to nepali datetime object
df['english_date'] = pd.to_datetime(df['english_date'], format='%Y-%m-%d')
# Drop duplicates based on 'nepali_date' column, keeping the first occurrence
df.drop_duplicates(subset=['english_date'], keep="first",inplace=True)
df.to_excel("fiscal_dashboard_data.xlsx", index=False)


