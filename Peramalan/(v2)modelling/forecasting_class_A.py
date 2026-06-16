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
import holidays

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "forecast_output")
HORIZON = 30
LOOKBACK = 14  
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def create_future_dataframe(last_date, horizon):
    id_holidays = holidays.country_holidays('ID')
    future_dates = [last_date + timedelta(days=x) for x in range(1, horizon + 1)]
    df_future = pd.DataFrame({'Date': future_dates})
    df_future['Weekend'] = df_future['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df_future['Holiday'] = df_future['Date'].apply(lambda x: 1 if x in id_holidays else 0)
    df_future['Promo'] = 0  
    return df_future

def train_predict_sarimax(train_df, future_df, use_promo=False, target_col='Sales'):
    endog = train_df[target_col]
    exog_cols = ['Weekend', 'Holiday', 'Promo'] if use_promo else ['Weekend', 'Holiday']
    exog_train = train_df[exog_cols]
    exog_future = future_df[exog_cols]
    
    print(f"  Training SARIMAX {SARIMAX_ORDER} x {SARIMAX_SEASONAL} with exog: {exog_cols}")
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
    print(f"  Training LSTM for target: {target_col}")
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
    
    X_past, X_future, y = prepare_lstm_data(train_df['scaled_target'], exog_train_df, lookback, HORIZON)
    
    if len(X_past) == 0:
        print("  Not enough samples to train.")
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

def process_class(class_name, dept, file_path):
    print(f"\n[{dept.upper()} - CLASS {class_name}] Processing...")
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    print("Calculating dual-target historical proportions...")
    sku_sales = df.groupby(['Store', 'SKU', 'SKU Name', 'Dept', 'Dept Name', 'Category']).agg(
        Sales=('Sales', 'sum'),
        Sales_Qty=('Sales Qty', 'sum')
    ).reset_index()
    
    total_sales = sku_sales['Sales'].sum()
    total_qty = sku_sales['Sales_Qty'].sum()
    
    # Safe division mapping to avoid Nans
    sku_sales['Proportion_Sales'] = np.where(total_sales > 0, sku_sales['Sales'] / total_sales, 0)
    sku_sales['Proportion_Qty'] = np.where(total_qty > 0, sku_sales['Sales_Qty'] / total_qty, 0)
    sku_metadata = sku_sales.drop(columns=['Sales', 'Sales_Qty'])
    
    print("Aggregating data to class level...")
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
    
    last_date = class_df['Date'].max()
    future_df = create_future_dataframe(last_date, HORIZON)
    
    forecasts = {}
    target_cols = ['Sales', 'Sales Qty']
    
    for target in target_cols:
        target_suffix = "Sales" if target == 'Sales' else "Qty"
        
        # 1. SARIMAX
        print(f"\n--- Modeling Class A: SARIMAX ({target}) ---")
        sarimax_pred, sarimax_fitted, sarimax_resid = train_predict_sarimax(class_df, future_df, use_promo=True, target_col=target)
        forecasts[f'Predicted_{target_suffix}_SARIMAX'] = sarimax_pred
        
        # 2. LSTM
        print(f"\n--- Modeling Class A: LSTM ({target}) ---")
        lstm_pred = train_predict_lstm(class_df, future_df, use_promo=True, target_col=target)
        forecasts[f'Predicted_{target_suffix}_LSTM'] = lstm_pred
        
        # 3. Hybrid SARIMAX - LSTM
        print(f"\n--- Modeling Class A: Hybrid SARIMAX-LSTM ({target}) ---")
        class_df_hybrid = class_df.copy()
        class_df_hybrid['SARIMAX_Residual'] = sarimax_resid
        hybrid_lstm_pred = train_predict_lstm(class_df_hybrid, future_df, use_promo=True, target_col='SARIMAX_Residual')
        hybrid_pred = sarimax_pred + hybrid_lstm_pred
        forecasts[f'Predicted_{target_suffix}_Hybrid'] = hybrid_pred
        
    print("\nDistributing dual-target forecasts to SKU level...")
    all_results = []
    
    for i, row in future_df.iterrows():
        current_date = row['Date']
        for _, sku_row in sku_metadata.iterrows():
            result_row = {
                'Date': current_date.strftime('%Y-%m-%d'),
                'Store': sku_row['Store'],
                'SKU': sku_row['SKU'],
                'SKU Name': sku_row['SKU Name'],
                'Dept': sku_row['Dept'],
                'Dept Name': sku_row['Dept Name'],
                'Category': sku_row['Category']
            }
            
            for method, pred_values in forecasts.items():
                predicted_total = max(0, pred_values[i])
                if '_Sales_' in method:
                    result_row[method] = int(round(predicted_total * sku_row['Proportion_Sales']))
                else:
                    result_row[method] = round(predicted_total * sku_row['Proportion_Qty'], 2)
            
            all_results.append(result_row)
            
    final_df = pd.DataFrame(all_results)
    output_path = os.path.join(OUTPUT_DIR, f"forecast_{dept}_class_{class_name}.csv")
    final_df.to_csv(output_path, index=False)
    print(f"Saved dual-target forecasts for Dept {dept}, Class {class_name} to {output_path}")

def main():
    classes = ['A']
    for dept in DEPARTMENTS:
        dept_data_dir = os.path.join(BASE_DATA_DIR, dept)
        for cls in classes:
            file_path = os.path.join(dept_data_dir, f"timeseries_{cls}.csv")
            if os.path.exists(file_path):
                process_class(cls, dept, file_path)
            else:
                print(f"File not found for Dept {dept}, Class {cls}: {file_path}")

if __name__ == "__main__":
    main()
