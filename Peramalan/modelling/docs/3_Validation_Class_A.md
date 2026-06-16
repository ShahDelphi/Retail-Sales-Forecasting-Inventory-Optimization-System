# 📚 Dokumentasi: Uji Tes Skrip `validation_class_A.py`

## 1. Deskripsi Umum Skrip
Sebagai nyawa dari bab metodologi penelitian Tesis (*Bab Analitik Data*), `validation_class_A.py` bekerja layaknya wasit "Ujian Saringan" performa ketiga *machine learning*. Skrip ini memotong/menyembunyikan **30 data hari transaksi terakhir** asli di riwayat Supermarket (seolah membutakan mata mesin tebaknya), dan diadu "Apakah tebakan mesin dari hari 0 hingga sebelum -30 mirip dengan kejadian harian aslinya 30 hari ini?".

## 2. Metodologi *Hold-out Validation* Tesis
Sistem ini menggunakan teknik standard industri yakni **Train-Test Split (Hold-out method):**
*   **`train_df` (Data Latih):** Data dari sejarah awal 2 tahun ke belakang hingga (-30) hari terakhir dipakai mesin belajar ritme kurva supermarket.
*   **`test_df` (Data Uji):** 30 Hari murni data transaksi sesungguhnya bulan terbaru milik supermarket sebagai rahasia kunci tes *(Ground-Truth Validasi)*.

## 3. Komparasi Tiga Kompetitor Algoritma (Dual-Target)
Skrip validation kelas elit `A` ini menandingkan langsung 3 algoritma pamungkas Anda:
1. Model Basis **SARIMAX.**
2. Model Modern Jaringan Saraf tiruan **LSTM.**
3. Skema Kawin Silang Model **Hybrid SARIMAX-LSTM.**

**Proses Pengujian (*Sesi Dual-Loop*):** Ujian perbandingan 3 arsitektur dilarikan berulang 2 kali. (1) Khusus menguji tebakan **Nilai Rupiah Asli (`Sales`)** ditarung kesesuaiannya vs angka riil 30 hari, lalu masuk ke Ujian (2) Khusus menguji prediksi model vs **volume barang konvensional (`Sales Qty`)** riil 30 harinya.

## 4. Rekaman Evaluasi Error Rate (Hitungan Rapor Model)
Tingkat kehebatan prediksi model dikuantifikasi menggunakan Metrik Numerik absolut:
1. **`MAPE` (Mean Absolute Percentage Error)**: Kesalahan persentase (Contoh: seberapa melenceng % tebakan uang terhadap kasir asli). 
2. **`MAE` (Mean Absolute Error)**: Kerugian meleset dalam angka rupiah rata-rata sesungguhnya per hari.
3. **`RMSE` (Root Mean Squared Error)**: Skor pinalti ganda jika kebetulan model anda meramal selisih terlalu ekstrem di hari besar. 

## 5. Output Analitik Tesis
Hasil akhir dieksekusi diam-diam tanpa merubah data operasional, dan dieksekusi menelurkan aset ilmiah ke dalam foder `validation_output/`:
1.  **Rekap Excel Performa:** `opt_validation_metrics_summary.csv` (Daftar tabel MAPE, RMSE yang siap ditarik ke Bab Laporan Tesis Tulis Anda).
2.  **Peta Grafik Tren Prediksi (Grafik `.png`)**: Visual hitam-putih elegan (semua garis perbandingan tebakan diletakkan terpasang melilit Kurva Hitam Tebal Data "Aktual/Nyata"). Sangat meyakinkan masuk Draf final!
