# 📚 Dokumentasi: Skrip `forecasting_class_BC.py`

## 1. Deskripsi Umum Skrip
Skrip `forecasting_class_BC.py` dirancang khusus di tingkat lini kedua sistem peramalan Tesis. Skrip ini melayani barang penjualan beromset medium (`Kelas B`) dan produk pelengkap lambat atau mati laku (`Kelas C`). Karena tren historis kategori B & C jauh lebih stasioner, jarang lonjakan, dan memiliki riwayat data penjualan (0) yang sering, sistem prediksi diubah ke arah regresi klasik agar efisien tenaga dan lari dari ancaman *overfitting* *Deep Learning*.

## 2. Model Algoritma yang Digunakan (*Lightweight Model*)
*   **Single SARIMAX (Seasonal ARIMA):** Khusus skrip Kelas BC ini, mesin `LSTM` murni **DIMATIKAN**. Kita secara sadar mempercayakan sepenuhnya komando peramalan harian pada algoritma fungsi statistika SARIMAX *(Order 1,1,1) x (Seasonal 7-hari)*. Metode ini secara ilmiah diyakini jauh lebih stabil menangani kumpulan data retail lambat putar (*Slow Moving Inventory*).

## 3. Fitur Utama & Mekanisme Serupa
Meskipun algoritmanya disederhanakan dari Kelas A, fitur logis canggih Kelas A tetap kita hadirkan di B & C:
*   **Pola Dual-Target Murni:** Loop peramalan target menembak ganda; Model menebak arah **`Sales`** Rupiah, kemudian berganti shift menebak **`Sales Qty`** Fisik dengan presisi *float* 2 angka koma.
*   **Pendistribusian Makro -> Mikro:** Data awal tetap dijumlahkan *Total Sum* di level kelas (B / C) harian lalu SARIMAX mengeksekusi angkanya, setelah selesai, hasil makro klasemen ditaburkan kembali proporsinya ke mikro SKU spesifik seperti *"Wortel"*, *"Jambu"* berdasarkan rata-rata proporsi lakunya (baik secara berat volume maupun omset pajaknya). Bebas anomali 0 dari SKU mati.

## 4. Variabel Eksogen Masukan (*Features*)
Integrasi komprehensif 3 variabel penunjang untuk SARIMAX Kelas BC:
*   **`Weekend`**: Indikator saksi psikologi akhir pekan.
*   **`Holiday`**: Tanggalan merah dari *library* Pustaka Indonesia Python.
*   **`Promo`**: Fitur pelacak diskon (mengetahui intervensi manajemen).

## 5. Alur Pemrosesan Tesis Eksekusi
*   Melempar pemrosesan per klasemen file yang ditemukan `timeseries_B.csv` dan `timeseries_C.csv` di setiap departemen buah/sayur secara estafet.
*   **Output Berkas:** Bermuara ke satu rute akhir yakni `forecast_{dept}_class_B.csv` (atau C) dalam foder `forecast_output/` yang mana angkanya menjadi basis data siap ditambang *Dashboard* Streamlit Anda.
