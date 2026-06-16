import os
import pandas as pd
import numpy as np
from datetime import timedelta
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
import warnings
import tensorflow as tf
from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate  # type: ignore
from tensorflow.keras.models import Model  # type: ignore
import holidays

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "forecast_output", "class_BC_LSTM")
HORIZON = 30
LOOKBACK = 14
SARIMAX_ORDER = (1, 1, 1)
SARIMAX_SEASONAL = (1, 1, 1, 7)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ── Future Dataframe ───────────────────────────────────────────────────────────
def create_future_dataframe(last_date, horizon):
    id_holidays = holidays.country_holidays('ID')
    future_dates = [last_date + timedelta(days=x) for x in range(1, horizon + 1)]
    df_future = pd.DataFrame({'Date': future_dates})
    df_future['Weekend'] = df_future['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    df_future['Holiday'] = df_future['Date'].apply(lambda x: 1 if x in id_holidays else 0)
    df_future['Promo'] = 0
    df_future['Operating_Hours'] = df_future['Date'].apply(
        lambda x: 10 if id_holidays.get(x) == 'Hari Raya Idul Fitri'
                 else (16 if (x.month == 12 and x.day == 31) else 14)
    )
    df_future['NYE'] = ((df_future['Date'].dt.month == 12) & (df_future['Date'].dt.day == 31)).astype(int)
    return df_future

# ── SARIMAX ────────────────────────────────────────────────────────────────────
def train_predict_sarimax(train_df, future_df, target_col='Sales'):
    endog = train_df[target_col]
    exog_cols = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours', 'NYE']
    model = sm.tsa.statespace.SARIMAX(
        endog,
        exog=train_df[exog_cols],
        order=SARIMAX_ORDER,
        seasonal_order=SARIMAX_SEASONAL,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    result = model.fit(disp=False)
    fitted_vals = result.fittedvalues
    residuals   = result.resid
    forecast = result.get_forecast(steps=HORIZON, exog=future_df[exog_cols])
    return forecast.predicted_mean.values, fitted_vals.values, residuals.values

# ── LSTM ───────────────────────────────────────────────────────────────────────
def prepare_lstm_data(series, exog_df, lookback, horizon):
    X_past, X_future, y = [], [], []
    series_vals = series.values
    exog_vals   = exog_df.values

    for i in range(len(series_vals) - lookback - horizon + 1):
        past_target   = series_vals[i:i + lookback].reshape(-1, 1)
        past_exog     = exog_vals[i:i + lookback]
        past_features = np.hstack([past_target, past_exog])
        future_exog   = exog_vals[i + lookback: i + lookback + horizon].flatten()
        X_past.append(past_features)
        X_future.append(future_exog)
        y.append(series_vals[i + lookback: i + lookback + horizon])

    return np.array(X_past), np.array(X_future), np.array(y)

def train_predict_lstm(train_df, future_df, lookback=LOOKBACK, target_col='Sales'):
    horizon   = len(future_df)
    exog_cols = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours', 'NYE']

    train_df = train_df.copy()
    train_df['dayofweek_sin'] = np.sin(2 * np.pi * train_df['Date'].dt.dayofweek / 7)
    train_df['dayofweek_cos'] = np.cos(2 * np.pi * train_df['Date'].dt.dayofweek / 7)
    future_df = future_df.copy()
    future_df['dayofweek_sin'] = np.sin(2 * np.pi * future_df['Date'].dt.dayofweek / 7)
    future_df['dayofweek_cos'] = np.cos(2 * np.pi * future_df['Date'].dt.dayofweek / 7)
    exog_cols = exog_cols + ['dayofweek_sin', 'dayofweek_cos']

    target_scaler = MinMaxScaler()
    scaled_target = target_scaler.fit_transform(train_df[[target_col]])
    train_df['scaled_target'] = scaled_target

    exog_scaler = MinMaxScaler()
    scaled_exog_train  = exog_scaler.fit_transform(train_df[exog_cols])
    scaled_exog_future = exog_scaler.transform(future_df[exog_cols])

    exog_train_df  = pd.DataFrame(scaled_exog_train,  columns=exog_cols)
    exog_future_df = pd.DataFrame(scaled_exog_future, columns=exog_cols)

    X_past, X_future_arr, y = prepare_lstm_data(
        train_df['scaled_target'], exog_train_df, lookback, horizon
    )

    if len(X_past) == 0:
        return np.zeros(horizon)

    num_exog     = len(exog_cols)
    input_past   = Input(shape=(lookback, 1 + num_exog))
    input_future = Input(shape=(horizon * num_exog,))
    lstm_out = LSTM(64, activation='relu')(input_past)
    concat   = Concatenate()([lstm_out, input_future])
    dense1   = Dense(64, activation='relu')(concat)
    output   = Dense(horizon)(dense1)

    model = Model(inputs=[input_past, input_future], outputs=output)
    model.compile(optimizer='adam', loss='mse')
    model.fit([X_past, X_future_arr], y, epochs=50, batch_size=16, verbose=0)

    past_target   = train_df['scaled_target'].values[-lookback:].reshape(-1, 1)
    past_exog     = exog_train_df.values[-lookback:]
    past_features = np.hstack([past_target, past_exog])
    X_past_pred   = np.array([past_features])
    X_future_pred = np.array([exog_future_df.values.flatten()])

    pred_scaled = model.predict([X_past_pred, X_future_pred], verbose=0)[0]
    return target_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()

# ── Main Process ───────────────────────────────────────────────────────────────
def process_class(class_name, dept, file_path):
    print(f"\n[{dept.upper()} - CLASS {class_name}] Processing...")
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])

    print("  Calculating SKU proportions...")
    sku_sales = df.groupby(['Store', 'SKU', 'SKU Name', 'Dept', 'Dept Name', 'Category']).agg(
        Sales=('Sales', 'sum'),
        Sales_Qty=('Sales Qty', 'sum')
    ).reset_index()
    total_sales = sku_sales['Sales'].sum()
    total_qty   = sku_sales['Sales_Qty'].sum()
    sku_sales['Proportion_Sales'] = np.where(total_sales > 0, sku_sales['Sales'] / total_sales, 0)
    sku_sales['Proportion_Qty']   = np.where(total_qty   > 0, sku_sales['Sales_Qty'] / total_qty, 0)
    sku_metadata = sku_sales.drop(columns=['Sales', 'Sales_Qty'])

    print("  Aggregating to class level...")
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

    last_date = class_df['Date'].max()
    future_df = create_future_dataframe(last_date, HORIZON)

    forecasts = {}
    for target in ['Sales', 'Sales Qty']:
        target_suffix = 'Sales' if target == 'Sales' else 'Qty'

        print(f"\n  --- SARIMAX ({target}) ---")
        sarimax_pred, sarimax_fitted, sarimax_resid = train_predict_sarimax(
            class_df, future_df, target_col=target
        )
        forecasts[f'Predicted_{target_suffix}_SARIMAX'] = sarimax_pred

        print(f"  --- LSTM ({target}) ---")
        lstm_pred = train_predict_lstm(class_df, future_df, target_col=target)
        forecasts[f'Predicted_{target_suffix}_LSTM'] = lstm_pred

        print(f"  --- Hybrid SARIMAX-LSTM ({target}) ---")
        class_df_hybrid = class_df.copy()
        class_df_hybrid['SARIMAX_Residual'] = np.nan
        class_df_hybrid.loc[len(class_df_hybrid) - len(sarimax_resid):, 'SARIMAX_Residual'] = sarimax_resid
        class_df_hybrid = class_df_hybrid.dropna(subset=['SARIMAX_Residual']).reset_index(drop=True)
        hybrid_lstm_pred = train_predict_lstm(
            class_df_hybrid, future_df, target_col='SARIMAX_Residual'
        )
        forecasts[f'Predicted_{target_suffix}_Hybrid'] = sarimax_pred + hybrid_lstm_pred

    print("\n  Distributing forecasts to SKU level...")
    all_results = []
    for i, row in future_df.iterrows():
        current_date = row['Date']
        for _, sku_row in sku_metadata.iterrows():
            result_row = {
                'Date':      current_date.strftime('%Y-%m-%d'),
                'Store':     sku_row['Store'],
                'SKU':       sku_row['SKU'],
                'SKU Name':  sku_row['SKU Name'],
                'Dept':      sku_row['Dept'],
                'Dept Name': sku_row['Dept Name'],
                'Category':  sku_row['Category'],
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
    print(f"  Saved: {output_path}")


def main():
    classes = ['B', 'C']
    for dept in DEPARTMENTS:
        dept_data_dir = os.path.join(BASE_DATA_DIR, dept)
        for cls in classes:
            file_path = os.path.join(dept_data_dir, f"timeseries_{cls}.csv")
            if os.path.exists(file_path):
                process_class(cls, dept, file_path)
            else:
                print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
