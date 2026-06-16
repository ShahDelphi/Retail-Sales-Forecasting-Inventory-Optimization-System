# 📚 Dokumentasi Pipeline Peramalan Berbasis ABC Analysis (Dual-Target)

Direktori ini berisi serangkaian *script* (kode program) Python yang membentuk aliran (*pipeline*) utama dari eksperimen **Tesis Peramalan Penjualan Ritel**. Sistem ini dirancang secara spesifik untuk memisahkan algoritma prediksi berdasarkan klasifikasi barang (Analisis ABC) serta mengkalkulasi dua target operasional secara mandiri: **Sales Amount (Nominal Uang/Rupiah)** dan **Sales Qty (Kuantitas Jumlah Unit/Berat)**.

---

## 🏗️ 1. Arsitektur File Sistem

Terdapat 5 komponen utama (file `.py`) di dalam *folder* `modelling/` ini:

| Nama File | Fungsi dan Deskripsi |
| :--- | :--- |
| `forecasting_class_A.py` | Mengeksekusi peramalan 30 hari ke depan untuk barang Kelas A (Fokus Utama/High-Demand). Menggunakan *triple-architecture*: **SARIMAX**, **Deep Learning (LSTM)**, dan **Hybrid SARIMAX-LSTM**. |
| `forecasting_class_BC.py` | Mengeksekusi peramalan 30 hari ke depan untuk barang Kelas B & C (Medium & Slow-Moving). Hanya menggunakan mesin **SARIMAX** murni karena pola fluktuasi transaksinya lebih linear dan model DL (Deep Learning) rentan *overfitting*. |
| `validation_class_A.py` | Skrip uji validasi *Hold-out* (menyembunyikan 30 hari terakhir data aktual untuk dites melawan tebakan mesin). Mengeluarkan kalkulasi metrik *Error* untuk Kelas A (SARIMAX, LSTM, Hybrid). |
| `validation_class_BC.py` | Skrip uji validasi *Hold-out* spesifik menghitung metrik *Error* untuk Kelas B dan C menggunakan SARIMAX saja. |
| `visualisation/app.py` | Layar visualisasi antarmuka aplikasi (*Dashboard* Tesis) modular standar industri untuk menampilkan analisis tren, kategori produk, performa toko, dan evaluasi model. |


---

## 🧠 2. Metodologi (Keunggulan Rekayasa Algoritma)

### A. Strategi Dual-Target
Setiap kali skrip berjalan, mesin dirakit untuk mengerjakan "dua sesi tugas (*looping*)":
1. **Fase Sales:** Menghitung prediksi Nominal `Sales` Rupiah. Hasil pendistribusian ke tabel CSV diotomatisasi dengan perintah pembulatan mutlak `int(round(...))` (karena uang ritel tidak mungkin recehan koma kecil).
2. **Fase Qty:** Menghapus memori sementaranya dan *training* ulang untuk menebak `Sales Qty`. Hasil tebakan Qty sengaja dibiarkan menyisakan desimal (`round(..., 2)`) karena barang supermarket fisik seperti buah dan sayur (Kg/Gram) sangat lazim dipecah (misal: tebakan laku 1.45 Kg). 

### B. Distribusi Proporsi Cerdas (Top-Down Approach)
Untuk menghindari peramalan "buta" karena data *noise* yang terlalu liar di tingkat per SKU harian, skrip ini menganut teknik:
1. Menjumlahkan total omset 1 Departemen-Kelas menjadi *"Super-Grafik Kelas"*.
2. Memasukkan *"Super-Grafik Kelas"* tersebut ke mesin pintar (SARIMAX/LSTM) agar menangkap perilaku pembelinya.
3. Setelah total harian kelas masa depan ditebak, nilainya **dipecah / didistribusikan** kembali menukik turun ke level SKU berdasarkan bobot historis historis spesifik SKU tersebut.
   * `Proportion_Sales` = Nilai Rupiah barang ini / Total Rupiah 1 Kelas.
   * `Proportion_Qty` = Kuantitas berat barang ini / Total Berat 1 Kelas.

*(Dengan pemecahan formula ini, SKU yang terjual murah namun volumenya berat seperti Semangka tetap mendapatkan ganjaran distribusi prediksinya secara berkeadilan).*

### C. Variabel Penunjang Terintegrasi (Eksogenitas Multivariat)
Pada Kelas A, B, maupun C, skrip telah direkayasa agar dapat membaca secara seragam:
- **Weekend:** Sabtu & Minggu otomatis jadi angka referensi kuat algoritma.
- **Promo:** Kalender promosi retail yang tertera di CSV dimasukkan sebagai *booster* tebakan.
- **Holiday (Modul Library Indonesia):** Mendeteksi Hari Jadi Nasional, Imlek, Idul Fitri, Lebaran dsb secara riil berbekal library `holidays`.

---

## 🚀 3. Eksekusi (*How to Run*)

### A. Membuka Aplikasi Output
Untuk melihat gambaran prediksi final dalam antarmuka UI interaktif terbaik, jalankan perintah ini di VS Code atau Terminal Anda:
```bash
streamlit run visualisation/app.py
```

*(Anda dapat menekan tombol toogle **"Target"** di aplikasi untuk me-_refresh_ grafik seketika dari mode Rupiah menjadi target Kuantitas Barang).*

### B. Merekap Ulang Skor Metrik Validasi (MAPE / RMSE)
Untuk mencetak gambar grafik dan tabel komparasi error 3 model:
```bash
python validation_class_A.py
python validation_class_BC.py
```
*(Outputnya akan bermuara pada folder `/validation_output` berupa metrik .csv dan tangkapan grafik model `.png`)*.

### C. Men-_Generate_ CSV Prediksi Terbaru
Jika Anda merasa terdapat data CSV sumber (/time-series) yang baru atau berubah:
```bash
python forecasting_class_A.py
python forecasting_class_BC.py
```
*(Outputnya akan menjatuhkan CSV Prediksi ke folder `/forecast_output` yang dibaca secara pasif oleh Streamlit nantinya).*
