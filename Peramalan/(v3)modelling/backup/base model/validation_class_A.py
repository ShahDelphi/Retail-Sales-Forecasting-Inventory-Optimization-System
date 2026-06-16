import os
import pandas as pd
import numpy as np
from datetime import timedelta
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
import warnings
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import LSTM, Dense # type: ignore
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "validation_output")
HORIZON = 30
LOOKBACK = 14  
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Error Metrics
def compute_mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    # avoid division by zero
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

# Reused training functions
def train_predict_sarimax(train_df, future_df, use_promo=False):
    endog = train_df['Sales']
    exog_cols = ['Weekend', 'Promo'] if use_promo else ['Weekend']
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

def prepare_lstm_data(series, exog_df, lookback):
    X, y = [], []
    series_vals = series.values
    exog_vals = exog_df.values
    
    for i in range(len(series_vals) - lookback):
        lag_features = series_vals[i:i+lookback]
        current_exog = exog_vals[i+lookback]
        merged_features = np.concatenate([lag_features, current_exog])
        X.append(merged_features)
        y.append(series_vals[i+lookback])
        
    return np.array(X), np.array(y)

def train_predict_lstm(train_df, future_df, lookback=LOOKBACK, use_promo=True, target_col='Sales'):
    exog_cols = ['Weekend', 'Promo'] if use_promo else ['Weekend']
    
    train_df = train_df.copy()
    train_df['dayofweek'] = train_df['Date'].dt.dayofweek
    exog_cols.append('dayofweek')
    
    future_df = future_df.copy()
    future_df['dayofweek'] = future_df['Date'].dt.dayofweek
    
    target_scaler = MinMaxScaler()
    scaled_target = target_scaler.fit_transform(train_df[[target_col]])
    train_df['scaled_target'] = scaled_target
    
    exog_scaler = MinMaxScaler()
    scaled_exog_train = exog_scaler.fit_transform(train_df[exog_cols])
    scaled_exog_future = exog_scaler.transform(future_df[exog_cols])
    
    exog_train_df = pd.DataFrame(scaled_exog_train, columns=exog_cols)
    exog_future_df = pd.DataFrame(scaled_exog_future, columns=exog_cols)
    
    X_train, y_train = prepare_lstm_data(train_df['scaled_target'], exog_train_df, lookback)
    X_train = np.reshape(X_train, (X_train.shape[0], 1, X_train.shape[1]))
    
    model = Sequential()
    model.add(LSTM(64, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    
    model.fit(X_train, y_train, epochs=30, batch_size=16, verbose=0)
    
    predictions = []
    last_lags = list(train_df['scaled_target'].values[-lookback:])
    
    for i in range(len(future_df)):
        current_exog = exog_future_df.iloc[i].values
        features = np.concatenate([last_lags, current_exog])
        features_reshaped = np.reshape(features, (1, 1, len(features)))
        
        pred_scaled = model.predict(features_reshaped, verbose=0)[0][0]
        predictions.append(pred_scaled)
        
        last_lags.pop(0)
        last_lags.append(pred_scaled)
        
    predictions = np.array(predictions).reshape(-1, 1)
    inv_predictions = target_scaler.inverse_transform(predictions).flatten()
    return inv_predictions

def validate_class(class_name, dept, file_path):
    print(f"\n{'='*50}")
    print(f"Validating Dept: {dept.upper()}, Class: {class_name}")
    print(f"{'='*50}")
    
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Weekend'] = df['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    
    class_df = df.groupby('Date').agg(
        Sales=('Sales', 'sum'),
        Promo=('Promo', 'max'),
        Weekend=('Weekend', 'max')
    ).reset_index()
    
    class_df = class_df.sort_values('Date').reset_index(drop=True)
    
    # Train-test split (hold out last HORIZON days)
    if len(class_df) <= HORIZON + LOOKBACK:
        print(f"Skipping {dept} Class {class_name}: Not enough data for validation.")
        return
        
    train_df = class_df.iloc[:-HORIZON].reset_index(drop=True)
    test_df = class_df.iloc[-HORIZON:].reset_index(drop=True)
    y_actual = test_df['Sales'].values
    
    print(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")
    
    print("\n--- Training Models ---")
    # 1. SARIMAX
    sarimax_pred, sarimax_fitted, sarimax_resid = train_predict_sarimax(train_df, test_df, use_promo=True)
    
    # 2. LSTM
    print("Training LSTM...")
    lstm_pred = train_predict_lstm(train_df, test_df, use_promo=True, target_col='Sales')
    
    # 3. Hybrid
    print("Training Hybrid SARIMAX-LSTM...")
    train_df_hybrid = train_df.copy()
    train_df_hybrid['SARIMAX_Residual'] = sarimax_resid
    hybrid_lstm_pred = train_predict_lstm(train_df_hybrid, test_df, use_promo=True, target_col='SARIMAX_Residual')
    hybrid_pred = sarimax_pred + hybrid_lstm_pred
    
    predictions_dict = {
        'SARIMAX': sarimax_pred,
        'LSTM': lstm_pred,
        'Hybrid': hybrid_pred
    }
    
    test_dates = test_df['Date']
    
    # --- 1. & 2. ERROR METRICS & RANGE CHECK ---
    print("\n[ Range Check ]")
    print_range_check("Actual Sales", y_actual)
    for model_name, preds in predictions_dict.items():
        print_range_check(f"Pred {model_name}", preds)
        
    print("\n[ Error Metrics ]")
    metrics_summary = []
    for model_name, preds in predictions_dict.items():
        mape_val = compute_mape(y_actual, preds)
        mae_val = compute_mae(y_actual, preds)
        rmse_val = compute_rmse(y_actual, preds)
        
        print(f"  {model_name:10} -> MAPE: {mape_val:6.2f}%, MAE: {mae_val:9.2f}, RMSE: {rmse_val:9.2f}")
        metrics_summary.append({
            'Dept': dept,
            'Class': class_name,
            'Model': model_name,
            'MAPE': mape_val,
            'MAE': mae_val,
            'RMSE': rmse_val
        })
    
    # --- 3. PLOT ACTUAL VS PREDICTION ---
    plt.figure(figsize=(12, 6))
    plt.plot(test_dates, y_actual, label='Actual', marker='o', color='black', linewidth=2)
    plt.plot(test_dates, sarimax_pred, label='SARIMAX', linestyle='--')
    plt.plot(test_dates, lstm_pred, label='LSTM', linestyle='--')
    plt.plot(test_dates, hybrid_pred, label='Hybrid', linestyle='-.')
    
    plt.title(f"Validation (Last {HORIZON} Days) - Dept: {dept.upper()} | Class: {class_name}")
    plt.xlabel("Date")
    plt.ylabel("Sales")
    plt.legend()
    plt.grid(True, alpha=0.5)
    
    plot_path = os.path.join(OUTPUT_DIR, f"val_plot_{dept}_class_{class_name}.png")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"\n=> Plot saved to {plot_path}")
    
    return metrics_summary


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
                print(f"File not found for Dept {dept}, Class {cls}: {file_path}")
                
    if all_metrics:
        df_metrics = pd.DataFrame(all_metrics)
        metrics_csv_path = os.path.join(OUTPUT_DIR, "validation_metrics_summary.csv")
        df_metrics.to_csv(metrics_csv_path, index=False)
        print(f"\nAll error metrics saved to {metrics_csv_path}")

if __name__ == "__main__":
    main()
