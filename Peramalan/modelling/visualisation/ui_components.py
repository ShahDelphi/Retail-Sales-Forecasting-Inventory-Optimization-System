import streamlit as st
import pandas as pd

def inject_custom_css():
    """
    Menyuntikkan CSS kustom untuk mempercantik tampilan UI Streamlit.
    """
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Font Global */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Menghilangkan garis default Streamlit */
    .stApp {
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
    }
    
    /* Memaksa warna teks utama di area main body menjadi gelap (mencegah tabrakan warna putih) */
    [data-testid="stMain"] h1, 
    [data-testid="stMain"] h2, 
    [data-testid="stMain"] h3, 
    [data-testid="stMain"] h4, 
    [data-testid="stMain"] h5, 
    [data-testid="stMain"] h6,
    [data-testid="stMain"] p,
    [data-testid="stMain"] label,
    [data-testid="stMain"] .stMarkdown p {
        color: #1E293B !important;
    }
    
    /* Desain Kartu KPI Kustom */
    .kpi-container {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
        width: 100%;
    }
    
    .kpi-card {
        flex: 1;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.06);
        transition: all 0.3s ease-in-out;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
        border-color: rgba(67, 97, 238, 0.3);
    }
    
    .kpi-label {
        font-size: 0.85rem;
        color: #6C757D !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2B2D42 !important;
        line-height: 1.2;
    }
    
    .kpi-subtext {
        font-size: 0.75rem;
        color: #4361EE !important;
        font-weight: 500;
        margin-top: 4px;
    }
    
    /* Styling khusus Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        color: #F8FAFC;
    }
    
    [data-testid="stSidebar"] .stMarkdown p {
        color: #CBD5E1 !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #F8FAFC !important;
    }

    
    /* Desain Tabs Custom */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: rgba(255, 255, 255, 0.5);
        border-radius: 10px 10px 0px 0px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-bottom: none;
        color: #475569;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #4361EE !important;
        border-top: 3px solid #4361EE !important;
        box-shadow: 0 -4px 12px rgba(67, 97, 238, 0.05);
    }
    
    /* Tombol ekspor */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_kpi_cards(df: pd.DataFrame, target_prefix: str, preferred_model: str, is_rupiah: bool):
    """
    Merender layout kartu KPI premium menggunakan HTML kustom.
    """
    col_name = f"Predicted_{target_prefix}_{preferred_model}"
    if col_name not in df.columns:
        cols = [c for c in df.columns if c.startswith(f"Predicted_{target_prefix}_")]
        col_name = cols[0] if cols else None
        
    if col_name:
        total_sum = df.groupby('Date')[col_name].sum().sum()
    else:
        total_sum = 0
        
    total_skus = df['SKU'].nunique()
    
    # Format nilai
    if is_rupiah:
        formatted_value = f"Rp {int(total_sum):,}".replace(",", ".")
        label_text = "Estimasi Pendapatan"
        model_subtext = f"Berdasarkan model {preferred_model}"
    else:
        formatted_value = f"{total_sum:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        label_text = "Estimasi Kuantitas Penjualan"
        model_subtext = f"Berdasarkan model {preferred_model} (Pcs/Kg)"
        
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">{label_text}</div>
            <div class="kpi-value">{formatted_value}</div>
            <div class="kpi-subtext">✨ {model_subtext}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Jumlah SKU Terdaftar</div>
            <div class="kpi-value">{total_skus} Item</div>
            <div class="kpi-subtext">📦 Terklasifikasi ABC Ritel</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Horizon Prediksi</div>
            <div class="kpi-value">30 Hari</div>
            <div class="kpi-subtext">📅 1 Bulan ke Depan (Jan 2026)</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)
