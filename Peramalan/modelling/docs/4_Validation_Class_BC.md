# 📚 Dokumentasi: Uji Tes Skrip `validation_class_BC.py`

## 1. Deskripsi Umum Skrip
Menyesuaikan rancang bangun filosofi algoritma linier lambat laju di Tesis ini, `validation_class_BC.py` menjalankan misi Evaluasi khusus untuk menghitung kerugian tingkat tebakan model di Barang Menengah dan Papan Bawah (Kategori Kelas `B` & `C`). Alur ujian sama persis berpusat pada akurasi SARIMAX.

## 2. Metodologi (Satu Lawan Nyata / *Single Run*)
Skrip ini langsung berfokus pada efisiensi validasi tanpa persaingan model lain:
*   Memonopoli model uji regresi tunggal linier (**SARIMAX**) menabrak 30 rentang waku hari *Hold-out Validation*.
*   Skrip merekam skor kerugian SARIMAX saat menebak Omset Keuangan Rupiah (`Target_Sales_B`) lalu mengevaluasi lagi SARIMAX saat merekam selisih kesalahan volume kilogram buah sayur (`Target_Qty_B`).

## 3. Parameter Ekstraksi Variabel Eksogen
SARIMAX dites kemampuan kepekaannya membaca pemicu libur tanpa terjebak *noise*. Sesi validasi dibekali:
*   Masukan asupan *dummy indicators*: **`Weekend`**, **`Holiday`**, **`Promo`**. Menguji apakah di tanggal merah, tren aktual yang anomali laku dipasar bisa tertangkap prediksinya oleh kerangka matematis SARIMAX murni di skrip ini.

## 4. Evaluasi Kalkulator Matematika Numerik
Metode ujian kerugian yang ditanamkan adalah standar tesis yang solid berstandar internasional:
*   `MAPE %`: Untuk mengevaluasi kelemahan rasio persentase meleset (*Range validasi: Bawah 10% adalah unggul/sangat akurat*).
*   `MAE` & `RMSE`: Nominal pasti selisih (Misal: kesalahan hitung kilogram sayur B/C secara per unit angka mutlak).

## 5. Keluaran Produksi (Output File Data Laporan) 
*   **Dapur Cetak Metrik (.csv)**: Angka laporan MAPE per Departemen B/C di _export_ keluar menjadi `validation_metrics_summary_BC.csv` yang aman terkumpul di folder `validation_output/`. Berapapun angkanya akan membuktikan teori kelayakan SARIMAX untuk barang C lambat jualnya.
*   **Foto Jejak Langkah Grafik (.png)**: Grafik perbandingan riil visual dengan latar jaring (*grids*) di _plot_ membalurkan nilai aktual kurva data riil 30 hari melawan tren *dashed line* Prediksi SARIMAX (Target Rupiah dan Qty). Memudahkan analisis dosen penilai akan kehebatan (*baseline fitting*) model.
