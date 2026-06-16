import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv(r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_clean.csv")

# Convert Date
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['YearMonth'] = df['Date'].dt.to_period('M')

# Analisis total sales per bulan
monthly_sales = df.groupby('YearMonth').agg({
    'Sales': 'sum',
    'SKU': 'count'
}).reset_index()
monthly_sales.columns = ['YearMonth', 'Total_Sales', 'Total_Rows']
monthly_sales['Avg_Sales_per_Row'] = monthly_sales['Total_Sales'] / monthly_sales['Total_Rows']

print("=== Total Sales per Bulan ===")
print(monthly_sales.to_string())

print("\n=== Statistik September 2025 ===")
sept_2025 = monthly_sales[monthly_sales['YearMonth'] == '2025-09']
print(f"Total Sales: Rp {sept_2025['Total_Sales'].values[0]:,.0f}")
print(f"Total Rows: {sept_2025['Total_Rows'].values[0]:,}")
print(f"Avg Sales/Row: Rp {sept_2025['Avg_Sales_per_Row'].values[0]:,.0f}")

print("\n=== Perbandingan dengan bulan lain di 2025 ===")
monthly_2025 = monthly_sales[monthly_sales['YearMonth'].astype(str).str.startswith('2025')]
print(monthly_2025.to_string())

print("\n=== Ranking Total Sales ===")
top_months = monthly_sales.sort_values('Total_Sales', ascending=False).head(10)
print(top_months.to_string())

# Cek apakah September 2025 memiliki data duplikat dibanding bulan lain
print("\n=== Analisis Jumlah Baris per Bulan 2025 ===")
monthly_2025_sorted = monthly_2025.sort_values('Total_Rows', ascending=False)
print(monthly_2025_sorted[['YearMonth', 'Total_Rows']].to_string())

# Analisis per Store untuk September 2025
print("\n=== Analisis September 2025 per Store ===")
df_sept_2025 = df[(df['Year'] == 2025) & (df['Month'] == 9)]
store_sales = df_sept_2025.groupby('Store').agg({
    'Sales': 'sum',
    'SKU': 'count'
}).reset_index()
store_sales.columns = ['Store', 'Total_Sales', 'Total_Rows']
print(store_sales.to_string())
