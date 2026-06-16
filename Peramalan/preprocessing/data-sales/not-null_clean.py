import pandas as pd
import os

input_path  = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\fix_data-sales\final_dataset.csv"
output_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset"
os.makedirs(output_folder, exist_ok=True)

# Load data
df = pd.read_csv(input_path, dtype={"SKU": str})
df["SKU"] = df["SKU"].str.zfill(8)
df["Date"] = pd.to_datetime(df["Date"])
print(f"Sebelum filter : {len(df):,} baris")

# 1. Hapus baris dengan (Sales = 0 DAN Sales Qty = 0)
df_clean = df[(df["Sales"] > 0) | (df["Sales Qty"] > 0)].reset_index(drop=True)
print(f"Setelah filter baris nol : {len(df_clean):,} baris")

# 2. Filter SKU aktif tahun 2025 saja
# Ambil set SKU unik yang memiliki transaksi penjualan di tahun 2025
active_skus_2025 = set(df_clean[df_clean["Date"].dt.year == 2025]["SKU"].unique())
print(f"Jumlah SKU unik aktif di tahun 2025: {len(active_skus_2025):,}")

# Filter dataset agar hanya menyimpan SKU aktif tersebut
sku_before = df_clean["SKU"].nunique()
df_clean = df_clean[df_clean["SKU"].isin(active_skus_2025)].reset_index(drop=True)
sku_after = df_clean["SKU"].nunique()

print(f"Filter SKU aktif 2025    : {len(df_clean):,} baris")
print(f"SKU dihapus (tidak aktif di 2025): {sku_before - sku_after:,} SKU")

# Kembalikan format tanggal ke string YYYY-MM-DD agar seragam di CSV
df_clean["Date"] = df_clean["Date"].dt.strftime("%Y-%m-%d")

print("\nContoh data:")
print(df_clean.head(10).to_string(index=False))

# Simpan
output_path = os.path.join(output_folder, "final_dataset_clean.csv")
df_clean.to_csv(output_path, index=False)
print(f"\n✅ Disimpan di: {output_path}")
