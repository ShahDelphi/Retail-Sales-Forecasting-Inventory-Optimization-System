import os
import pandas as pd

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR   = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\promotion discount"
INPUT_CSV  = os.path.join(BASE_DIR, "combined", "promotion_discount.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "combined", "promotion_discount_clean.csv")

# Kode store yang diambil (1001 - 1013)
STORE_CODES = [str(code) for code in range(1001, 1014)]

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def clean_data(input_csv, output_csv):
    print(f"\n{'='*60}")
    print(f" DATA CLEANING")
    print(f"{'='*60}")
    print(f" Input  : {input_csv}")
    print(f" Output : {output_csv}")
    print(f"{'='*60}\n")

    # Read CSV
    df = pd.read_csv(input_csv, dtype=str)
    print(f" Total rows awal  : {len(df):,}")
    print(f" Kolom awal       : {list(df.columns)}\n")

    # ── 1. Hapus kolom PAGE_NUM ───────────────────────────────────────────────
    if "PAGE_NUM" in df.columns:
        df = df.drop(columns=["PAGE_NUM"])
        print(f" [OK] Kolom 'PAGE_NUM' berhasil dihapus.")
    else:
        print(f" [INFO] Kolom 'PAGE_NUM' tidak ditemukan, dilewati.")

    # ── 2. Filter berdasarkan kode STORE ─────────────────────────────────────
    # Kolom STORE berisi format seperti "1001 AEON BSD CITY"
    # Ambil kode di awal string (4 digit pertama)
    print(f"\n Filter STORE kode: {STORE_CODES}")

    before = len(df)
    df["STORE"] = df["STORE"].str.strip().str[:4]  # ambil kode numerik saja
    df = df[df["STORE"].isin(STORE_CODES)]
    after = len(df)

    print(f" [OK] Baris sebelum filter : {before:,}")
    print(f" [OK] Baris setelah filter : {after:,}")
    print(f" [OK] Baris dihapus        : {before - after:,}")

    # ── 3. Preview distribusi store ──────────────────────────────────────────
    print(f"\n Distribusi data per Store (kode):")
    store_counts = df["STORE"].value_counts().sort_index()
    for store, count in store_counts.items():
        print(f"   Store {store} : {count:,} rows")

    # ── 4. Filter kolom dan Rename ────────────────────────────────────────────
    # Sisakan hanya: SHORT_SK, STORE, EFFECTIVE, ENDING
    cols_mapping = {
        "SHORT_SKU": "SKU",
        "STORE": "Store",
        "EFFECTIVE_DATE": "Start_Date",
        "ENDING_DATE": "End_Date"
    }
    # Pastikan ambil kolom yang ada
    available_cols = [c for c in cols_mapping.keys() if c in df.columns]
    df = df[available_cols]
    df = df.rename(columns=cols_mapping)

    # ── 5. Hapus baris yang kosong (misal End_Date) ───────────────────────────
    before_drop = len(df)
    df = df.replace(r'^\s*$', pd.NA, regex=True) # ubah string kosong jadi pd.NA
    df = df.dropna()                             # drop baris yang ada pd.NA
    after_drop = len(df)
    print(f"\n [OK] Baris kosong dihapus : {before_drop - after_drop:,} rows")

    # ── 6. Simpan ─────────────────────────────────────────────────────────────
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"\n Kolom akhir      : {list(df.columns)}")
    print(f" Total rows akhir : {len(df):,}")
    print(f"\n{'='*60}")
    print(f" [SELESAI] File disimpan ke:")
    print(f"  {output_csv}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    clean_data(INPUT_CSV, OUTPUT_CSV)
