# %%
# Importing necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# %%
# Import data and clean it
df1 = pd.read_excel('fiscal_dashboard_data.xlsx')
exclude_cols = ['nepali_date','english_date','np_date','fiscal_year','day_of_year','name_of_the_day']
cols_to_clean = [c for c in df1.columns if c not in exclude_cols]
df1[cols_to_clean] = (df1[cols_to_clean].astype(str) .replace({',': '', ' ': '', '%': ''}, regex=True))
df1[cols_to_clean] = df1[cols_to_clean].apply(pd.to_numeric, errors='coerce')

# %%
# Select only three columns and the current fiscal year
df1 = df1[df1['fiscal_year'] == "2082_83"]
# df1 = df1[['day_of_year','total_revenue_percentage','total_expenditure_percentage']]
df1 = df1.iloc[4:].reset_index(drop=True)

# %%
# Forward fill with previous value if there is zero value
cols = ['total_revenue_percentage', 'total_expenditure_percentage']
df1[cols] = df1[cols].replace(0, np.nan)
df1[cols] = df1[cols].ffill()

# %%
df1.columns

# %%
# Now make table
# Build base table
last = df1.iloc[-1]
summary_table = pd.DataFrame(
    {
        'target_amount': [last['total_revenue_target'],last['total_expenditure_target']],
        'Collection_to_Date': [last['total_revenue_upto_today'],last['total_expenditure_upto_today']],
        'Percentage': [last['total_revenue_percentage'],last['total_expenditure_percentage']]
    },
    index=['Revenue', 'Expenditure']
)

# Compute Surplus / Deficit (Revenue - Expenditure)
surplus_deficit = summary_table.loc['Revenue'] - summary_table.loc['Expenditure']
summary_table.loc['Surplus/Deficit'] = surplus_deficit
print(summary_table)

# %%
# Draw line plot
plt.figure(figsize=(10, 5))
plt.plot(df1['day_of_year'], df1['total_revenue_percentage'], label='Revenue Percentage')
plt.plot(df1['day_of_year'], df1['total_expenditure_percentage'], label='Expenditure Percentage')
plt.xlabel('Day of Year')
plt.ylabel('Percentage')
plt.title('Revenue vs Expenditure Percentage Over Time')
plt.legend()
plt.show()


