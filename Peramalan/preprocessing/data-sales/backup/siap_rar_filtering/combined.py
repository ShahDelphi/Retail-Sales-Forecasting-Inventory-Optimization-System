import pandas as pd
import os

# ======================
# LOAD SALES
# ======================
sales_path = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\sales_clean\all_sales_clean.csv"
df_sales = pd.read_csv(sales_path)
df_sales = df_sales.rename(columns={"Sales Amount": "Sales"})

# bersihkan SKU sales + zero-pad ke 8 digit agar cocok dengan master (ex: 800068 → 00800068)
df_sales["SKU"] = df_sales["SKU"].astype(str).str.strip().str.zfill(8)
print("Sales shape:", df_sales.shape)

# ======================
# LOAD MASTER ITEM
# Kolom yang diperlukan:
#   'Short SKU'               → SKU
#   'Description'             → SKU Name
#   'Department'              → Dept       (ex: ="2038")
#   'Department Description'  → Dept Name  (ex: FRUIT)
#   'Category Description'    → Category   (ex: STONEFRUIT)
# ======================
master_path = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\Master Item\20260322_162314_MT_SkuDescListing_2410091.csv"

df_master = pd.read_csv(
    master_path,
    skiprows=3,
    encoding="utf-8-sig",
    on_bad_lines="skip",
    low_memory=False,
    usecols=["Short SKU", "Description", "Department", "Department Description", "Category Description"]
)

# rename ke nama yang lebih bersih
df_master = df_master.rename(columns={
    "Short SKU":              "SKU",
    "Description":            "SKU Name",
    "Department":             "Dept",
    "Department Description": "Dept Name",
    "Category Description":   "Category",
})

# bersihkan SKU master (hapus format ="00800013")
df_master["SKU"] = (
    df_master["SKU"]
    .astype(str)
    .str.replace('="', '', regex=False)
    .str.replace('"', '', regex=False)
    .str.strip()
)

# bersihkan Dept (hapus format ="2038")
df_master["Dept"] = (
    df_master["Dept"]
    .astype(str)
    .str.replace('="', '', regex=False)
    .str.replace('"', '', regex=False)
    .str.strip()
)

# hapus duplikat SKU
df_master = df_master.drop_duplicates(subset=["SKU"])
print("Master shape:", df_master.shape)
print("\nContoh master:")
print(df_master.head(5).to_string(index=False))

# ======================
# JOIN
# ======================
df_final = df_sales.merge(df_master, on="SKU", how="left")

# urutkan kolom output
df_final = df_final[["Date", "Store", "SKU", "SKU Name", "Dept", "Dept Name", "Category", "Sales", "Sales Qty"]]
df_final = df_final.sort_values(["Date", "Store", "SKU"]).reset_index(drop=True)

print("\n✅ JOIN BERHASIL")
print("Jumlah data:", len(df_final))
print("\nContoh output:")
print(df_final.head(10).to_string(index=False))

# cek berapa SKU yang tidak match
unmatched = df_final["Dept"].isna().sum()
print(f"\nSKU tidak match master: {unmatched} baris ({unmatched/len(df_final)*100:.1f}%)")

# ======================
# FIX TIPE DATA
# ======================
df_final["Date"]  = pd.to_datetime(df_final["Date"], errors="coerce")   # datetime64
df_final["Store"] = df_final["Store"].astype(str)                        # object
df_final["SKU"]   = df_final["SKU"].astype(str).str.zfill(8)            # object (8 digit)
df_final["Sales"] = df_final["Sales"].astype(float)                      # float64
df_final["Sales Qty"] = df_final["Sales Qty"].astype(float)              # float64

print("\n✅ TIPE DATA FINAL:")
print(df_final.dtypes)

# ======================
# SAVE
# ======================
output_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\fix_data-sales"
os.makedirs(output_folder, exist_ok=True)

# Simpan CSV
output_csv = os.path.join(output_folder, "final_dataset.csv")
df_final.to_csv(output_csv, index=False)
print(f"\nCSV disimpan : {output_csv}")

# Simpan sample XLSX (500 baris pertama) agar SKU tampil benar di Excel
# Excel tidak bisa handle 7.4 juta baris, jadi hanya sample
output_xlsx = os.path.join(output_folder, "final_dataset_sample.xlsx")
df_sample = df_final.head(500).copy()

with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
    df_sample.to_excel(writer, index=False, sheet_name="Data")
    ws = writer.sheets["Data"]
    sku_col_idx = df_final.columns.get_loc("SKU") + 1
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row,
                             min_col=sku_col_idx, max_col=sku_col_idx):
        for cell in row:
            cell.number_format = "@"
            cell.value = str(cell.value).zfill(8)

print(f"XLSX sample  : {output_xlsx} (500 baris pertama)")
print("\n⚠️  Untuk buka CSV lengkap di Excel tanpa leading zero hilang:")
print("   → Gunakan menu Data → Get Data → From Text/CSV")
print("   → Set kolom SKU sebagai 'Text'")