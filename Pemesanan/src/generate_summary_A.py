"""
GENERATE SUMMARY SOLUSI A
Membaca hasil simulasi (CSV) dan menghasilkan laporan Excel
dengan persentase Waste & Lost Sale per Dept, SKU, Store.

Jalankan setelah simulasi_solusi_A.py selesai.
"""
import pandas as pd
import numpy as np
import os

DIR_OUTPUT    = r"d:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\output"
FILE_CSV      = os.path.join(DIR_OUTPUT, "Solusi_A_PerStore_Filter.csv")
FILE_XLSX     = os.path.join(DIR_OUTPUT, "Solusi_A_Summary_WasteLost.xlsx")
WASTE_THRESHOLD = 8.0   # <= nilai ini dianggap bagus (%)


def _pct(df, num_col, den_col):
    """Hitung persentase num/den * 100, aman terhadap pembagi 0."""
    return np.where(df[den_col] > 0,
                    (df[num_col] / df[den_col] * 100).round(2), 0.0)


def _status(series, threshold=WASTE_THRESHOLD):
    """Beri label status berdasarkan threshold."""
    return np.where(series <= threshold, 'Bagus (<=8%)', 'Perlu Perhatian (>8%)')


def build_summary_dept(df):
    g = df.groupby(['Dept', 'Dept Name'], as_index=False).agg(
        Total_Actual_Qty   = ('Actual_SKU',        'sum'),
        Total_Sales_Rp     = ('Sales_Rupiah',      'sum'),
        Total_OpenStock    = ('Opening_Stock',      'sum'),
        Total_Waste_Qty    = ('Waste_Kadaluwarsa',  'sum'),
        Total_Waste_Rp     = ('Waste_Rupiah',       'sum'),
        Total_LostSale_Qty = ('Lost_Sale',          'sum'),
        Total_LostSale_Rp  = ('LostSale_Rupiah',    'sum'),
        Total_Order        = ('Order',              'sum'),
        Total_Deliver      = ('Deliver',            'sum'),
        Jumlah_SKU         = ('SKU',                'nunique'),
        Jumlah_Store       = ('Store',              'nunique'),
    )
    g['Waste_Pct']        = _pct(g, 'Total_Waste_Rp',    'Total_Sales_Rp')
    g['LostSale_Pct']     = _pct(g, 'Total_LostSale_Rp', 'Total_Sales_Rp')
    g['Status_Waste']     = _status(g['Waste_Pct'])
    g['Status_LostSale']  = _status(g['LostSale_Pct'])
    return g.sort_values('Dept').reset_index(drop=True)


def build_summary_dept_class(df):
    g = df.groupby(['Dept', 'Dept Name', 'Class'], as_index=False).agg(
        Total_Actual_Qty   = ('Actual_SKU',        'sum'),
        Total_Sales_Rp     = ('Sales_Rupiah',      'sum'),
        Total_OpenStock    = ('Opening_Stock',      'sum'),
        Total_Waste_Qty    = ('Waste_Kadaluwarsa',  'sum'),
        Total_Waste_Rp     = ('Waste_Rupiah',       'sum'),
        Total_LostSale_Qty = ('Lost_Sale',          'sum'),
        Total_LostSale_Rp  = ('LostSale_Rupiah',    'sum'),
        Jumlah_SKU         = ('SKU',                'nunique'),
    )
    g['Waste_Pct']        = _pct(g, 'Total_Waste_Rp',    'Total_Sales_Rp')
    g['LostSale_Pct']     = _pct(g, 'Total_LostSale_Rp', 'Total_Sales_Rp')
    g['Status_Waste']     = _status(g['Waste_Pct'])
    g['Status_LostSale']  = _status(g['LostSale_Pct'])
    return g.sort_values(['Dept', 'Class']).reset_index(drop=True)


def build_summary_sku(df):
    g = df.groupby(
        ['SKU', 'SKU DESC', 'Dept', 'Dept Name', 'Category', 'Class',
         'Shelf_Life', 'Lead_Time', 'Review_Period'],
        as_index=False
    ).agg(
        Total_Forecast     = ('Forecast_SKU',      'sum'),
        Total_Actual_Qty   = ('Actual_SKU',        'sum'),
        Total_Sales_Rp     = ('Sales_Rupiah',      'sum'),
        Total_OpenStock    = ('Opening_Stock',      'sum'),
        Total_Waste_Qty    = ('Waste_Kadaluwarsa',  'sum'),
        Total_Waste_Rp     = ('Waste_Rupiah',       'sum'),
        Total_LostSale_Qty = ('Lost_Sale',          'sum'),
        Total_LostSale_Rp  = ('LostSale_Rupiah',    'sum'),
        Total_Order        = ('Order',              'sum'),
        Total_Deliver      = ('Deliver',            'sum'),
        Jumlah_Hari        = ('Date',               'count'),
        Jumlah_Store       = ('Store',              'nunique'),
    )
    g['Waste_Pct']    = _pct(g, 'Total_Waste_Rp',    'Total_Sales_Rp')
    g['LostSale_Pct'] = _pct(g, 'Total_LostSale_Rp', 'Total_Sales_Rp')
    return g.sort_values('Class').reset_index(drop=True)


def build_summary_store(df):
    g = df.groupby(['Store', 'Class'], as_index=False).agg(
        Total_Forecast     = ('Forecast_SKU',      'sum'),
        Total_Actual_Qty   = ('Actual_SKU',        'sum'),
        Total_Sales_Rp     = ('Sales_Rupiah',      'sum'),
        Total_OpenStock    = ('Opening_Stock',      'sum'),
        Total_Waste_Qty    = ('Waste_Kadaluwarsa',  'sum'),
        Total_Waste_Rp     = ('Waste_Rupiah',       'sum'),
        Total_LostSale_Qty = ('Lost_Sale',          'sum'),
        Total_LostSale_Rp  = ('LostSale_Rupiah',    'sum'),
        Total_Order        = ('Order',              'sum'),
        Total_Deliver      = ('Deliver',            'sum'),
        Jumlah_SKU         = ('SKU',                'nunique'),
    )
    g['Waste_Pct']        = _pct(g, 'Total_Waste_Rp',    'Total_Sales_Rp')
    g['LostSale_Pct']     = _pct(g, 'Total_LostSale_Rp', 'Total_Sales_Rp')
    g['Status_Waste']     = _status(g['Waste_Pct'])
    g['Status_LostSale']  = _status(g['LostSale_Pct'])
    return g.sort_values(['Store', 'Class']).reset_index(drop=True)


def build_summary_sku_store(df):
    g = df.groupby(
        ['SKU', 'SKU DESC', 'Class', 'Store', 'Shelf_Life', 'Review_Period'],
        as_index=False
    ).agg(
        Total_Actual_Qty   = ('Actual_SKU',        'sum'),
        Total_Sales_Rp     = ('Sales_Rupiah',      'sum'),
        Total_OpenStock    = ('Opening_Stock',      'sum'),
        Total_Waste_Qty    = ('Waste_Kadaluwarsa',  'sum'),
        Total_Waste_Rp     = ('Waste_Rupiah',       'sum'),
        Total_LostSale_Qty = ('Lost_Sale',          'sum'),
        Total_LostSale_Rp  = ('LostSale_Rupiah',    'sum'),
    )
    g['Waste_Pct']    = _pct(g, 'Total_Waste_Rp',    'Total_Sales_Rp')
    g['LostSale_Pct'] = _pct(g, 'Total_LostSale_Rp', 'Total_Sales_Rp')
    return g.sort_values(['Class', 'SKU', 'Store']).reset_index(drop=True)


def generate_summary():
    print(f"Membaca CSV: {FILE_CSV}")
    df = pd.read_csv(FILE_CSV, parse_dates=['Date'])
    print(f"  Total baris: {len(df):,} | SKU: {df['SKU'].nunique():,} | Store: {df['Store'].nunique()}")

    print("\nMembangun summary...")
    grp_dept       = build_summary_dept(df)
    grp_dept_class = build_summary_dept_class(df)
    grp_sku        = build_summary_sku(df)
    grp_store      = build_summary_store(df)
    grp_sku_store  = build_summary_sku_store(df)

    print(f"Menyimpan Excel: {FILE_XLSX}")
    with pd.ExcelWriter(FILE_XLSX, engine='openpyxl') as writer:
        grp_dept.to_excel(writer,       sheet_name='Summary_Dept',       index=False)
        grp_dept_class.to_excel(writer, sheet_name='Summary_Dept_Class', index=False)
        grp_sku.to_excel(writer,        sheet_name='Summary_SKU',        index=False)
        grp_store.to_excel(writer,      sheet_name='Summary_Store',      index=False)
        grp_sku_store.to_excel(writer,  sheet_name='Summary_SKU_Store',  index=False)

    print(f"  Sheet 'Summary_Dept'      : {len(grp_dept):,} baris  (threshold <= {WASTE_THRESHOLD}%)")
    print(f"  Sheet 'Summary_Dept_Class': {len(grp_dept_class):,} baris")
    print(f"  Sheet 'Summary_SKU'       : {len(grp_sku):,} baris")
    print(f"  Sheet 'Summary_Store'     : {len(grp_store):,} baris")
    print(f"  Sheet 'Summary_SKU_Store' : {len(grp_sku_store):,} baris")

    # Tampilkan dept yang perlu perhatian
    buruk = grp_dept[grp_dept['Waste_Pct'] > WASTE_THRESHOLD][['Dept Name', 'Waste_Pct']]
    if not buruk.empty:
        print(f"\n[!] Dept dengan Waste_Pct > {WASTE_THRESHOLD}%:")
        for _, r in buruk.iterrows():
            print(f"     {str(r['Dept Name'])[:30]:<30} -> {r['Waste_Pct']:.2f}%")
    else:
        print(f"\n[OK] Semua Dept sudah di bawah threshold {WASTE_THRESHOLD}% waste!")

    print("\nSelesai!")


if __name__ == "__main__":
    generate_summary()
