import streamlit as st
import pandas as pd
import os

# Memuat modul kustom kita
from data_loader import load_forecast_data, load_validation_metrics, format_store_code, VALIDATION_DIR
from charts import plot_forecast_lines, plot_category_distribution, plot_store_distribution
from ui_components import inject_custom_css, render_kpi_cards

# 1. Konfigurasi Awal Halaman Streamlit
st.set_page_config(
    page_title="Forecasting Dashboard Retail",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Injeksi CSS Kustom
inject_custom_css()

# 2. Header Aplikasi
st.title("🛒 Dashboard Peramalan Penjualan Retail")
st.markdown("Visualisasi prediksi cerdas **30 Hari Ke Depan** berbasis Analisis ABC menggunakan algoritma klasik stasioner (**SARIMAX**) maupun Deep Learning (**LSTM**).")
st.markdown("---")

# 3. Pengaturan Navigasi & Filter di Sidebar
st.sidebar.header("Filter Analisis & Data")

# Filter Utama
dept = st.sidebar.selectbox("Pilih Departemen", ["Fruit", "Vegetable"]).lower()
cls = st.sidebar.selectbox("Pilih Kelas ABC", ["A", "B", "C"]).upper()

# Pilihan Target Visualisasi
st.sidebar.markdown("---")
st.sidebar.subheader("Target Peramalan")
tgt_selection = st.sidebar.radio(
    "Tampilkan Metrik Grafik:", 
    ["💰 Sales Amount (Rupiah)", "📦 Sales Qty (Jumlah Barang)"]
)
target_prefix = "Sales" if "Rupiah" in tgt_selection else "Qty"
is_rupiah = target_prefix == "Sales"
unit_label = "Rp" if is_rupiah else "Unit (Pcs/Kg)"

# Load Data Awal berdasarkan Departemen & Kelas ABC
df_raw = load_forecast_data(dept, cls)

if df_raw is None:
    st.error(f"⚠️ Berkas data peramalan `forecast_{dept}_class_{cls}.csv` tidak ditemukan di folder `forecast_output`.")
    st.info("Silakan jalankan ulang skrip forecasting di terminal Anda terlebih dahulu untuk menggenerasi data.")
else:
    # Penentuan Model Aktif berdasarkan Kelas ABC
    st.sidebar.markdown("---")
    st.sidebar.subheader("Algoritma Model")
    if cls == 'A':
        preferred_model = st.sidebar.selectbox(
            "🎯 Model Acuan Utama:", 
            ["Hybrid", "SARIMAX", "LSTM"],
            help="Hybrid menggabungkan keunggulan linearitas SARIMAX dan non-linearitas LSTM."
        )
        active_models = ["SARIMAX", "LSTM", "Hybrid"]
        st.sidebar.info("📌 **Kelas A (Fokus Utama):**\nMenggunakan 3 arsitektur model lengkap (SARIMAX, LSTM, Hybrid).")
    else:
        preferred_model = "SARIMAX"
        active_models = ["SARIMAX"]
        st.sidebar.info(f"📌 **Kelas {cls} (Medium/Slow Moving):**\nHanya menggunakan model SARIMAX murni karena pola fluktuasi transaksinya lebih linear.")

    # Filter Toko (Store)
    df_filtered = df_raw.copy()
    if 'Store' in df_raw.columns:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Cabang Ritel")
        
        raw_stores = sorted(df_raw['Store'].astype(str).unique().tolist())
        store_mapping = {"Semua Toko (Gabungan)": "Semua Toko (Gabungan)"}
        for s in raw_stores:
            store_mapping[format_store_code(s)] = s
            
        selected_display = st.sidebar.selectbox("🏢 Filter per Toko:", list(store_mapping.keys()))
        
        if store_mapping[selected_display] != "Semua Toko (Gabungan)":
            df_filtered = df_filtered[df_filtered['Store'].astype(str) == store_mapping[selected_display]]

    # 4. Render Metrik KPI Utama di Bagian Atas
    render_kpi_cards(df_filtered, target_prefix, preferred_model, is_rupiah)

    # 5. Susunan Tab Layar Utama Dashboard
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Ringkasan Bisnis (Overview)", 
        "📈 Tren Peramalan (Forecasting)", 
        "🧪 Akurasi & Validasi Model", 
        "📥 Pusat Ekspor & Rekomendasi"
    ])
    
    # ----------------------------------------------------
    # TAB 1: EXECUTIVE OVERVIEW
    # ----------------------------------------------------
    with tab1:
        st.subheader("Ikhtisar Performa Penjualan & Distribusi")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown(f"#### 🍩 Kontribusi Penjualan per Kategori ({preferred_model})")
            fig_pie = plot_category_distribution(df_filtered, target_prefix, preferred_model)
            if fig_pie:
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("Data kategori tidak tersedia.")
                
        with col_c2:
            st.markdown("#### 🏢 Perbandingan Kontribusi antar Toko (Cabang)")
            fig_bar = plot_store_distribution(df_filtered, target_prefix, preferred_model, format_store_code)
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.write("Data Toko tidak tersedia.")
                
    # ----------------------------------------------------
    # TAB 2: FORECASTING DEEP-DIVE
    # ----------------------------------------------------
    with tab2:
        st.subheader("Tren Prediksi Detail & Perbandingan Model")
        
        # Filter Pencarian SKU
        sku_list = sorted(df_filtered['SKU Name'].unique().tolist())
        selected_skus = st.multiselect(
            "🔍 Cari & Filter Berdasarkan Nama SKU (Kosongkan untuk menampilkan semua):", 
            sku_list
        )
        
        df_plot = df_filtered.copy()
        if selected_skus:
            df_plot = df_plot[df_plot['SKU Name'].isin(selected_skus)]
            
        # Tampilkan Grafik Line Chart
        fig_lines = plot_forecast_lines(df_plot, target_prefix, active_models, unit_label)
        st.plotly_chart(fig_lines, use_container_width=True)
        
        # Detail Data Tabel SKU
        st.markdown("#### 📊 Rincian Tabel Prediksi SKU")
        
        display_df = df_plot.copy()
        # Pembersihan kolom untuk tampilan tabel
        if 'Store' in display_df.columns:
            display_df['Store'] = display_df['Store'].astype(str).apply(format_store_code)
        if 'Date' in display_df.columns:
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.date
            
        # Menyederhanakan kolom prediksi di tabel
        pred_cols = [c for c in display_df.columns if c.startswith('Predicted_')]
        base_cols = ['Date', 'Store', 'SKU', 'SKU Name', 'Category']
        
        # Format nilai angka di tabel agar mudah dibaca
        table_df = display_df[base_cols + pred_cols].copy()
        for col in pred_cols:
            if 'Sales' in col:
                table_df[col] = table_df[col].apply(lambda x: f"Rp {int(x):,}".replace(",", "."))
            else:
                table_df[col] = table_df[col].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    # ----------------------------------------------------
    # TAB 3: MODEL VALIDATION & ACCURACY
    # ----------------------------------------------------
    with tab3:
        st.subheader("Evaluasi Performa & Akurasi Model Historis")
        
        metrics_df = load_validation_metrics(cls)
        
        if metrics_df is not None:
            # Map target prefix ke target name di CSV
            val_target_name = "Sales" if target_prefix == "Sales" else "Sales Qty"
            
            # Filter baris yang cocok dengan Dept dan Target
            filtered_metrics = metrics_df[
                (metrics_df['Dept'].str.lower() == dept.lower()) & 
                (metrics_df['Target'] == val_target_name)
            ].copy()
            
            if not filtered_metrics.empty:
                st.markdown(f"Tabel berikut menampilkan metrik evaluasi model hasil uji validasi *Hold-out* (30 hari data aktual terakhir disembunyikan untuk pengujian akurasi).")
                
                # Format tampilan metrik
                disp_metrics = filtered_metrics.copy()
                disp_metrics['MAPE'] = disp_metrics['MAPE'].apply(lambda x: f"{x:.2f}%")
                disp_metrics['MAE'] = disp_metrics['MAE'].apply(lambda x: f"{x:,.2f}")
                disp_metrics['RMSE'] = disp_metrics['RMSE'].apply(lambda x: f"{x:,.2f}")
                
                # Tampilkan tabel metrik
                st.dataframe(disp_metrics, use_container_width=True, hide_index=True)
                
                # Insight performa terbaik
                best_row = filtered_metrics.loc[filtered_metrics['MAPE'].idxmin()]
                st.success(
                    f"🏆 **Rekomendasi Akurasi:** Model **{best_row['Model']}** memiliki tingkat kesalahan terendah "
                    f"pada kategori ini dengan nilai **MAPE sebesar {best_row['MAPE']:.2f}%**."
                )
            else:
                st.warning("Metrik untuk kombinasi Departemen dan Target saat ini tidak ditemukan.")
        else:
            st.warning("Data metrik validasi model belum tergenerasi untuk Kelas ini.")
            
        # Tampilkan Grafik Plot Validasi Historis jika tersedia
        st.markdown("#### 📈 Visualisasi Validasi Aktual vs Prediksi")
        
        # Deteksi nama file chart plot validasi
        target_val_suffix = "Sales" if target_prefix == "Sales" else "SalesQty"
        plot_filename = f"opt_val_plot_{dept}_class_{cls}_{target_val_suffix}.png"
        
        # Path ke file plot validasi
        plot_path = os.path.join(VALIDATION_DIR, f"class_{cls}", plot_filename)
        
        # Jika file kelas B/C memiliki format nama yang berbeda (tidak memakai kata opt_)
        if not os.path.exists(plot_path) and cls in ['B', 'C']:
            plot_filename = f"opt_val_plot_{dept}_class_{cls}_{target_val_suffix}.png" # default
            plot_path = os.path.join(VALIDATION_DIR, f"class_{cls}", f"opt_val_plot_{dept}_class_{cls}_{target_val_suffix}.png")
            # Coba alternatif nama file jika tidak menggunakan opt_
            if not os.path.exists(plot_path):
                plot_path = os.path.join(VALIDATION_DIR, f"class_{cls}", f"val_plot_{dept}_class_{cls}_{target_val_suffix}.png")
                
        if os.path.exists(plot_path):
            st.image(plot_path, caption=f"Grafik Perbandingan Data Aktual vs Prediksi Model Validasi ({dept.capitalize()} Kelas {cls} - {val_target_name})", use_container_width=True)
        else:
            st.info(f"Gambar plot visualisasi validasi `{plot_filename}` tidak ditemukan di folder `validation_output`.")

    # ----------------------------------------------------
    # TAB 4: EXPORT CENTER & SUPPLY CHAIN INSIGHTS
    # ----------------------------------------------------
    with tab4:
        st.subheader("📥 Pusat Ekspor Laporan Prediksi")
        st.markdown("Unduh hasil peramalan penjualan untuk perencanaan rantai pasok dan pemesanan inventaris.")
        
        # Penyiapan Data Unduh
        export_df = df_filtered.copy()
        if 'Store' in export_df.columns:
            export_df['Store'] = export_df['Store'].astype(str).apply(format_store_code)
            
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=f"💾 Unduh Data Peramalan ({dept.capitalize()} Kelas {cls} - {target_prefix}) (.CSV)",
            data=csv_data,
            file_name=f"forecast_retail_{dept}_class_{cls}_{target_prefix.lower()}.csv",
            mime="text/csv",
            key='download-csv'
        )
        
        st.markdown("---")
        st.subheader("💡 Rekomendasi Manajemen Inventaris (Supply Chain Insights)")
        
        # Analisis Cerdas untuk Rantai Pasok
        # Hitung item dengan total prediksi volume tertinggi dan terendah
        col_pred_main = f"Predicted_{target_prefix}_{preferred_model}"
        if col_pred_main in df_filtered.columns:
            sku_summary = df_filtered.groupby('SKU Name')[col_pred_main].sum().reset_index()
            sku_summary = sku_summary.sort_values(by=col_pred_main, ascending=False)
            
            col_in1, col_in2 = st.columns(2)
            
            with col_in1:
                st.error("🚨 **Barang Kategori Permintaan Tinggi (Prioritas Stok)**")
                st.markdown("SKU di bawah ini diproyeksikan memiliki volume penjualan terbesar 30 hari ke depan. Pastikan ketersediaan stok aman (*safety stock*) untuk mencegah kehilangan penjualan (*stockout*):")
                
                top_items = sku_summary.head(5)
                for idx, row in top_items.iterrows():
                    val_str = f"Rp {int(row[col_pred_main]):,}".replace(",", ".") if is_rupiah else f"{row[col_pred_main]:,.1f} Unit".replace(",", "X").replace(".", ",").replace("X", ".")
                    st.write(f"- **{row['SKU Name']}** (Proyeksi: {val_str})")
                    
            with col_in2:
                st.warning("⚠️ **Barang Kategori Permintaan Rendah (Risiko Overstock)**")
                st.markdown("SKU di bawah ini diproyeksikan memiliki volume penjualan sangat rendah. Disarankan untuk membatasi pemesanan (*purchase order*) untuk meminimalkan pembusukan/kedaluwarsa barang:")
                
                bottom_items = sku_summary.tail(5).iloc[::-1] # Urutkan dari yang terendah
                for idx, row in bottom_items.iterrows():
                    val_str = f"Rp {int(row[col_pred_main]):,}".replace(",", ".") if is_rupiah else f"{row[col_pred_main]:,.1f} Unit".replace(",", "X").replace(".", ",").replace("X", ".")
                    st.write(f"- **{row['SKU Name']}** (Proyeksi: {val_str})")
        else:
            st.info("Rekomendasi inventaris tidak dapat dimuat karena kolom model yang dipilih tidak tersedia.")

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Tesis Forecasting Analytics")
