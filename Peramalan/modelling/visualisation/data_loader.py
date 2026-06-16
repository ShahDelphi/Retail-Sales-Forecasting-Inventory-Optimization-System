import os
import pandas as pd
import streamlit as st

# Konfigurasi Path Dinamis
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PARENT_DIR, "forecast_output")
VALIDATION_DIR = os.path.join(PARENT_DIR, "validation_output")

def format_store_code(store_id):
    """Mengubah kode store numerik ritel menjadi format T-XX (misal: 1001 -> T-01)."""
    val_str = str(store_id).strip()
    if val_str.startswith('10'):
        try:
            return f"T-{int(val_str) % 1000:02d}"
        except:
            pass
    elif val_str.isdigit():
        try:
            return f"T-{int(val_str):02d}"
        except:
            pass
    return val_str

@st.cache_data(show_spinner=True)
def load_forecast_data(dept: str, cls: str):
    """
    Memuat data CSV prediksi berdasarkan departemen (fruit/vegetable) dan kelas ABC (A/B/C).
    Mengembalikan DataFrame pandas atau None jika berkas tidak ditemukan.
    """
    file_name = f"forecast_{dept.lower()}_class_{cls.upper()}.csv"
    file_path = os.path.join(OUTPUT_DIR, file_name)
    
    if not os.path.exists(file_path):
        return None
        
    df = pd.read_csv(file_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        
    return df

@st.cache_data(show_spinner=True)
def load_validation_metrics(cls: str):
    """
    Memuat data metrik validasi model (MAPE, MAE, RMSE) dari berkas CSV validasi historis.
    """
    cls_upper = cls.upper()
    if cls_upper == 'A':
        file_path = os.path.join(VALIDATION_DIR, "class_A", "opt_validation_metrics_summary_class_A.csv")
    elif cls_upper == 'B':
        file_path = os.path.join(VALIDATION_DIR, "class_B", "validation_metrics_summary_class_B.csv")
    elif cls_upper == 'C':
        file_path = os.path.join(VALIDATION_DIR, "class_C", "validation_metrics_summary_class_C.csv")
    else:
        return None
        
    if not os.path.exists(file_path):
        return None
        
    df = pd.read_csv(file_path)
    # Bersihkan nama kolom dan data teks
    df.columns = [col.strip() for col in df.columns]
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
        
    return df
