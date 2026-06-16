import os
import pandas as pd
import numpy as np
from datetime import timedelta
import statsmodels.api as sm
import warnings
import matplotlib.pyplot as plt
import holidays

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "validation_output")
HORIZON = 30
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def compute_mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0
    if np.sum(mask) == 0:
        return np.nan
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def compute_mae(y_true, y_pred):
    return np.mean(np.abs(np.array(y_true) - np.array(y_pred)))

def compute_rmse(y_true, y_pred):
    return np.sqrt(np.mean((np.array(y_true) - np.array(y_pred))**2))

def print_range_check(name, series):
    print(f"  {name:15} -> Min: {np.min(series):8.2f}, Max: {np.max(series):8.2f}, Mean: {np.mean(series):8.2f}")

def train_predict_sarimax(train_df, future_df, target_col='Sales'):
    endog = train_df[target_col]
    exog_cols = ['Weekend', 'Holiday', 'Promo']
    exog_train = train_df[exog_cols]
    exog_future = future_df[exog_cols]
    
    model = sm.tsa.statespace.SARIMAX(
        endog,
        exog=exog_train,
        order=SARIMAX_ORDER,
        seasonal_order=SARIMAX_SEASONAL,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    result = model.fit(disp=False)
    
    forecast = result.get_forecast(steps=len(future_df), exog=exog_future)
    return forecast.predicted_mean.values

# Bulan-bulan yang divalidasi: (year, month, nama_bulan)
VALIDATION_MONTHS = [
    (2025, 10, 'Oktober'),
    (2025, 11, 'November'),
]

def validate_class_month(class_name, dept, class_df, year, month, month_name):
    """Validasi satu bulan tertentu sebagai test set (SARIMAX only untuk Class B & C)."""
    print(f"\n{'='*55}")
    print(f"Dept: {dept.upper()} | Class: {class_name} | Test: {month_name} {year}")
    print(f"{'='*55}")

    # Test set = seluruh hari di bulan & tahun tersebut
    mask_test = (class_df['Date'].dt.year == year) & (class_df['Date'].dt.month == month)
    test_df  = class_df[mask_test].reset_index(drop=True)
    # Train set = semua data sebelum bulan test
    train_df = class_df[class_df['Date'] < test_df['Date'].min()].reset_index(drop=True)

    if len(test_df) == 0:
        print(f"  Tidak ada data untuk {month_name} {year}. Dilewati.")
        return []
    if len(train_df) < HORIZON * 2:
        print(f"  Data training tidak cukup untuk {month_name} {year}. Dilewati.")
        return []

    print(f"  Train: {len(train_df)} hari | Test: {len(test_df)} hari "
          f"({test_df['Date'].min().date()} s.d. {test_df['Date'].max().date()})")

    metrics_summary = []

    for target in ['Sales', 'Sales Qty']:
        y_actual = test_df[target].values

        print(f"\n--- [{month_name}] Training SARIMAX {SARIMAX_ORDER} x {SARIMAX_SEASONAL} ({target}) ---")
        sarimax_pred = train_predict_sarimax(train_df, test_df, target_col=target)
        predictions_dict = {'SARIMAX': sarimax_pred}

        print(f"\n  [ Range Check: {target} ]")
        print_range_check(f"Actual {target}", y_actual)
        for model_name, preds in predictions_dict.items():
            print_range_check(f"Pred {model_name}", preds)

        print(f"\n  [ Error Metrics: {target} | {month_name} {year} ]")
        for model_name, preds in predictions_dict.items():
            mape_val = compute_mape(y_actual, preds)
            mae_val  = compute_mae(y_actual, preds)
            rmse_val = compute_rmse(y_actual, preds)
            print(f"    {model_name:10} -> MAPE: {mape_val:6.2f}%, MAE: {mae_val:9.2f}, RMSE: {rmse_val:9.2f}")
            metrics_summary.append({
                'Dept': dept,
                'Class': class_name,
                'Month': month_name,
                'Year': year,
                'Target': target,
                'Model': model_name,
                'MAPE': mape_val,
                'MAE': mae_val,
                'RMSE': rmse_val
            })

        # --- Plot ---
        test_dates = test_df['Date']
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(test_dates, y_actual,     label=f'Actual {target}', marker='o', color='black', linewidth=2)
        ax.plot(test_dates, sarimax_pred, label='SARIMAX',           linestyle='--', color='steelblue', linewidth=2)

        ax.set_title(
            f"Validasi {month_name} {year} ({target}) — Dept: {dept.upper()} | Class: {class_name}",
            fontsize=13
        )
        ax.set_xlabel("Tanggal")
        ax.set_ylabel(target)
        ax.legend()
        ax.grid(True, alpha=0.4)
        fig.autofmt_xdate()
        plt.tight_layout()

        fname_suffix = target.replace(' ', '')
        month_tag    = month_name.lower()
        plot_path = os.path.join(
            OUTPUT_DIR,
            f"opt_val_plot_{dept}_class_{class_name}_{month_tag}_{fname_suffix}.png"
        )
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"  Plot disimpan: {plot_path}")

    return metrics_summary


def validate_class(class_name, dept, file_path):
    print(f"\n{'='*50}")
    print(f"Validating Dept: {dept.upper()}, Class: {class_name}")
    print(f"{'='*50}")

    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])

    id_holidays = holidays.country_holidays('ID')
    df['Weekend'] = df['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df['Holiday'] = df['Date'].apply(lambda x: 1 if x in id_holidays else 0)

    class_df = df.groupby('Date').agg(
        Sales=('Sales', 'sum'),
        Sales_Qty=('Sales Qty', 'sum'),
        Promo=('Promo', 'max'),
        Weekend=('Weekend', 'max'),
        Holiday=('Holiday', 'max')
    ).reset_index()
    class_df = class_df.rename(columns={'Sales_Qty': 'Sales Qty'})
    class_df = class_df.sort_values('Date').reset_index(drop=True)

    # 31 Desember ditetapkan sebagai hari promo (peak season Tahun Baru)
    mask_dec31 = (class_df['Date'].dt.month == 12) & (class_df['Date'].dt.day == 31)
    class_df.loc[mask_dec31, 'Promo'] = 1

    if len(class_df) <= HORIZON * 2:
        print(f"Skipping {dept} Class {class_name}: Not enough data.")
        return []

    all_metrics = []
    for year, month, month_name in VALIDATION_MONTHS:
        metrics = validate_class_month(class_name, dept, class_df, year, month, month_name)
        all_metrics.extend(metrics)

    return all_metrics


def main():
    classes = ['B', 'C']
    all_metrics = []

    for dept in DEPARTMENTS:
        dept_data_dir = os.path.join(BASE_DATA_DIR, dept)
        for cls in classes:
            file_path = os.path.join(dept_data_dir, f"timeseries_{cls}.csv")
            if os.path.exists(file_path):
                metrics = validate_class(cls, dept, file_path)
                if metrics:
                    all_metrics.extend(metrics)
            else:
                print(f"File not found: {file_path}")

    if all_metrics:
        df_metrics = pd.DataFrame(all_metrics)
        metrics_csv_path = os.path.join(OUTPUT_DIR, "validation_metrics_summary_BC.csv")
        df_metrics.to_csv(metrics_csv_path, index=False)
        print(f"\nMetrics summary disimpan ke: {metrics_csv_path}")
        print(df_metrics.to_string(index=False))

if __name__ == "__main__":
    main()
