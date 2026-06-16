import pandas as pd
import os

print("=== Regenerating all_sales_clean.csv ===\n")

# Folder input
input_folder = r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\sales_clean"
output_file = os.path.join(input_folder, "all_sales_clean.csv")

# Baca semua file clean_*.csv
all_data = []
file_count = 0

for file in sorted(os.listdir(input_folder)):
    if file.startswith("clean_") and file.endswith(".csv"):
        file_path = os.path.join(input_folder, file)
        print(f"Reading: {file}")
        
        df = pd.read_csv(file_path)
        print(f"  Rows: {len(df):,}")
        
        # Tampilkan date range
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        all_data.append(df)
        file_count += 1

print(f"\nTotal files processed: {file_count}")

# Gabung semua
print("\nCombining all files...")
final_df = pd.concat(all_data, ignore_index=True)
print(f"Total rows before groupby: {len(final_df):,}")

# Group by untuk handle duplikat antar file (jika ada)
print("\nGrouping by Date, SKU, Store...")
final_df = (
    final_df
    .groupby(["Date", "SKU", "Store"], as_index=False)[["Sales Amount", "Sales Qty"]]
    .sum()
    .sort_values(["Date", "SKU", "Store"])
    .reset_index(drop=True)
)

print(f"Total rows after groupby: {len(final_df):,}")

# Save
final_df.to_csv(output_file, index=False)
print(f"\n✅ SAVED: {output_file}")
print(f"   Total baris: {len(final_df):,}")

# Analisis per bulan
final_df['Date'] = pd.to_datetime(final_df['Date'])
final_df['YearMonth'] = final_df['Date'].dt.to_period('M')

monthly_summary = final_df.groupby('YearMonth').agg({
    'Sales Amount': 'sum',
    'SKU': 'count'
}).reset_index()
monthly_summary.columns = ['YearMonth', 'Total_Sales', 'Total_Rows']

print("\n=== Monthly Summary ===")
print(monthly_summary.to_string())

print("\n=== September 2025 Details ===")
sept_2025 = monthly_summary[monthly_summary['YearMonth'] == '2025-09']
if not sept_2025.empty:
    print(f"Total Sales: Rp {sept_2025['Total_Sales'].values[0]:,.0f}")
    print(f"Total Rows: {sept_2025['Total_Rows'].values[0]:,}")
else:
    print("No September 2025 data found")
