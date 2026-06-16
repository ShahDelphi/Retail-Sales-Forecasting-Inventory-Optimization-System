"""
SOLUSI A: Simulasi Per-Store dengan Filter Baris Nol
Hanya menyimpan baris di mana toko tersebut benar-benar
menjual SKU tersebut (Forecast_SKU > 0 ATAU Actual_SKU > 0).
Output: ~490 ribu baris (bukan 4 juta)
"""
import pandas as pd
import numpy as np
import os
import math

DIR_DATASET = r"d:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\dataset"
DIR_OUTPUT  = r"d:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\output"
FILE_MASTER = os.path.join(DIR_DATASET, "Bab 4 - Praproses Pemesanan.xlsx")
FILE_HIST   = os.path.join(DIR_DATASET, "final_dataset_clean.csv")

if not os.path.exists(DIR_OUTPUT):
    os.makedirs(DIR_OUTPUT)

Z_SCOR = 1.28

# Mapping Shelf Life ke Periode Review (dari tabel Note sheet)
SHELF_TO_REVIEW = {
    1: 1, 2: 1, 3: 2, 4: 2, 5: 2,
    6: 3, 7: 3, 8: 3, 9: 3, 10: 3,
    14: 7, 21: 7, 30: 7,
    60: 14, 90: 30, 180: 30, 360: 30, 365: 30
}

def get_review_period(shelf_life):
    """Konversi shelf life ke periode review sesuai tabel mapping"""
    if shelf_life in SHELF_TO_REVIEW:
        return SHELF_TO_REVIEW[shelf_life]
    # Fallback: cari yang paling dekat
    elif shelf_life <= 2:
        return 1
    elif shelf_life <= 5:
        return 2
    elif shelf_life <= 10:
        return 3
    elif shelf_life <= 30:
        return 7
    elif shelf_life <= 60:
        return 14
    else:
        return 30


def run_simulation_solusi_a():
    # --- MASTER DATA ---
    print("Membaca Master Data...")
    df_master = pd.read_excel(FILE_MASTER, sheet_name='Master')
    df_note   = pd.read_excel(FILE_MASTER, sheet_name='Note')
    df_master = pd.merge(df_master, df_note, left_on='SHELFLIFE', right_on='Shelflife', how='left')
    df_master = df_master.dropna(subset=['SKU', 'MINOR', 'SALES', 'SHELFLIFE'])

    df_child = df_master[df_master['ITEM PARENT/CHILD'] == 'C'][['SKU', 'SKU PARENT']]
    child_to_parent = dict(zip(df_child['SKU'].astype(str), df_child['SKU PARENT'].astype(str)))

    print("Menggabungkan Sales Child ke Parent...")
    df_master['SALES'] = df_master.groupby('SKU PARENT')['SALES'].transform('sum')
    df_master = df_master[df_master['ITEM PARENT/CHILD'] != 'C'].reset_index(drop=True)

    # --- HISTORI & LOOKUP ---
    print("Membaca histori penjualan...")
    df_hist = pd.read_csv(FILE_HIST)
    df_hist['Date']  = pd.to_datetime(df_hist['Date'])
    df_hist['SKU']   = df_hist['SKU'].astype(str).map(lambda x: child_to_parent.get(x, x))
    df_hist['Store'] = df_hist['Store'].astype(str)
    df_hist['Month'] = df_hist['Date'].dt.month

    grp = df_hist.groupby(['SKU', 'Store', 'Month'], as_index=False).agg(
        Total_Sales=('Sales', 'sum'),
        Total_Qty=('Sales Qty', 'sum')
    )
    grp['Avg_Price'] = np.where(grp['Total_Qty'] > 0,
                                grp['Total_Sales'] / grp['Total_Qty'], np.nan)

    total_qty_sku        = grp.groupby('SKU')['Total_Qty'].transform('sum')
    grp['Store_Prop']    = (grp['Total_Qty'] / total_qty_sku.replace(0, np.nan)).fillna(0)

    all_stores = sorted(df_hist['Store'].unique())
    n_stores   = len(all_stores)

    avg_price_dict = {(r.SKU, r.Store, r.Month): r.Avg_Price for r in grp.itertuples()}
    store_prop_dict = {}
    for r in grp.itertuples():
        store_prop_dict.setdefault(r.SKU, {})[r.Store] = r.Store_Prop

    # --- ABC ANALYSIS ---
    print("Melakukan ABC Analysis...")
    df_master = df_master.sort_values('SALES', ascending=False).reset_index(drop=True)
    total_sales_all = df_master['SALES'].sum()
    df_master['Cum_Pct'] = df_master['SALES'].cumsum() / total_sales_all
    df_master['Class']   = df_master['Cum_Pct'].apply(
        lambda p: 'A' if p <= 0.70 else ('B' if p <= 0.90 else 'C'))

    # --- SIMULASI ---
    all_results = []
    for cls in ['A', 'B', 'C']:
        print(f"\n{'='*50}\nKelas {cls}\n{'='*50}")
        file_fc = os.path.join(DIR_DATASET, f"daily_forecast_class_{cls}.csv")
        if not os.path.exists(file_fc):
            continue

        df_class  = df_master[df_master['Class'] == cls].copy()
        df_class['Proporsi'] = df_class['SALES'] / df_class['SALES'].sum()
        df_forecast = pd.read_csv(file_fc)
        df_forecast['Date'] = pd.to_datetime(df_forecast['Date'])

        for _, row in df_class.iterrows():
            sku        = str(int(row['SKU']))
            desc       = row['SKU DESC']
            dept       = str(row['DEPT NAME']).lower()
            dept_code  = row['DEPT']
            dept_name  = row['DEPT NAME']
            category   = row['CATEGORY']
            moq        = row['MINOR']
            if pd.isna(moq) or moq <= 0:
                moq = 1
            else:
                moq = int(moq)
            shelf_life = int(row['SHELFLIFE'])
            lead_time  = int(row['LEAD TIME'])
            proporsi   = row['Proporsi']
            
            # Konversi shelf life ke periode review
            review_period = get_review_period(shelf_life)

            df_fc = df_forecast[df_forecast['Dept'] == dept].sort_values('Date').reset_index(drop=True)
            if df_fc.empty:
                continue

            n_days = len(df_fc)
            dates  = df_fc['Date'].values
            Forecast_AGG = (df_fc['Forecast_SalesQty'] * proporsi).round().astype(int).values
            Actual_AGG   = (df_fc['Actual_SalesQty']   * proporsi).round().astype(int).values

            # Pecah ke store - SIMULASI PER TOKO
            props = store_prop_dict.get(sku, {})
            if not props or sum(props.values()) == 0:
                props = {s: 1/n_stores for s in all_stores}
            total_prop = sum(props.values())
            props = {s: v/total_prop for s, v in props.items()}

            months = pd.to_datetime(dates).month
            store_rows = []
            Day_arr = np.arange(1, n_days + 1, dtype=int)

            for store in all_stores:
                sp = props.get(str(store), 0)
                if sp == 0:       # toko tidak pernah jual SKU ini -> skip
                    continue

                fc_s     = np.floor(Forecast_AGG * sp).astype(int)
                actual_s = np.floor(Actual_AGG * sp).astype(int)

                # *** FILTER: buang hari jika kedua-duanya 0 ***
                mask = (fc_s > 0) | (actual_s > 0)
                if mask.sum() == 0:
                    continue

                # Hitung store-level Error, Stdev, dan SS sebelum simulasi harian
                error_store = actual_s - fc_s
                stdev_s = np.std(error_store, ddof=1) if len(error_store) > 1 else 0
                stdev_s = 0 if (pd.isna(stdev_s) or math.isinf(stdev_s)) else round(stdev_s, 0)
                SS_s = round(Z_SCOR * stdev_s * math.sqrt(lead_time + review_period), 0)

                # Inisialisasi parameter simulasi lokal toko
                Opening_Aging_s = np.zeros(n_days)
                Order_s         = np.zeros(n_days)
                Deliver_s       = np.zeros(n_days)
                SL_arr_s        = np.zeros(n_days)
                Opening_Stock_s = np.zeros(n_days)
                Closing_Stock_s = np.zeros(n_days)
                Waste_s         = np.zeros(n_days)
                Lost_Sale_s     = np.zeros(n_days)
                Note_Order_arr  = []   # kapan order dilakukan
                Note_Waste_arr  = []   # kapan barang kadaluarsa

                # Seed random per SKU dan Store agar independen
                np.random.seed((int(sku) + int(store.replace('T-', ''))) % (2**31))

                # Opening Stock Awal (t=0) lokal toko
                fc_day0 = max(fc_s[0], 1)
                fc_low  = fc_day0 * 0.95
                fc_high = fc_day0 * 1.05
                fc_rand = np.random.uniform(fc_low, fc_high)
                coverage_days = min(review_period, shelf_life)
                initial_opening_stock = round(fc_rand * coverage_days)

                for t in range(n_days):
                    note_order = "Ya" if (Day_arr[t] % review_period) == 0 else "Tidak"
                    note_waste = "Ya" if (Day_arr[t] % shelf_life) == 0 else "Tidak"

                    Note_Order_arr.append(note_order)
                    Note_Waste_arr.append(note_waste)

                    if t == 0:
                        Opening_Aging_s[t] = initial_opening_stock
                    else:
                        Opening_Aging_s[t] = max(Closing_Stock_s[t-1], 0)
                    
                    SL_arr_s[t] = round(np.random.uniform(0.80, 1.00), 2)

                    # 1. Deliver_s[t]
                    if t < lead_time:
                        Deliver_s[t] = math.floor(fc_s[t] * SL_arr_s[t])
                    else:
                        order_date = t - lead_time
                        Deliver_s[t] = math.floor(Order_s[order_date] * SL_arr_s[t])

                    # 2. Opening_Stock_s[t]
                    Opening_Stock_s[t] = Opening_Aging_s[t] + Deliver_s[t]

                    # 3. Closing_Stock_s[t] & Lost_Sale_s[t] before adjustments
                    Closing_Stock_s[t] = max(Opening_Stock_s[t] - actual_s[t], 0)
                    Lost_Sale_s[t] = max(actual_s[t] - Opening_Stock_s[t], 0)

                    # 4. Waste_s[t] (tidak mengurangi Closing_Stock_s[t] di inventory flow sesuai Excel)
                    Waste_s[t] = round(Closing_Stock_s[t] * 0.3, 1) \
                                 if (Closing_Stock_s[t] > 0 and note_waste == "Ya") else 0

                    # 5. Order_s[t] (dihitung setelah Closing_Stock_s[t] didapat)
                    if note_order == "Ya":
                        forecast_sum = 0
                        for i in range(1, review_period + 1):
                            fc_idx = t + i
                            if fc_idx < n_days:
                                forecast_sum += fc_s[fc_idx]
                        Order_s[t] = math.ceil(max(0, SS_s + forecast_sum - Closing_Stock_s[t]) / moq) * moq
                    else:
                        Order_s[t] = 0

                # Ambil rata-rata harga toko
                avg_prices = np.array([
                    avg_price_dict.get((sku, str(store), int(m)), np.nan) for m in months])
                fallback = np.nanmedian(avg_prices) if not np.all(np.isnan(avg_prices)) else 0
                avg_prices = np.where(np.isnan(avg_prices), fallback, avg_prices)

                waste_qty_s    = np.round(Waste_s[mask], 1)
                lostsale_qty_s = np.round(Lost_Sale_s[mask]).astype(int)
                actual_qty_s   = actual_s[mask]
                avg_p          = np.round(avg_prices[mask], 2)

                # Nilai Rupiah
                waste_rp    = np.round(waste_qty_s    * avg_p, 0)
                lostsale_rp = np.round(lostsale_qty_s * avg_p, 0)
                sales_rp    = np.round(actual_qty_s   * avg_p, 0)

                # Persentase (basis: nilai Rupiah)
                waste_pct    = np.where(sales_rp > 0, np.round(waste_rp    / sales_rp * 100, 2), 0.0)
                lostsale_pct = np.where(sales_rp > 0, np.round(lostsale_rp / sales_rp * 100, 2), 0.0)

                sl_s = np.where(Deliver_s[mask] > 0, SL_arr_s[mask], np.nan)

                df_s = pd.DataFrame({
                    'SKU'              : sku,
                    'SKU DESC'         : desc,
                    'Dept'             : dept_code,
                    'Dept Name'        : dept_name,
                    'Category'         : category,
                    'Class'            : cls,
                    'Store'            : store,
                    'Date'             : pd.to_datetime(dates)[mask],
                    'Forecast_SKU'     : fc_s[mask],
                    'Actual_SKU'       : actual_qty_s,
                    'Avg_Price'        : avg_p,
                    'Sales_Rupiah'     : sales_rp,
                    'Minor_MOQ'        : moq,
                    'Z_Scor'           : Z_SCOR,
                    'Error'            : error_store[mask],
                    'Stdev'            : stdev_s,
                    'SS'               : SS_s,
                    'Opening_Aging'    : Opening_Aging_s[mask],
                    'Order'            : Order_s[mask],
                    'Deliver'          : Deliver_s[mask],
                    'SL'               : sl_s,
                    'Opening_Stock'    : Opening_Stock_s[mask],
                    'Closing_Stock'    : Closing_Stock_s[mask],
                    'Waste_Kadaluwarsa': waste_qty_s,
                    'Waste_Rupiah'     : waste_rp,
                    'Waste_Pct'        : waste_pct,
                    'Lost_Sale'        : Lost_Sale_s[mask],
                    'LostSale_Rupiah'  : lostsale_rp,
                    'LostSale_Pct'     : lostsale_pct,
                    'Shelf_Life'       : shelf_life,
                    'Lead_Time'        : lead_time,
                    'Review_Period'    : review_period,
                    'Day'              : Day_arr[mask],
                    'Note_Order'       : np.array(Note_Order_arr)[mask],
                    'Note_Waste'       : np.array(Note_Waste_arr)[mask],
                })
                store_rows.append(df_s)

            if store_rows:
                all_results.append(pd.concat(store_rows, ignore_index=True))

            sku_waste = sum(df_s['Waste_Kadaluwarsa'].sum() for df_s in store_rows)
            sku_lost  = sum(df_s['Lost_Sale'].sum() for df_s in store_rows)
            print(f"  > {desc[:25]:<25} | Stores aktif: {len(store_rows):>2} | "
                  f"Waste: {sku_waste:>5.1f} | Lost: {sku_lost:>5.1f}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df = final_df.sort_values(['SKU', 'Store', 'Date']).reset_index(drop=True)

        # --- Simpan CSV utama ---
        out_csv = os.path.join(DIR_OUTPUT, "Solusi_A_PerStore_Filter.csv")
        final_df.to_csv(out_csv, index=False)
        print(f"\nSelesai! Total baris: {len(final_df):,}")
        print(f"SKU: {final_df['SKU'].nunique():,} | Store: {final_df['Store'].nunique()}")
        print(f"Disimpan: {out_csv}")

        # --- Generate summary Excel (logika ada di generate_summary_A.py) ---
        from generate_summary_A import generate_summary
        generate_summary()


if __name__ == "__main__":
    run_simulation_solusi_a()

