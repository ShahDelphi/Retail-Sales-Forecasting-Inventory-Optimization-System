import pandas as pd

# Load dataset
df = pd.read_csv(r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_clean.csv")

# Filter data September 2025
df['Date'] = pd.to_datetime(df['Date'])
df_sept_2025 = df[(df['Date'].dt.year == 2025) & (df['Date'].dt.month == 9)]

print(f"Total baris September 2025: {len(df_sept_2025)}")
print(f"Jumlah tanggal unik: {df_sept_2025['Date'].nunique()}")
print(f"Range tanggal: {df_sept_2025['Date'].min()} s/d {df_sept_2025['Date'].max()}")

# Cek duplikasi berdasarkan semua kolom
duplicated_rows = df_sept_2025[df_sept_2025.duplicated(keep=False)]
print(f"\nBaris yang duplikat (exact duplicates): {len(duplicated_rows)}")

if len(duplicated_rows) > 0:
    print(f"Baris unik yang duplikat: {len(duplicated_rows.drop_duplicates())}")
    
# Cek duplikasi berdasarkan SKU dan Date
duplicated_sku_date = df_sept_2025[df_sept_2025.duplicated(subset=['SKU', 'Date'], keep=False)]
print(f"\nBaris dengan SKU & Date yang sama: {len(duplicated_sku_date)}")

if len(duplicated_sku_date) > 0:
    print(f"\nContoh duplikasi SKU & Date:")
    sample = duplicated_sku_date.groupby(['SKU', 'Date']).size().reset_index(name='count')
    print(sample.sort_values('count', ascending=False).head(10))
    
# Analisis per tanggal
print("\n=== Analisis per tanggal September 2025 ===")
date_counts = df_sept_2025.groupby('Date').size().reset_index(name='count')
print(date_counts.sort_values('Date'))

print("\n=== Total transaksi per tanggal ===")
total_sales = df_sept_2025.groupby('Date')['Sales'].sum().reset_index()
print(total_sales.sort_values('Date'))
