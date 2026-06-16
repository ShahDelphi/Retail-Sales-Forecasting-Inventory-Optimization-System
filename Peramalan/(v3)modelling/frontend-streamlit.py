import streamlit as st
import pandas as pd
import os

# Konfigurasi Halaman (Harus di paling atas)
st.set_page_config(page_title="Forecasting Dashboard", layout="wide", page_icon="📈")

# Konfigurasi Path
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
OUTPUT_DIR = os.path.join(CURR_DIR, "forecast_output")

# Header
st.title("🛒 Dashboard Peramalan Penjualan Retail")
st.markdown("Visualisasi prediksi cerdas **30 Hari Ke Depan** berbasis Analisis ABC menggunakan algoritma klasik stasioner (**SARIMAX**) maupun Deep Learning (**LSTM**).")

# Sidebar Navigasi
st.sidebar.header("Filter Laporan")
dept = st.sidebar.selectbox("Pilih Departemen", ["Fruit", "Vegetable"]).lower()
cls = st.sidebar.selectbox("Pilih Kelas ABC", ["A", "B", "C"])

# Tentukan Target Metrik Visualisasi
st.sidebar.markdown("---")
st.sidebar.subheader("Pilihan Mode Target")
tgt_selection = st.sidebar.radio("Tampilkan Metrik Grafik:", ["💰 Sales Amount (Rupiah)", "📦 Sales Qty (Jumlah Barang)"])
target_prefix = "Sales" if "Rupiah" in tgt_selection else "Qty"
tgt_label = "Total Rupiah (Rp)" if "Rupiah" in tgt_selection else "Pcs/Kg"

# Informasi Model di Sidebar
st.sidebar.markdown("---")
if cls == 'A':
    st.sidebar.info("📌 **Model Aktif (Kelas A):**\n- SARIMAX\n- Direct Multi-Step LSTM\n- Hybrid SARIMAX-LSTM\n\n_(Menangkap fluktuasi kompleks hari libur dan promosi)_")
else:
    st.sidebar.info(f"📌 **Model Aktif (Kelas {cls}):**\n- SARIMAX\n\n_(Regresi linear kokoh untuk pola penjualan sayur/buah berfluktuasi rendah)_")

# Proses Pembacaan Data
file_name = f"forecast_{dept}_class_{cls}.csv"
file_path = os.path.join(OUTPUT_DIR, file_name)

if not os.path.exists(file_path):
    st.warning(f"⚠️ Berkas prediksi untuk Departemen **{dept.capitalize()}** Kelas **{cls}** belum tersedia.\nSilakan jalankan ulang skrip *forecasting* di terminal Tesis Anda untuk memuat fitur Dual-Target (Sales & Qty).")
else:
    # Memuat CSV ke Pandas DataFrame
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Filter Store
    if 'Store' in df.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Pilihan Cabang")
        
        def format_store_code(store_id):
            if str(store_id).startswith('10'):
                try:
                    return f"T-{int(store_id) % 1000:02d}"
                except:
                    pass
            return str(store_id)
            
        raw_stores = sorted(df['Store'].astype(str).unique().tolist())
        store_mapping = {"Semua Toko (Gabungan)": "Semua Toko (Gabungan)"}
        for s in raw_stores:
            store_mapping[format_store_code(s)] = s
            
        selected_display = st.sidebar.selectbox("🏢 Filter per Toko", list(store_mapping.keys()))
        
        if store_mapping[selected_display] != "Semua Toko (Gabungan)":
            df = df[df['Store'].astype(str) == store_mapping[selected_display]]
            
    # Deteksi apakah file ini sudah versi Dual Target baru
    # Cek ada tidaknya Predicted_Qty_SARIMAX
    is_dual = 'Predicted_Qty_SARIMAX' in df.columns
    
    # Metrik Papan Atas (KPIs)
    total_skus = df['SKU'].nunique()
    
    st.markdown(f"### Ikhtisar: Departemen {dept.capitalize()} - Kelas {cls}")
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total SKU Terdaftar", f"{total_skus} Item")
    col2.metric("📅 Horizon Waktu", f"30 Hari")
    
    if is_dual:
        total_volume_sum = df.groupby('Date')[f'Predicted_{target_prefix}_SARIMAX'].sum().sum()
        col3.metric(f"📈 Estimasi Total Volume ({target_prefix} - SARIMAX)", f"{int(total_volume_sum):,}")
    else:
        st.warning("Data yang ada masih menggunakan skema single-target lama. Menampilkan visualisasi Sales default...")
        target_prefix = "Sales"
        total_volume_sum = df.groupby('Date')[f'Predicted_Sales_SARIMAX'].sum().sum()
        col3.metric(f"📈 Estimasi Total Volume (Sales - SARIMAX)", f"{int(total_volume_sum):,}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Susunan Tab Layar Utama
    tab1, tab2 = st.tabs(["📉 Grafik Tren Agregat (Perbandingan Model)", "📊 Tabel Prediksi Komprehensif per SKU"])
    
    with tab1:
        st.subheader(f"Tren Prediksi Total Gabungan SKU ({tgt_label})")
        st.markdown("Jika tidak ada filter SKU di tab sebelah yang dipilih, grafik ini menjumlahkan (*sum*) estimasi harian seluruh barang di departemen ini.")
        
        # Agregasikan data berdasar Date
        agg_cols = [f'Predicted_{target_prefix}_SARIMAX']
        if cls == 'A':
            # Deteksi fitur LSTM dan Hybrid (khusus jika ada)
            if f'Predicted_{target_prefix}_LSTM' in df.columns:
                agg_cols.extend([f'Predicted_{target_prefix}_LSTM', f'Predicted_{target_prefix}_Hybrid'])
            
        # Pengecekan jika pengguna sebelumnya memfilter sesuatu
        if 'selected_skus' in st.session_state and st.session_state['selected_skus']:
            filtered_df_for_plot = df[df['SKU Name'].isin(st.session_state['selected_skus'])]
            agg_df = filtered_df_for_plot.groupby('Date')[agg_cols].sum().reset_index()
        else:
            agg_df = df.groupby('Date')[agg_cols].sum().reset_index()
            
        agg_df.set_index('Date', inplace=True)
        st.line_chart(agg_df, use_container_width=True)
        
    with tab2:
        st.subheader("Data Prediksi SKU Detail Lengkap (Sales & Qty)")
        
        sku_list = df['SKU Name'].unique().tolist()
        selected_skus = st.multiselect("🔍 Cari spesifik (Filter Berdasarkan Nama SKU):", sku_list, key='selected_skus')
        
        display_df = df.copy()
        if selected_skus:
            display_df = display_df[display_df['SKU Name'].isin(selected_skus)]

        # Format kolom Store: 1001 → T-01, dst.
        if 'Store' in display_df.columns:
            display_df['Store'] = display_df['Store'].astype(str).apply(format_store_code)

        # Format kolom Date: hilangkan jam (00:00:00), tampilkan tanggal saja
        if 'Date' in display_df.columns:
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.date
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Tesis Forecasting Analytics")
