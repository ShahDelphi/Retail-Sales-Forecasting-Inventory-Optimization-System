# 📚 Dokumentasi: Antarmuka Aplikasi `frontend-streamlit.py`

## 1. Deskripsi Umum Program (Data Visualization Dashboard)
Skrip Python `frontend-streamlit.py` adalah jubah etalase final dari penelitian Tesis Anda. Skrip ini dibangun bertumpu mulus pada *Framework Data-UI* berbasis Pustaka Python `Streamlit`. Fungsinya bukan sebagai mesin peramal lagi, namun semata-mata sebagai cermin pembaca (*read-only*) yang menarik secara estetika laporan metrik-metrik abstrak milik *skrip forecaster* A, B, dan C dan mensulapnya menjadi sebuah mahakarya *Dashboard* UI modern agar interaktif ketika diperagakan secara langsung di hadapan audiensi penilai Tesis.

## 2. Tab Interaktif Logika Panel Analitik & Dinamis 
Terdapat susunan arsitektur perwajahan interaktif yang ditanamkan di aplikasi web ini (dieksekusi melalui `streamlit run ...`):

### A. Panel Filter Analisis (*Sisi Kiri Sidebar*)
1.  **Saringan Departemen-Kelas ABC**: Menampilkan Opsi untuk mengganti tabel prediksi dengan _Dropdown_ menu memilih antara Departemen *Buah/Sayur*, serta Kelas sasarannya (*A*, *B*, *C*). Jika dipilih Kelas B/C, otomatis teks narasi informatif di layar akan memberi tahu audiens bawah layar ini membedah *Baseline SARIMAX Regresi Logistik* porsi stabil.
2.  **Tombol Pengalih Skala (*Radio Button Targets*)**: Memungkinkan pengguna dengan satu kali *"klik"* menyihir *mode* perwajahan **Grafik 💰 Rupiah Keuntungan (Sales)** menjadi **Tabel dan Kurva 📦 Volume Stok (Qty) Barangan**. Konversi angkanya berjalan di atas *backend logic* skrip untuk mengambil *Header DataFrame* prediksi secara otomatis sesuai prefiks "*Sales*" atau "*Qty*".

### B. Indikator Tolok Ukur Inti (*Top Header KPIs*)
Bagian badan halaman awal memberikan potret cepat *(Macro View)* terkait angka agregasi utama (Metra Utama): 
*   Berapa *banyak Item (SKU)* spesifik unik yang laku hari itu?
*   Menghitung rentang batasan waktu *Horizons*, serta Nilai Totalkan Estimasi/Omset Makro selama siklus sebulan (Berapa proyeksi kasar uang terkumpul jika Kelas A ini terjual 30 hari murni ke depan).  

### C. Kurva Pemandangan *Timeseries Analysis* (*Tab 1*)
Tab presentasi Grafik `(st.line_chart)` memetakan perbandingan "Omset Kolektif/Super Agregasi Sum Total" secara utuh (Makro-Super). Menyarangkan 3 garis warna-warni yang langsung menunjukkan adu mekanik dari masa depan yang di-*plot* model (SARIMAX kuning vs LSTM merah vs Hybrid Biru). 

### D. Tabel Penyaring Mikro SKU Detail (*Tab 2*)
Halaman data *DataFrame* statis lengkap. Anda tidak perlu mencari angka komoditi satu per satu dengan manual kalkulator; fitur **Multiselect Kolom Spesifik** (Sistem Cari) mengizinkan asisten / Penguji menyebut nama produk dan secara reaktif (misal: "Jeruk Pontianak"), sistem akan memfilter jutaan sel di datanya secara mandiri dan melempar ke *Pandas DataFrame Web* rentetan prediksi 30 Angka rupiah/Biji per harinya.
