import pandas as pd
import os

by_abc_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-abc"
ts_input      = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_clean.csv"

promo_input   = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\promo\promotion_discount_clean.csv"

ts_base = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\time-series"
ts_folders = {
    "FRUIT":     os.path.join(ts_base, "fruit"),
    "VEGETABLE": os.path.join(ts_base, "vegetable"),
}
for folder in ts_folders.values():
    os.makedirs(folder, exist_ok=True)

# Load time series lengkap
df_ts = pd.read_csv(ts_input, dtype={"SKU": str})
df_ts["SKU"]  = df_ts["SKU"].str.zfill(8)
df_ts["Date"] = pd.to_datetime(df_ts["Date"])
print(f"Time series loaded: {len(df_ts):,} baris")

# Tambah kolom Weekend (Sabtu=5, Minggu=6 -> 1, selain itu 0)
df_ts["Weekend"] = df_ts["Date"].dt.dayofweek.isin([5, 6]).astype(int)
print(f"  Weekend rows: {df_ts['Weekend'].sum():,}")

# Load Promo & jadikan data harian (explode rentang Start_Date ke End_Date)
df_promo = pd.read_csv(promo_input, dtype={"SKU": str})
df_promo["SKU"] = df_promo["SKU"].str.zfill(8)
df_promo["Start_Date"] = pd.to_datetime(df_promo["Start_Date"])
df_promo["End_Date"]   = pd.to_datetime(df_promo["End_Date"])

# Explode range tanggal
df_promo["Date"] = [pd.date_range(s, e) for s, e in zip(df_promo["Start_Date"], df_promo["End_Date"])]
df_promo_daily = df_promo.explode("Date")[["Store", "SKU", "Date"]].drop_duplicates()
df_promo_daily["Promo"] = 1
print(f"Promo data loaded : {len(df_promo_daily):,} kombinasi unik (Store, SKU, Date)")

# Merge kolom promo ke time series
df_ts = df_ts.merge(df_promo_daily, on=["Store", "SKU", "Date"], how="left")
df_ts["Promo"] = df_ts["Promo"].fillna(0).astype(int)
print(f"  Active promo rows: {df_ts['Promo'].sum():,}")

for dept in ["FRUIT", "VEGETABLE"]:
    print(f"\n{'='*50}")
    print(f"  {dept}")
    print(f"{'='*50}")

    # Load ABC mapping untuk dept ini
    abc_path = os.path.join(by_abc_folder, f"dataset_{dept}_ABC.csv")
    df_abc   = pd.read_csv(abc_path, dtype={"SKU": str})
    df_abc["SKU"] = df_abc["SKU"].str.zfill(8)
    abc_map  = df_abc[["Store", "SKU", "ABC"]].drop_duplicates()
    print(f"  ABC map: {len(abc_map):,} entri")

    # Filter time series untuk dept ini
    df_dept = df_ts[df_ts["Dept Name"] == dept].copy()

    # Merge ABC
    df_dept = df_dept.merge(abc_map, on=["Store", "SKU"], how="left")
    unmatched = df_dept["ABC"].isna().sum()
    if unmatched > 0:
        print(f"  [WARN] {unmatched:,} baris tidak match (di-skip)")
    df_dept = df_dept.dropna(subset=["ABC"])

    # Split & simpan per kelas A/B/C
    out_folder = ts_folders[dept]
    for kelas in ["A", "B", "C"]:
        df_kelas = (
            df_dept[df_dept["ABC"] == kelas]
            .drop(columns=["ABC"])
            .sort_values(["Date", "Store", "SKU"])
            .reset_index(drop=True)
        )
        out_path = os.path.join(out_folder, f"timeseries_{kelas}.csv")
        df_kelas.to_csv(out_path, index=False)
        print(f"  [OK] Kelas {kelas}: {len(df_kelas):,} baris -> timeseries_{kelas}.csv")

print(f"\n[INFO] Finished!")
print(f"   FRUIT     -> {ts_folders['FRUIT']}")
print(f"   VEGETABLE -> {ts_folders['VEGETABLE']}")
