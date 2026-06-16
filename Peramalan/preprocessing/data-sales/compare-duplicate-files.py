import pandas as pd
import hashlib

file1 = r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\sales_clean\clean_20260322_122705_MR_TotalSalesByDayBySKU_2410091.csv"
file2 = r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\sales_clean\clean_20260322_122747_MR_TotalSalesByDayBySKU_2410091.csv"

print("=== Membandingkan 2 file September 2025 ===\n")

# Baca kedua file
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

print(f"File 1 shape: {df1.shape}")
print(f"File 2 shape: {df2.shape}")

# Bandingkan struktur
print(f"\nKolom sama? {list(df1.columns) == list(df2.columns)}")

# Bandingkan data
if df1.shape == df2.shape:
    # Cek apakah data benar-benar identik
    is_identical = df1.equals(df2)
    print(f"Data benar-benar identik? {is_identical}")
    
    if not is_identical:
        # Cari perbedaannya
        print("\n=== Mencari perbedaan ===")
        diff_mask = df1 != df2
        diff_count = diff_mask.sum().sum()
        print(f"Jumlah sel yang berbeda: {diff_count}")
        
        if diff_count > 0:
            print("\nKolom dengan perbedaan:")
            for col in df1.columns:
                diff_in_col = (df1[col] != df2[col]).sum()
                if diff_in_col > 0:
                    print(f"  {col}: {diff_in_col} perbedaan")
    else:
        print("\n⚠️ KEDUA FILE BENAR-BENAR IDENTIK (100% DUPLIKAT)")
        
# Sample data dari masing-masing file
print("\n=== Sample dari File 1 (5 baris pertama) ===")
print(df1.head())

print("\n=== Sample dari File 2 (5 baris pertama) ===")
print(df2.head())

# Cek total sales di masing-masing file
print("\n=== Total Sales ===")
print(f"File 1 total sales: Rp {df1['Sales'].sum():,.0f}")
print(f"File 2 total sales: Rp {df2['Sales'].sum():,.0f}")
print(f"Selisih: Rp {abs(df1['Sales'].sum() - df2['Sales'].sum()):,.0f}")
