import os
import time
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

def train_predict_sarimax(train_df, future_df, use_promo=False, target_col='Sales'):
    endog = train_df[target_col]
    exog_cols = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours', 'NYE'] if use_promo else ['Weekend', 'Holiday', 'Operating_Hours', 'NYE']
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
    exog_cols = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours', 'NYE'] if use_promo else ['Weekend', 'Holiday', 'Operating_Hours', 'NYE']
    
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
    
    X_past, X_future, y = prepare_lstm_data(train_df['scaled_target'], exog_train_df, lookback, HORIZON)
    
    if len(X_past) == 0:
        return np.zeros(HORIZON)
        
    num_exog = len(exog_cols)
    input_past = Input(shape=(lookback, 1 + num_exog))
    input_future = Input(shape=(HORIZON * num_exog,))
    lstm_out = LSTM(64, activation='relu')(input_past)
    concat = Concatenate()([lstm_out, input_future])
    dense1 = Dense(64, activation='relu')(concat)
    output = Dense(HORIZON)(dense1)
    
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

def validate_class(class_name, dept, file_path):
    print(f"\n{'='*50}")
    print(f"Validating Dept: {dept.upper()}, Class: {class_name}")
    print(f"{'='*50}")
    
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    id_holidays = holidays.country_holidays('ID')
    df['Weekend'] = df['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df['Holiday'] = df['Date'].apply(lambda x: 1 if x in id_holidays else 0)
    df['Operating_Hours'] = df['Date'].apply(
        lambda x: 10 if id_holidays.get(x) == 'Hari Raya Idul Fitri'
                 else (16 if (x.month == 12 and x.day == 31) else 14)
    )
    df['NYE'] = ((df['Date'].dt.month == 12) & (df['Date'].dt.day == 31)).astype(int)
    
    class_df = df.groupby('Date').agg(
        Sales=('Sales', 'sum'),
        Sales_Qty=('Sales Qty', 'sum'),
        Promo=('Promo', 'max'),
        Weekend=('Weekend', 'max'),
        Holiday=('Holiday', 'max'),
        Operating_Hours=('Operating_Hours', 'max'),
        NYE=('NYE', 'max')
    ).reset_index()
    class_df = class_df.rename(columns={'Sales_Qty': 'Sales Qty'})
    class_df = class_df.sort_values('Date').reset_index(drop=True)
    
    if len(class_df) <= HORIZON * 2 + LOOKBACK:
        print(f"Skipping {dept} Class {class_name}: Not enough data for validation.")
        return []
        
    train_df = class_df.iloc[:-HORIZON].reset_index(drop=True)
    test_df = class_df.iloc[-HORIZON:].reset_index(drop=True)
    
    print(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")
    metrics_summary = []
    
    for target in ['Sales', 'Sales Qty']:
        print(f"\n--- Training Models for [{target}] ---")
        y_actual = test_df[target].values
        
        start_t = time.time()
        sarimax_pred, sarimax_fitted, sarimax_resid = train_predict_sarimax(train_df, test_df, use_promo=True, target_col=target)
        sarimax_time = time.time() - start_t
        
        print(f"Training LSTM ({target})...")
        start_t = time.time()
        lstm_pred = train_predict_lstm(train_df, test_df, use_promo=True, target_col=target)
        lstm_time = time.time() - start_t
        
        print(f"Training Hybrid ({target})...")
        start_t = time.time()
        train_df_hybrid = train_df.copy()
        train_df_hybrid['SARIMAX_Residual'] = sarimax_resid
        hybrid_lstm_pred = train_predict_lstm(train_df_hybrid, test_df, use_promo=True, target_col='SARIMAX_Residual')
        hybrid_pred = sarimax_pred + hybrid_lstm_pred
        hybrid_time = sarimax_time + (time.time() - start_t)
        
        predictions_dict = {
            'SARIMAX': sarimax_pred,
            'LSTM': lstm_pred,
            'Hybrid': hybrid_pred
        }
        
        time_dict = {
            'SARIMAX': sarimax_time,
            'LSTM': lstm_time,
            'Hybrid': hybrid_time
        }
        
        print(f"\n[ Range Check: {target} ]")
        print_range_check(f"Actual {target}", y_actual)
        for model_name, preds in predictions_dict.items():
            print_range_check(f"Pred {model_name}", preds)
            
        print(f"\n[ Error Metrics: {target} ]")
        for model_name, preds in predictions_dict.items():
            mape_val = compute_mape(y_actual, preds)
            mae_val = compute_mae(y_actual, preds)
            rmse_val = compute_rmse(y_actual, preds)
            
            print(f"  {model_name:10} -> MAPE: {mape_val:6.2f}%, MAE: {mae_val:9.2f}, RMSE: {rmse_val:9.2f}, Time: {time_dict[model_name]:.2f}s")
            metrics_summary.append({
                'Dept': dept,
                'Class': class_name,
                'Target': target,
                'Model': model_name,
                'MAPE': mape_val,
                'MAE': mae_val,
                'RMSE': rmse_val,
                'Time (s)': time_dict[model_name]
            })
        
        test_dates = test_df['Date']
        plt.figure(figsize=(12, 6))
        plt.plot(test_dates, y_actual, label=f'Actual {target}', marker='o', color='black', linewidth=2)
        plt.plot(test_dates, sarimax_pred, label='SARIMAX', linestyle='--')
        plt.plot(test_dates, lstm_pred, label='LSTM', linestyle='--')
        plt.plot(test_dates, hybrid_pred, label='Hybrid', linestyle='-.')
        
        plt.title(f"Optimized Validation ({target}) - Dept: {dept.upper()} | Class: {class_name}")
        plt.xlabel("Date")
        plt.ylabel(target)
        plt.legend()
        plt.grid(True, alpha=0.5)
        
        fname_suffix = target.replace(' ', '')
        class_output_dir = os.path.join(OUTPUT_DIR, f"class_{class_name}")
        if not os.path.exists(class_output_dir):
            os.makedirs(class_output_dir)
        plot_path = os.path.join(class_output_dir, f"opt_val_plot_{dept}_class_{class_name}_{fname_suffix}.png")
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()
    
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
            
    if all_metrics:
        df_metrics = pd.DataFrame(all_metrics)
        for cls in classes:
            cls_metrics = df_metrics[df_metrics['Class'] == cls]
            if not cls_metrics.empty:
                class_output_dir = os.path.join(OUTPUT_DIR, f"class_{cls}")
                if not os.path.exists(class_output_dir):
                    os.makedirs(class_output_dir)
                metrics_csv_path = os.path.join(class_output_dir, f"opt_validation_metrics_summary_class_{cls}.csv")
                cls_metrics.to_csv(metrics_csv_path, index=False)
                
        model_comp_dir = os.path.join(CURR_DIR, "model comparison")
        if not os.path.exists(model_comp_dir):
            os.makedirs(model_comp_dir)
            
        df_time_comp = df_metrics.sort_values(by=['Dept', 'Class', 'Target', 'Time (s)'])
        comp_csv_path = os.path.join(model_comp_dir, "computation_time_comparison_class_A.csv")
        df_time_comp.to_csv(comp_csv_path, index=False)

if __name__ == "__main__":
    main()
