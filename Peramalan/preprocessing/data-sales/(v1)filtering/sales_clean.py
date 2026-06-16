import pandas as pd
import os

input_folder  = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\Sales"
output_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\sales_clean"
os.makedirs(output_folder, exist_ok=True)

# Mapping nama kolom → Store ID
# AOLS (online) dipetakan ke Store ID yang SAMA dengan AIN (offline) pasangannya
# sehingga saat di-group, sales offline + online otomatis terjumlah
store_mapping = {
    # Offline (AIN) → Store ID
    "AIN BSD":  1001,
    "AIN JGC":  1002,
    "AIN STL":  1003,
    "AIN TJB":  1004,
    "AIN DTM":  1005,
    "AIN ALS":  1006,
    "AIN KWS":  1007,
    "AIN MCT":  1008,
    "AIN PMB":  1009,
    "AIN EVR":  1010,
    "AIN PVJ":  1011,
    "AIN DPM":  1012,
    "AIN PMS":  1013,
    # Online (AOLS) → Store ID yang SAMA dengan pasangan offline-nya
    "AOLS BSD": 1001,   # AOLS BSD (5101) → 1001
    "AOLS JGC": 1002,   # AOLS JGC (5102) → 1002
    "AOLS SC":  1003,   # AOLS SC  (5103) → 1003
    "AOLS TJB": 1004,   # AOLS TJB (5104) → 1004
    "AOLS ALS": 1006,   # AOLS ALS (5106) → 1006
}

all_data = []

for file in os.listdir(input_folder):
    if file.endswith(".csv"):
        print(f"\nProcessing: {file}")
        file_path = os.path.join(input_folder, file)

        df = pd.read_csv(file_path, skiprows=7, header=[0, 1], low_memory=False)

        # flatten multi-level header
        df.columns = [
            ' '.join([str(i) for i in col if str(i) != 'nan']).strip()
            for col in df.columns
        ]

        # detect kolom Date dan Item (SKU)
        date_col = [c for c in df.columns if c.startswith("Date")][0]
        sku_col  = [c for c in df.columns if c.startswith("Item ")][0]

        df = df.rename(columns={date_col: "Date", sku_col: "SKU"})

        # ambil kolom Sales Qty & Amount
        store_amt_cols = [c for c in df.columns if "Sales Amount" in c]
        store_qty_cols = [c for c in df.columns if "Sales Qty" in c]
        print(f"  Kolom Amount ({len(store_amt_cols)}), Qty ({len(store_qty_cols)})")

        df = df[["Date", "SKU"] + store_amt_cols + store_qty_cols]
        df = df[df["Date"].notna()]

        # unpivot
        df_amt = df.melt(id_vars=["Date", "SKU"], value_vars=store_amt_cols, var_name="Store_Raw", value_name="Sales Amount")
        df_qty = df.melt(id_vars=["Date", "SKU"], value_vars=store_qty_cols, var_name="Store_Raw", value_name="Sales Qty")

        # Pastikan alignment terjamin dengan menggabungkan jadi satu dataframe (melt beroperasi berurutan)
        df_melt = df_amt.copy()
        df_melt["Sales Qty"] = df_qty["Sales Qty"].values
        
        # Bersihkan & konversi
        df_melt["Sales Amount"] = df_melt["Sales Amount"].astype(str).str.replace(r"[^\d.-]", "", regex=True)
        df_melt["Sales Amount"] = pd.to_numeric(df_melt["Sales Amount"], errors="coerce").fillna(0)
        
        df_melt["Sales Qty"]    = df_melt["Sales Qty"].astype(str).str.replace(r"[^\d.-]", "", regex=True)
        df_melt["Sales Qty"]    = pd.to_numeric(df_melt["Sales Qty"], errors="coerce").fillna(0)
        
        # Ekstrak nama toko dari kolom Amount (contoh: "AIN BSD Sales Amount(Without VAT)")
        df_melt["Store"] = df_melt["Store_Raw"].str.extract(r"^((?:AOLS|AIN) \w+)")[0].map(store_mapping)
        df_melt = df_melt.drop(columns=["Store_Raw"])

        # bersihkan SKU + zero-pad ke 8 digit (801539 → 00801539)
        df_melt["SKU"] = (
            df_melt["SKU"]
            .astype(str)
            .str.replace('="', '', regex=False)
            .str.replace('"', '', regex=False)
            .str.strip()
            .str.zfill(8)
        )

        # bersihkan Date
        df_melt["Date"] = pd.to_datetime(df_melt["Date"], errors="coerce")

        # drop baris tidak valid
        df_melt = df_melt.dropna(subset=["Date", "Store"])
        df_melt = df_melt[df_melt["SKU"] != ""]
        df_melt["Store"] = df_melt["Store"].astype(int)

        # ✅ GROUP BY Date + SKU + Store (Re-aggregate safe net)
        df_result = (
            df_melt
            .groupby(["Date", "SKU", "Store"], as_index=False)[["Sales Amount", "Sales Qty"]]
            .sum()
            .sort_values(["Date", "SKU", "Store"])
            .reset_index(drop=True)
        )

        print(f"  Jumlah baris hasil: {len(df_result)}")
        print(df_result.head(5).to_string(index=False))

        output_file = os.path.join(output_folder, f"clean_{file}")
        df_result.to_csv(output_file, index=False)
        all_data.append(df_result)

# gabung semua file
final_df = pd.concat(all_data, ignore_index=True)

# jika ada duplikat antar file, jumlahkan lagi
final_df = (
    final_df
    .groupby(["Date", "SKU", "Store"], as_index=False)[["Sales Amount", "Sales Qty"]]
    .sum()
    .sort_values(["Date", "SKU", "Store"])
    .reset_index(drop=True)
)

output_all = os.path.join(output_folder, "all_sales_clean.csv")
final_df.to_csv(output_all, index=False)

print(f"\n✅ SELESAI")
print(f"   Total baris  : {len(final_df)}")
print(f"   Contoh output:\n{final_df.head(10).to_string(index=False)}")