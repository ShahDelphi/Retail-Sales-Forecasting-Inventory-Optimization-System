# 📚 Panduan Eksekusi Lengkap Pipeline Peramalan & Simulasi (Rerun)

Dokumen ini berisi panduan langkah-demi-langkah untuk menjalankan ulang seluruh pipeline, mulai dari data penjualan mentah (*raw sales*), pembersihan data, pemodelan, hingga simulasi persediaan (*inventory simulation*).

---

## 🏗️ Peta Aliran Data (Data Flow)
```
[Sales/ (CSV Mentah)] 
         │  (sales_clean.py)
         ▼
[sales_clean/all_sales_clean.csv] 
         │  (combined.py & not-null_clean.py)
         ▼
[new-dataset/final_dataset_clean.csv] 
         │  (remap_pipeline.py → Konversi T-01 s.d T-10)
         ▼
[split-dataset/ (Dept & ABC)] 
         │  (split-dataset-by-dept.py & ABC_analysist.py)
         ▼
[split-dataset/time-series/ (A/B/C)] 
         │  (time-series-dataset.py & Salin ke folder modelling)
         ▼
[modelling/dataset/time-series/]
         │  (validation_class_A/BC_oct-dec_2025.py)
         ▼
[daily_forecast_class_*.csv] 
         │  (Salin ke Pemesanan/dataset/)
         ▼
[simulasi_solusi_A.py & generate_formula_excel.py] 
         │
         ▼
[KPI Update & Simulasi_Formula_Visible.xlsx (Selesai)]
```

---

## 🚀 Langkah-Langkah Eksekusi

Jalankan perintah-perintah di bawah ini secara berturut-turut menggunakan Terminal pilihan Anda (Bash / Command Prompt / PowerShell):

### Bagian 1: Pembersihan & Pemrosesan Data (Preprocessing)

1.  **Masuk ke folder preprocessing**:
    ```bash
    cd D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales
    ```
2.  **Bersihkan dan gabungkan data penjualan mentah**:
    ```bash
    python sales_clean.py
    ```
3.  **Gabungkan dengan Master Item**:
    ```bash
    python combined.py
    ```
4.  **Hapus baris kosong (Sales & Qty = 0)**:
    ```bash
    python not-null_clean.py
    ```
5.  **Terapkan pemetaan Toko Baru (`T-01` s.d `T-10`)**:
    *(Script ini secara aman mengonversi nama toko pada dataset pemesanan & peramalan sekaligus)*
    ```bash
    python remap_pipeline.py
    ```
6.  **Pecah data per Departemen**:
    ```bash
    python split-dataset-by-dept.py
    ```
7.  **Jalankan Analisis ABC**:
    ```bash
    python ABC_analysist.py
    ```
8.  **Jalankan Pemisahan Deret Waktu (Time Series)**:
    ```bash
    python time-series-dataset.py
    ```
9.  **Salin file deret waktu hasil pemecahan ke folder Modelling** (Gunakan terminal PowerShell):
    ```powershell
    Copy-Item -Path "D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\time-series\*" -Destination "D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling\dataset\time-series\" -Recurse -Force
    ```

---

### Bagian 2: Pemodelan & Uji Validasi (Modelling)

10. **Masuk ke folder modelling**:
    ```bash
    cd D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling
    ```
11. **Jalankan model peramalan untuk periode validasi simulasi (Okt-Des 2025)**:
    *(Proses ini melatih model SARIMAX + LSTM dan menghasilkan file `daily_forecast_class_*.csv`)*
    ```bash
    python validation_class_A_oct-dec_2025.py
    python validation_class_BC_oct-dec_2025.py
    ```
12. **Salin hasil prediksi harian ke folder simulasi Pemesanan** (Gunakan terminal PowerShell):
    ```powershell
    Copy-Item -Path "D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling\validation_output_oct_dec_2025\class_A\daily_forecast_class_A.csv" -Destination "D:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\dataset\" -Force
    Copy-Item -Path "D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling\validation_output_oct_dec_2025\class_B\daily_forecast_class_B.csv" -Destination "D:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\dataset\" -Force
    Copy-Item -Path "D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling\validation_output_oct_dec_2025\class_C\daily_forecast_class_C.csv" -Destination "D:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\dataset\" -Force
    ```

---

### Bagian 3: Simulasi Persediaan & Pelaporan (Pemesanan)

13. **Masuk ke folder pemesanan**:
    ```bash
    cd D:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\src
    ```
14. **Jalankan Simulasi Inventory harian**:
    *(Mengkalkulasi Waste dan Lost Sales untuk toko T-01 s.d T-10)*
    ```bash
    python simulasi_solusi_A.py
    ```
15. **Perbarui rumus di file Excel visualisasi interaktif**:
    ```bash
    python generate_formula_excel.py
    ```

---
*Catatan: Parameter Z-Score saat ini dikonfigurasi pada **1.28** (setara dengan target Service Level 90%) untuk menekan Lost Sales di bawah 10% dengan tingkat Waste di bawah 4.4%.*
