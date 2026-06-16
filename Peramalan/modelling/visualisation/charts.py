import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Palet warna premium untuk model dan visualisasi
COLOR_MAP = {
    'SARIMAX': '#4361EE',       # Indigo
    'LSTM': '#4CC9F0',          # Cyan
    'Hybrid': '#F72585',        # Rose
    'Historical': '#7209B7'     # Violet
}

def plot_forecast_lines(df: pd.DataFrame, target_prefix: str, active_models: list, unit_label: str):
    """
    Membuat grafik garis interaktif Plotly untuk perbandingan hasil prediksi model.
    """
    fig = go.Figure()
    
    # Kelompokkan data harian
    agg_df = df.groupby('Date').sum().reset_index()
    
    for model in active_models:
        col_name = f"Predicted_{target_prefix}_{model}"
        if col_name in agg_df.columns:
            fig.add_trace(go.Scatter(
                x=agg_df['Date'],
                y=agg_df[col_name],
                mode='lines+markers',
                name=f"Prediksi {model}",
                line=dict(color=COLOR_MAP.get(model, '#6c757d'), width=3),
                marker=dict(size=6, symbol='circle'),
                hovertemplate=f"<b>Model {model}</b><br>Tanggal: %{{x|%d %b %Y}}<br>Nilai: %{{y:,.2f}} {unit_label}<extra></extra>"
            ))
            
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        xaxis_title="Tanggal Peramalan (30 Hari)",
        yaxis_title=f"Total Hasil Peramalan ({unit_label})",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=50, b=40),
        height=450,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            rangeslider=dict(visible=True),
            type="date",
            tickfont=dict(color='#1E293B'),
            title=dict(font=dict(color='#1E293B'))
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            tickformat=",",
            tickfont=dict(color='#1E293B'),
            title=dict(font=dict(color='#1E293B'))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1E293B')
    )
    
    return fig

def plot_category_distribution(df: pd.DataFrame, target_prefix: str, preferred_model: str):
    """
    Membuat Donut Chart Plotly untuk kontribusi penjualan per kategori barang.
    """
    col_name = f"Predicted_{target_prefix}_{preferred_model}"
    if col_name not in df.columns:
        # Fallback jika model pilihan tidak ada di data
        cols = [c for c in df.columns if c.startswith(f"Predicted_{target_prefix}_")]
        if not cols:
            return None
        col_name = cols[0]
        
    cat_df = df.groupby('Category')[col_name].sum().reset_index()
    cat_df = cat_df.sort_values(by=col_name, ascending=False)
    
    # Gunakan palet warna yang harmonis
    fig = px.pie(
        cat_df, 
        values=col_name, 
        names='Category', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Safe,
        labels={'Category': 'Kategori', col_name: 'Total Estimasi'}
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Estimasi Penjualan: %{value:,.0f}<br>Persentase: %{percent}<extra></extra>"
    )
    
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1E293B')
    )
    
    return fig

def plot_store_distribution(df: pd.DataFrame, target_prefix: str, preferred_model: str, format_store_fn):
    """
    Membuat Horizontal Bar Chart Plotly untuk perbandingan proyeksi kontribusi antar Store.
    """
    col_name = f"Predicted_{target_prefix}_{preferred_model}"
    if col_name not in df.columns:
        cols = [c for c in df.columns if c.startswith(f"Predicted_{target_prefix}_")]
        if not cols:
            return None
        col_name = cols[0]
        
    store_df = df.groupby('Store')[col_name].sum().reset_index()
    store_df['Store_Code'] = store_df['Store'].apply(format_store_fn)
    store_df = store_df.sort_values(by=col_name, ascending=True) # Ascending untuk horizontal bar chart
    
    fig = px.bar(
        store_df,
        x=col_name,
        y='Store_Code',
        orientation='h',
        labels={'Store_Code': 'Cabang Toko', col_name: 'Total Estimasi'},
        color_discrete_sequence=['#4361EE']
    )
    
    fig.update_traces(
        hovertemplate="<b>Cabang %{y}</b><br>Estimasi Penjualan: %{x:,.0f}<extra></extra>"
    )
    
    fig.update_layout(
        template="plotly_white",
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)',
            tickformat=",",
            tickfont=dict(color='#1E293B'),
            title=dict(font=dict(color='#1E293B'))
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color='#1E293B'),
            title=dict(font=dict(color='#1E293B'))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1E293B')
    )
    
    return fig
