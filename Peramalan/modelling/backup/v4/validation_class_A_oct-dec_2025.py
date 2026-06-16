import os
import pandas as pd
import numpy as np
from datetime import timedelta
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
import warnings
import tensorflow as tf
from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate # type: ignore
from tensorflow.keras.models import Model # type: ignore
import matplotlib.pyplot as plt
import holidays

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "validation_output_oct_dec_2025", "class_A")
HORIZON = 30
LOOKBACK = 14  
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Error Metrics
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

def mask_anomaly_period(train_df, col, anomaly_year=2025, anomaly_month=9, window=30):
    """Ganti nilai pada periode anomali yang diketahui dengan rolling median.

    Pendekatan ini lebih targeted daripada IQR global: hanya mengganti
    bulan yang secara domain knowledge diidentifikasi sebagai anomali
    (September 2025 = spike tidak normal), sehingga bulan lain tidak
    terdampak dan tren historis tetap terjaga.
    """
    df = train_df.copy()
    # Hitung rolling median dari seluruh series sebagai nilai pengganti
    rolling_med = df[col].rolling(window, center=True, min_periods=5).median()
    rolling_med = rolling_med.ffill().bfill()

    anomaly_mask = (
        (df['Date'].dt.year  == anomaly_year) &
        (df['Date'].dt.month == anomaly_month)
    )
    n_replaced = anomaly_mask.sum()
    if n_replaced > 0:
        df.loc[anomaly_mask, col] = rolling_med[anomaly_mask].values
        print(f"    [Anomaly Masking] {n_replaced} hari {anomaly_month}/{anomaly_year} "
              f"pada '{col}' diganti rolling median (window={window})")
    return df[col]

def train_predict_sarimax(train_df, future_df, use_promo=False, target_col='Sales'):
    endog = train_df[target_col]
    exog_cols = ['Weekend', 'Holiday', 'Promo'] if use_promo else ['Weekend', 'Holiday']
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
    
    fitted_vals = result.fittedvalues
    residuals = result.resid
    
    forecast = result.get_forecast(steps=len(future_df), exog=exog_future)
    return forecast.predicted_mean.values, fitted_vals.values, residuals.values

def prepare_lstm_data(series, exog_df, lookback, horizon):
    X_past, X_future, y = [], [], []
    series_vals = series.values
    exog_vals = exog_df.values
    
    for i in range(len(series_vals) - lookback - horizon + 1):
        past_target = series_vals[i:i+lookback].reshape(-1, 1)
        past_exog = exog_vals[i:i+lookback]
        past_features = np.hstack([past_target, past_exog])
        future_exog = exog_vals[i+lookback : i+lookback+horizon].flatten()
        X_past.append(past_features)
        X_future.append(future_exog)
        y.append(series_vals[i+lookback : i+lookback+horizon])
        
    return np.array(X_past), np.array(X_future), np.array(y)

def train_predict_lstm(train_df, future_df, lookback=LOOKBACK, use_promo=True, target_col='Sales'):
    # Gunakan panjang aktual future_df sebagai horizon (fleksibel untuk setiap bulan)
    horizon = len(future_df)
    exog_cols = ['Weekend', 'Holiday', 'Promo'] if use_promo else ['Weekend', 'Holiday']

    train_df = train_df.copy()
    train_df['dayofweek_sin'] = np.sin(2 * np.pi * train_df['Date'].dt.dayofweek / 7)
    train_df['dayofweek_cos'] = np.cos(2 * np.pi * train_df['Date'].dt.dayofweek / 7)
    future_df = future_df.copy()
    future_df['dayofweek_sin'] = np.sin(2 * np.pi * future_df['Date'].dt.dayofweek / 7)
    future_df['dayofweek_cos'] = np.cos(2 * np.pi * future_df['Date'].dt.dayofweek / 7)
    exog_cols.extend(['dayofweek_sin', 'dayofweek_cos'])

    target_scaler = MinMaxScaler()
    scaled_target = target_scaler.fit_transform(train_df[[target_col]])
    train_df['scaled_target'] = scaled_target
    exog_scaler = MinMaxScaler()
    scaled_exog_train = exog_scaler.fit_transform(train_df[exog_cols])
    scaled_exog_future = exog_scaler.transform(future_df[exog_cols])

    exog_train_df = pd.DataFrame(scaled_exog_train, columns=exog_cols)
    exog_future_df = pd.DataFrame(scaled_exog_future, columns=exog_cols)

    X_past, X_future, y = prepare_lstm_data(train_df['scaled_target'], exog_train_df, lookback, horizon)

    if len(X_past) == 0:
        return np.zeros(horizon)

    num_exog = len(exog_cols)
    input_past = Input(shape=(lookback, 1 + num_exog))
    input_future = Input(shape=(horizon * num_exog,))
    lstm_out = LSTM(64, activation='relu')(input_past)
    concat = Concatenate()([lstm_out, input_future])
    dense1 = Dense(64, activation='relu')(concat)
    output = Dense(horizon)(dense1)

    model = Model(inputs=[input_past, input_future], outputs=output)
    model.compile(optimizer='adam', loss='mse')
    model.fit([X_past, X_future], y, epochs=50, batch_size=16, verbose=0)

    past_target = train_df['scaled_target'].values[-lookback:].reshape(-1, 1)
    past_exog = exog_train_df.values[-lookback:]
    past_features = np.hstack([past_target, past_exog])
    X_past_pred = np.array([past_features])
    future_exog = exog_future_df.values.flatten()
    X_future_pred = np.array([future_exog])

    pred_scaled = model.predict([X_past_pred, X_future_pred], verbose=0)[0]
    inv_predictions = target_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()
    return inv_predictions

# Bulan-bulan yang divalidasi: (year, month, nama_bulan)
VALIDATION_MONTHS = [
    (2025, 10, 'Oktober'),
    (2025, 11, 'November'),
    (2025, 12, 'Desember'),
]

def validate_class_month(class_name, dept, class_df, year, month, month_name):
    """Validasi satu bulan tertentu sebagai test set."""
    print(f"\n{'='*55}")
    print(f"Dept: {dept.upper()} | Class: {class_name} | Test: {month_name} {year}")
    print(f"{'='*55}")

    # Tentukan test set = seluruh hari di bulan & tahun tersebut
    mask_test = (class_df['Date'].dt.year == year) & (class_df['Date'].dt.month == month)
    test_df  = class_df[mask_test].reset_index(drop=True)
    # Train set = semua data sebelum bulan test
    train_df = class_df[class_df['Date'] < test_df['Date'].min()].reset_index(drop=True)

    if len(test_df) == 0:
        print(f"  Tidak ada data untuk {month_name} {year}. Dilewati.")
        return []
    if len(train_df) < LOOKBACK + HORIZON:
        print(f"  Data training tidak cukup untuk {month_name} {year}. Dilewati.")
        return []

    print(f"  Train: {len(train_df)} hari | Test: {len(test_df)} hari "
          f"({test_df['Date'].min().date()} s.d. {test_df['Date'].max().date()})")

    # Masking periode anomali September 2025 pada data training sebelum fitting model
    print(f"  Anomaly masking pada training data:")
    train_df = train_df.copy()
    train_df['Sales']     = mask_anomaly_period(train_df, 'Sales',     window=30)
    train_df['Sales Qty'] = mask_anomaly_period(train_df, 'Sales Qty', window=30)

    metrics_summary = []

    for target in ['Sales', 'Sales Qty']:
        print(f"\n--- [{month_name}] Training Models for [{target}] ---")
        y_actual = test_df[target].values

        # SARIMAX perlu steps = len(test_df)
        sarimax_pred, sarimax_fitted, sarimax_resid = train_predict_sarimax(
            train_df, test_df, use_promo=True, target_col=target
        )

        print(f"  Training LSTM ({target})...")
        lstm_pred = train_predict_lstm(
            train_df, test_df, use_promo=True, target_col=target
        )

        print(f"  Training Hybrid ({target})...")
        train_df_hybrid = train_df.copy()
        train_df_hybrid['SARIMAX_Residual'] = sarimax_resid
        hybrid_lstm_pred = train_predict_lstm(
            train_df_hybrid, test_df, use_promo=True, target_col='SARIMAX_Residual'
        )
        hybrid_pred = sarimax_pred + hybrid_lstm_pred

        predictions_dict = {
            'SARIMAX': sarimax_pred,
            'LSTM': lstm_pred,
            'Hybrid': hybrid_pred
        }

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

        # --- Plot Gabungan (semua model) ---
        test_dates   = test_df['Date']
        fname_suffix = target.replace(' ', '')
        month_tag    = month_name.lower()

        def _save_plot(ax, fig, suffix):
            ax.set_xlabel("Tanggal")
            ax.set_ylabel(target)
            ax.legend()
            ax.grid(True, alpha=0.4)
            fig.autofmt_xdate()
            plt.tight_layout()
            path = os.path.join(OUTPUT_DIR, suffix)
            plt.savefig(path, dpi=150)
            plt.close()
            print(f"  Plot disimpan: {path}")

        # 1. Gabungan
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(test_dates, y_actual,     label=f'Actual {target}',    marker='o', color='black',      linewidth=2)
        ax.plot(test_dates, sarimax_pred, label='SARIMAX',             linestyle='--', color='steelblue')
        ax.plot(test_dates, lstm_pred,    label='LSTM',                linestyle='--', color='darkorange')
        ax.plot(test_dates, hybrid_pred,  label='Hybrid SARIMAX-LSTM', linestyle='-.', color='green')
        ax.set_title(
            f"Validasi {month_name} {year} ({target}) — Dept: {dept.upper()} | Class: {class_name}",
            fontsize=13
        )
        _save_plot(ax, fig,
            f"opt_val_plot_{dept}_class_{class_name}_{month_tag}_{fname_suffix}.png")

        # 2. Actual vs SARIMAX
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(test_dates, y_actual,     label=f'Actual {target}', marker='o', color='black',    linewidth=2)
        ax.plot(test_dates, sarimax_pred, label='SARIMAX',           linestyle='--', color='steelblue', linewidth=2)
        ax.set_title(
            f"Actual vs SARIMAX — {month_name} {year} ({target}) | Dept: {dept.upper()} | Class: {class_name}",
            fontsize=13
        )
        _save_plot(ax, fig,
            f"opt_val_plot_{dept}_class_{class_name}_{month_tag}_{fname_suffix}_SARIMAX.png")

        # 3. Actual vs LSTM
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(test_dates, y_actual,  label=f'Actual {target}', marker='o', color='black',      linewidth=2)
        ax.plot(test_dates, lstm_pred, label='LSTM',              linestyle='--', color='darkorange', linewidth=2)
        ax.set_title(
            f"Actual vs LSTM — {month_name} {year} ({target}) | Dept: {dept.upper()} | Class: {class_name}",
            fontsize=13
        )
        _save_plot(ax, fig,
            f"opt_val_plot_{dept}_class_{class_name}_{month_tag}_{fname_suffix}_LSTM.png")

        # 4. Actual vs Hybrid
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(test_dates, y_actual,    label=f'Actual {target}',    marker='o', color='black', linewidth=2)
        ax.plot(test_dates, hybrid_pred, label='Hybrid SARIMAX-LSTM', linestyle='-.', color='green', linewidth=2)
        ax.set_title(
            f"Actual vs Hybrid SARIMAX-LSTM — {month_name} {year} ({target}) | Dept: {dept.upper()} | Class: {class_name}",
            fontsize=13
        )
        _save_plot(ax, fig,
            f"opt_val_plot_{dept}_class_{class_name}_{month_tag}_{fname_suffix}_Hybrid.png")

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

    if len(class_df) <= HORIZON * 2 + LOOKBACK:
        print(f"Skipping {dept} Class {class_name}: Not enough data.")
        return []

    all_metrics = []
    for year, month, month_name in VALIDATION_MONTHS:
        metrics = validate_class_month(class_name, dept, class_df, year, month, month_name)
        all_metrics.extend(metrics)

    return all_metrics

def main():
    classes = ['A']
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
        metrics_csv_path = os.path.join(OUTPUT_DIR, "opt_validation_metrics_summary.csv")
        df_metrics.to_csv(metrics_csv_path, index=False)
        print(f"\nMetrics summary disimpan ke: {metrics_csv_path}")
        print(df_metrics.to_string(index=False))

if __name__ == "__main__":
    main()
