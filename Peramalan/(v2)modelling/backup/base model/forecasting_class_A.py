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

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "forecast_output")
HORIZON = 30
LOOKBACK = 14  # Window size for LSTM lag features
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def create_future_dataframe(last_date, horizon):
    """Create a dataframe of future dates with weekend feature."""
    future_dates = [last_date + timedelta(days=x) for x in range(1, horizon + 1)]
    df_future = pd.DataFrame({'Date': future_dates})
    df_future['Weekend'] = df_future['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df_future['Promo'] = 0  # Assume no future promo if unknown
    return df_future

def train_predict_sarimax(train_df, future_df, use_promo=False):
    """Train and predict using SARIMAX."""
    endog = train_df['Sales']
    exog_cols = ['Weekend', 'Promo'] if use_promo else ['Weekend']
    exog_train = train_df[exog_cols]
    exog_future = future_df[exog_cols]
    
    print(f"Training SARIMAX {SARIMAX_ORDER} x {SARIMAX_SEASONAL} with exog: {exog_cols}")
    model = sm.tsa.statespace.SARIMAX(
        endog,
        exog=exog_train,
        order=SARIMAX_ORDER,
        seasonal_order=SARIMAX_SEASONAL,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    result = model.fit(disp=False)
    
    # Store fitted and residuals
    fitted_vals = result.fittedvalues
    residuals = result.resid
    
    # Predict future
    forecast = result.get_forecast(steps=HORIZON, exog=exog_future)
    pred_mean = forecast.predicted_mean
    return pred_mean.values, fitted_vals.values, residuals.values

def prepare_lstm_data(series, exog_df, lookback):
    """Prepare data for LSTM."""
    X, y = [], []
    series_vals = series.values
    exog_vals = exog_df.values
    
    for i in range(len(series_vals) - lookback):
        # Features: lags of target + exog features (weekend, promo, etc.) of the target date
        lag_features = series_vals[i:i+lookback]
        current_exog = exog_vals[i+lookback]
        merged_features = np.concatenate([lag_features, current_exog])
        X.append(merged_features)
        y.append(series_vals[i+lookback])
        
    return np.array(X), np.array(y)

def train_predict_lstm(train_df, future_df, lookback=LOOKBACK, use_promo=True, target_col='Sales'):
    """Train and predict using LSTM model iteratively."""
    print(f"Training LSTM for target: {target_col}")
    exog_cols = ['Weekend', 'Promo'] if use_promo else ['Weekend']
    
    # Add calendar features
    train_df = train_df.copy()
    train_df['dayofweek'] = train_df['Date'].dt.dayofweek
    exog_cols.append('dayofweek')
    
    future_df = future_df.copy()
    future_df['dayofweek'] = future_df['Date'].dt.dayofweek
    
    # Scale Target
    target_scaler = MinMaxScaler()
    scaled_target = target_scaler.fit_transform(train_df[[target_col]])
    train_df['scaled_target'] = scaled_target
    
    # Scale Exog (weekend, promo, dayofweek)
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
    
    # Iterative prediction
    predictions = []
    # Get last `lookback` scaled target values
    last_lags = list(train_df['scaled_target'].values[-lookback:])
    
    for i in range(HORIZON):
        current_exog = exog_future_df.iloc[i].values
        features = np.concatenate([last_lags, current_exog])
        features_reshaped = np.reshape(features, (1, 1, len(features)))
        
        pred_scaled = model.predict(features_reshaped, verbose=0)[0][0]
        predictions.append(pred_scaled)
        
        # Update lags: drop oldest, append newly predicted
        last_lags.pop(0)
        last_lags.append(pred_scaled)
        
    predictions = np.array(predictions).reshape(-1, 1)
    # Inverse transform
    inv_predictions = target_scaler.inverse_transform(predictions).flatten()
    return inv_predictions

def process_class(class_name, dept, file_path):
    print(f"\nProcessing Dept {dept}, Class {class_name}...")
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate historical proportion of each SKU
    print("Calculating historical proportion...")
    sku_sales = df.groupby(['SKU', 'SKU Name', 'Dept', 'Dept Name', 'Category'])['Sales'].sum().reset_index()
    total_sales = sku_sales['Sales'].sum()
    sku_sales['Proportion'] = sku_sales['Sales'] / total_sales
    sku_metadata = sku_sales.drop(columns=['Sales'])
    
    # Aggregate data to class level
    print("Aggregating data to class level...")
    df['Weekend'] = df['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    
    class_df = df.groupby('Date').agg(
        Sales=('Sales', 'sum'),
        Promo=('Promo', 'max'),
        Weekend=('Weekend', 'max')
    ).reset_index()
    
    class_df = class_df.sort_values('Date').reset_index(drop=True)
    
    last_date = class_df['Date'].max()
    future_df = create_future_dataframe(last_date, HORIZON)
    
    forecasts = {}
    
    # 1. SARIMAX
    print("\n--- Modeling Class A: SARIMAX ---")
    sarimax_pred, sarimax_fitted, sarimax_resid = train_predict_sarimax(class_df, future_df, use_promo=True)
    forecasts['Predicted_Sales_SARIMAX'] = sarimax_pred
    
    # 2. LSTM
    print("\n--- Modeling Class A: LSTM ---")
    lstm_pred = train_predict_lstm(class_df, future_df, use_promo=True, target_col='Sales')
    forecasts['Predicted_Sales_LSTM'] = lstm_pred
    
    # 3. Hybrid SARIMAX - LSTM
    print("\n--- Modeling Class A: Hybrid SARIMAX-LSTM ---")
    # Add residual to class_df to train LSTM
    class_df_hybrid = class_df.copy()
    class_df_hybrid['SARIMAX_Residual'] = sarimax_resid
    hybrid_lstm_pred = train_predict_lstm(class_df_hybrid, future_df, use_promo=True, target_col='SARIMAX_Residual')
    hybrid_pred = sarimax_pred + hybrid_lstm_pred
    forecasts['Predicted_Sales_Hybrid'] = hybrid_pred
        
    # Distribute forecasts to SKU level
    print("\nDistributing forecasts to SKU level...")
    all_results = []
    
    for i, row in future_df.iterrows():
        current_date = row['Date']
        for _, sku_row in sku_metadata.iterrows():
            result_row = {
                'Date': current_date.strftime('%Y-%m-%d'),
                'SKU': sku_row['SKU'],
                'SKU Name': sku_row['SKU Name'],
                'Dept': sku_row['Dept'],
                'Dept Name': sku_row['Dept Name'],
                'Category': sku_row['Category']
            }
            # Distribute each forecast method proportionally
            for method, pred_values in forecasts.items():
                predicted_total = pred_values[i]
                # Avoid negative forecasts (can happen with ARIMA/LSTM)
                predicted_total = max(0, predicted_total)
                result_row[method] = predicted_total * sku_row['Proportion']
            
            all_results.append(result_row)
            
    final_df = pd.DataFrame(all_results)
    
    # Save output
    output_path = os.path.join(OUTPUT_DIR, f"forecast_{dept}_class_{class_name}.csv")
    final_df.to_csv(output_path, index=False)
    print(f"Saved forecasts for Dept {dept}, Class {class_name} to {output_path}")


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
