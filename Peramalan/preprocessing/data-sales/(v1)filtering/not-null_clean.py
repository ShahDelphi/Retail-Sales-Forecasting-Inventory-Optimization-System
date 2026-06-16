import pandas as pd
import os

input_path  = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\fix_data-sales\final_dataset.csv"
output_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset"
os.makedirs(output_folder, exist_ok=True)

# Load data
df = pd.read_csv(input_path, dtype={"SKU": str})
df["SKU"] = df["SKU"].str.zfill(8)
print(f"Sebelum filter : {len(df):,} baris")

# Hapus baris dengan (Sales = 0 DAN Sales Qty = 0)
df_clean = df[(df["Sales"] > 0) | (df["Sales Qty"] > 0)].reset_index(drop=True)
print(f"Setelah filter : {len(df_clean):,} baris")
print(f"Dihapus        : {len(df) - len(df_clean):,} baris (Sales & Qty = 0)")

print("\nContoh data:")
print(df_clean.head(10).to_string(index=False))

# Simpan
output_path = os.path.join(output_folder, "final_dataset_clean.csv")
df_clean.to_csv(output_path, index=False)
print(f"\n✅ Disimpan di: {output_path}")
