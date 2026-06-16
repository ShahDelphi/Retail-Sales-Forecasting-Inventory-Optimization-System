import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import os

# Set file paths
curr_dir = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
data_path = os.path.join(curr_dir, "dataset", "time-series", "fruit", "timeseries_A.csv")
output_dir = os.path.join(curr_dir, "plots")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 1. Load Data
print("Loading data...")
df = pd.read_csv(data_path)
print("Columns:", df.columns.tolist())

date_col = 'Date'
sku_col = 'SKU'
sales_col = 'Sales' if 'Sales' in df.columns else 'Quantity'
if sales_col not in df.columns:
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        sales_col = numeric_cols[0]

print(f"\nUsing '{sku_col}' for items, '{date_col}' for time, and '{sales_col}' for values.")

# 2. Find top 3 SKUs by sales
top_skus = df.groupby(sku_col)[sales_col].sum().sort_values(ascending=False).head(3).index.tolist()
print(f"Top 3 SKUs by total {sales_col}: {top_skus}")

# 3. Pengecekan for each SKU
for sku in top_skus:
    print(f"\n{'='*50}")
    print(f"Analyzing SKU: {sku}")
    print(f"{'='*50}")
    
    sku_df = df[df[sku_col] == sku].copy()
    
    if date_col in sku_df.columns:
        sku_df[date_col] = pd.to_datetime(sku_df[date_col])
        # Aggregate by date if there are multiple entries per date
        ts_aggr = sku_df.groupby(date_col)[sales_col].sum()
        ts_aggr = ts_aggr.sort_index()
    else:
        ts_aggr = sku_df[sales_col]
        
    ts_clean = ts_aggr.dropna()
    print(f"Data points after aggregation: {len(ts_clean)}")
    
    # a. Plot Data
    plt.figure(figsize=(12, 4))
    plt.plot(ts_clean.index if date_col in sku_df.columns else range(len(ts_clean)), ts_clean.values)
    plt.title(f"{sku} - Data Plot ({sales_col})")
    plt.ylabel(sales_col)
    plt.xlabel('Date')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"{sku}_plot.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"-> Saved data plot: {plot_path}")
    
    # b. ADF Test
    print("\nPerforming ADF Test...")
    if len(ts_clean) > 10:
        try:
            result = adfuller(ts_clean)
            adf_statistic = result[0]
            p_value = result[1]
            print(f"   ADF Statistic: {adf_statistic:.4f}")
            print(f"   p-value: {p_value:.4f}")
            if p_value < 0.05:
                print("   Conclusion: Data is STATIONARY (Reject H0)")
            else:
                print("   Conclusion: Data is NON-STATIONARY (Fail to reject H0)")
        except Exception as e:
            print(f"   ADF Test failed: {e}")
    else:
        print("   Not enough data for ADF test.")
        
    # c. ACF & PACF
    try:
        lags = min(40, len(ts_clean) // 3)
        if lags > 0:
            fig, axes = plt.subplots(1, 2, figsize=(16, 4))
            plot_acf(ts_clean, ax=axes[0], lags=lags)
            plot_pacf(ts_clean, ax=axes[1], lags=lags)
            axes[0].set_title(f"{sku} - ACF")
            axes[1].set_title(f"{sku} - PACF")
            plt.tight_layout()
            acf_pacf_path = os.path.join(output_dir, f"{sku}_acf_pacf.png")
            plt.savefig(acf_pacf_path)
            plt.close()
            print(f"-> Saved ACF/PACF plot: {acf_pacf_path}")
        else:
            print("   Not enough data lags for ACF/PACF plots.")
    except Exception as e:
        print(f"   ACF/PACF plotting failed: {e}")

print("\nAnalysis complete.")
