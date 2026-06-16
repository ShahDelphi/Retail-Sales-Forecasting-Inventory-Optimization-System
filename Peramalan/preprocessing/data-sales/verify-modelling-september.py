import pandas as pd
import os

print("=== Verifikasi September 2025 di Dataset Modelling ===\n")

base_path = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling\dataset\time-series"

for dept in ["fruit", "vegetable"]:
    print(f"\n{'='*60}")
    print(f"  {dept.upper()}")
    print(f"{'='*60}")
    
    for kelas in ["A", "B", "C"]:
        file_path = os.path.join(base_path, dept, f"timeseries_{kelas}.csv")
        
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Filter September 2025
        df_sept = df[(df['Date'].dt.year == 2025) & (df['Date'].dt.month == 9)]
        
        total_sales = df_sept['Sales'].sum()
        total_rows = len(df_sept)
        avg_sales = total_sales / total_rows if total_rows > 0 else 0
        
        print(f"Kelas {kelas}:")
        print(f"  Total Sales Sept 2025: Rp {total_sales:,.0f}")
        print(f"  Total Rows: {total_rows:,}")
        print(f"  Avg Sales/Row: Rp {avg_sales:,.0f}")

# Bandingkan dengan bulan lain
print(f"\n{'='*60}")
print("  PERBANDINGAN MONTHLY (FRUIT - Kelas A)")
print(f"{'='*60}")

file_path = os.path.join(base_path, "fruit", "timeseries_A.csv")
df = pd.read_csv(file_path)
df['Date'] = pd.to_datetime(df['Date'])
df['YearMonth'] = df['Date'].dt.to_period('M')

monthly = df.groupby('YearMonth').agg({
    'Sales': 'sum',
    'SKU': 'count'
}).reset_index()
monthly.columns = ['YearMonth', 'Total_Sales', 'Total_Rows']
monthly['Avg_Sales_per_Row'] = monthly['Total_Sales'] / monthly['Total_Rows']

print("\n2025 Monthly:")
monthly_2025 = monthly[monthly['YearMonth'].astype(str).str.startswith('2025')]
print(monthly_2025.to_string(index=False))

print(f"\n{'='*60}")
print("  PERBANDINGAN MONTHLY (VEGETABLE - Kelas A)")
print(f"{'='*60}")

file_path = os.path.join(base_path, "vegetable", "timeseries_A.csv")
df = pd.read_csv(file_path)
df['Date'] = pd.to_datetime(df['Date'])
df['YearMonth'] = df['Date'].dt.to_period('M')

monthly = df.groupby('YearMonth').agg({
    'Sales': 'sum',
    'SKU': 'count'
}).reset_index()
monthly.columns = ['YearMonth', 'Total_Sales', 'Total_Rows']
monthly['Avg_Sales_per_Row'] = monthly['Total_Sales'] / monthly['Total_Rows']

print("\n2025 Monthly:")
monthly_2025 = monthly[monthly['YearMonth'].astype(str).str.startswith('2025')]
print(monthly_2025.to_string(index=False))
