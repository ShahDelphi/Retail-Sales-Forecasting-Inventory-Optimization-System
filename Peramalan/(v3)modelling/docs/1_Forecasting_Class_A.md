# 📚 Dokumentasi: Skrip `forecasting_class_A.py`

## 1. Deskripsi Umum Skrip
Skrip `forecasting_class_A.py` adalah jantung pertahanan analisis penjualan tingkat tinggi/primer (`Kelas A`) di departemen buah dan sayur Anda. Barang-barang di kelas ini dianggap memiliki *demand* (permintaan) yang tinggi dan sering berfluktuasi secara tidak terduga, sehingga model matematis yang sangat cerdas diaktifkan untuk mempelajarinya. Skrip ini bertugas memprediksi angka penjualan/kuantitas operasional *live* 30 hari penuh ke depan.

## 2. Model Algoritma yang Digunakan (*Triple Architecture*)
Skrip ini merancang tiga mesin pembelajar mesin (*Machine Learning*) sekaligus dan mengeksekusinya secara bergantian (*ensemble*):
1. **SARIMAX (Seasonal AutoRegressive Integrated Moving Average with eXogenous variables):** Model stokastik klasik untuk menangkap pola linear stabil mingguan (Seasonal 7-harian).
2. **LSTM (Long Short-Term Memory):** Jaringan saraf turunan *Deep Learning* (Keras/TensorFlow) untuk mengekstrak kerumitan/lonjakan nonlinear pada transaksi yang tak terbaca SARIMAX.
3. **Hybrid Model (SARIMAX + LSTM):** Menggabungkan SARIMAX dan LSTM; SARIMAX menebak tebakan kasarnya, dan LSTM menyapu residu tebakan kasarnya (selisih keteledoran SARIMAX) sehingga akurasinya diklaim menjadi yang terbaik.

## 3. Fitur Utama & Keunggulan Rekayasa

*   **Pola Dual-Target (Target Ganda):** Mesin akan berputar (loop) melatih 3 jenis model di atas untuk mencari nilai **`Sales`** (dalam Nominal Rupiah) terlebih dahulu. Jika selesai, model men-_reset_ ingatannya dan melatih ulang khusus menebak **`Sales Qty`** (Kuantitas Jumlah Fisik/Berat).
*   **Cyclic Encoding (LSTM Bionic):** Keras LSTM disuplai dengan fitur *Trigonometri Cos-Sin* peredaran hari (Senin = 0, Minggu = 6) sehingga siklus psikologi belanja akhir pekan mudah dikenali jaringan saraf model.
*   **Distribusi Top-Down Berbasis SKU:** Data *sales* yang diolah bukan harian per SKU (agar tak terjadi tebakan kacau karena banyak *noise* angka 0), namun seluruh SKU dikumpulkan omsetnya dan diramal secara makro-kelas. Data makro yang tercetak kemudian disebarkan pecahan nilai-nya ke tiap-tiap nama *SKU item* (seperti Apel A, Apel B) berdasar `Proportion_Sales` & `Proportion_Qty` historis masing-masing (pendekatan *Top-Down Distribution*).

## 4. Variabel Eksogen Masukan (*Features*)
Model diawasi pengaruh kuat 3 fitur bantuan (*Exogenous Variables*):
*   **`Weekend`**: Indikator *binary* (1 untuk Sabtu-Minggu).
*   **`Holiday`**: Indikator kalender nyata libur nasional region-ID (Indonesia API).
*   **`Promo`**: Fitur biner promosi diskon per masa harian sesuai dataset mentah riwayat supermarket ritel Anda.

## 5. Parameter Eksekusi & Output Tesis
*   `HORIZON = 30`: Menetapkan mesin menerawang masa depan sejauh 30 hari batas ke depan.
*   `LOOKBACK = 14`: Jendela riwayat LSTM melirik tren 14 hari transaksi terakhir untuk menentukan besok.
*   **Output File Akhir:** Memuncratkan berkas `forecast_{dept}_class_A.csv` ke dalam foder `forecast_output/` yang isinya memplot ratusan baris lengkap prediksi *Sales* (Pembulatan desimal Mutlak) dan *Qty* (Berdesimal rapi) untuk dibaca laporan Streamlit esok harinya.
