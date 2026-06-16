# (v1)preprocessing - Data Preprocessing Workflow

**Created:** May 17, 2026  
**Purpose:** Production-ready files untuk preprocessing data sales (preprocessing, cleaning, ABC analysis)

---

## 📁 Struktur Folder

### Python Scripts (Core Workflow)
1. **sales_clean.py** - Initial cleaning dari raw sales data
2. **combined.py** - Menggabungkan cleaned sales files → `final_dataset.csv`
3. **not-null_clean.py** - Remove zero sales → `final_dataset_clean.csv`
4. **ABC_analysist.py** - ABC classification analysis
5. **time-series-dataset.py** - Generate time-series datasets untuk modelling
6. **split-dataset-by-dept.py** - Split dataset by department

### Data Folders

#### 📂 sales_clean/ (498.80 MB, 25 files)
- Cleaned sales data dari berbagai source files
- File format: `clean_YYYYMMDD_HHMMSS_MR_TotalSalesByDayBySKU_*.csv`
- Contains: Date, Store, SKU, SKU Name, Dept, Dept Name, Category, Sales, Sales Qty
- **Combined output:** `all_sales_clean.csv`

#### 📂 fix_data-sales/ (577.15 MB, 3 files)
- Intermediate dataset hasil dari combined.py
- **Files:**
  - `final_dataset.csv` - Gabungan semua sales_clean files
  - `final_dataset.xlsx` - Excel version
  - `final_dataset_sample.xlsx` - Sample untuk preview

#### 📂 new-dataset/ (1,167.59 MB, 29 files)
- Final cleaned datasets
- **Key files:**
  - `final_dataset_clean.csv` - Final dataset (zero sales removed)
  - `abc_summary_per_sku.csv` - ABC classification per SKU
  - `final_dataset_abc.csv` - Dataset with ABC classification
  - `split-dataset/` - Split by department

#### 📂 promo/ (0.54 MB, 1 file)
- `promotion_discount_clean.csv` - Promotion discount data

### Reference Files
- **cols.txt** - Column reference

---

## 🔄 Workflow Sequence

```
1. sales_clean.py
   └─> Membersihkan raw sales data
   └─> Output: sales_clean/*.csv

2. combined.py
   └─> Menggabungkan semua files di sales_clean/
   └─> Output: fix_data-sales/final_dataset.csv

3. not-null_clean.py
   └─> Remove rows dengan Sales = 0
   └─> Output: new-dataset/final_dataset_clean.csv

4. ABC_analysist.py
   └─> ABC classification analysis
   └─> Output: new-dataset/abc_summary_per_sku.csv
   └─> Output: new-dataset/final_dataset_abc.csv

5. time-series-dataset.py
   └─> Generate time-series datasets untuk modelling
   └─> Output: timeseries_A.csv, timeseries_B.csv, timeseries_C.csv
   └─> (Output ke folder modelling/dataset/time-series/)

6. split-dataset-by-dept.py
   └─> Split dataset by department
   └─> Output: new-dataset/split-dataset/
```

---

## 📊 Data Specifications

**Date Range:** January 2024 - December 2025 (24 months)  
**Stores:** 12 stores (IDs: 1001-1012)  
**Departments:** 2 (FRUIT: 2038, VEGETABLE: 2037)  
**ABC Classification:** A (70%), B (70-90%), C (90-100%)

**Final Dataset Stats:**
- Rows: 2,950,134
- Columns: 9 (Date, Store, SKU, SKU Name, Dept, Dept Name, Category, Sales, Sales Qty)
- Size: ~245 MB

---

## ⚠️ Important Notes

### September 2025 Correction (May 17, 2026)
- Ditemukan duplikasi data September 2025 (2x lipat)
- Root cause: 2 source files identical (clean_20260322_122705 & clean_20260322_122747)
- **Fix:** Deleted duplicate file, regenerated all datasets
- **Verified:** September 2025 = Rp 36.03B (normal, not Rp 72B)

### Files NOT Included (Debug/Temporary)
File-file debugging ini TIDAK dimasukkan ke (v1)preprocessing:
- check-september-2025.py
- compare-duplicate-files.py
- compare-monthly-sales.py
- detail-september-duplicate.py
- regenerate-all-sales-clean.py
- trace-september-source.py
- verify-modelling-september.py
- cek-duplicate.py
- check_dataType.py
- backup/ folder
- sales_clean-manual/ folder
- preprocessing_data-sales.rar (old archive)
- all_sales_clean.csv (duplicate file)

---

## 📦 Archive Information

**Total Size:** 2,244.11 MB (≈ 2.19 GB)  
**Total Files:** 65 files  
**Ready for:** RAR archiving

**Recommended RAR command:**
```powershell
# From: d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\
rar a -m5 -rr3p -ag+YYYYMMDD "(v1)preprocessing.rar" "(v1)preprocessing"
```

---

**Last Updated:** May 17, 2026  
**Status:** ✅ Production Ready - All September 2025 corrections applied
