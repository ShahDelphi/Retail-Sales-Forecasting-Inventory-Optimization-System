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
    exog_cols = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours', 'NYE']
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

    # 31 Desember ditetapkan sebagai hari promo (peak season Tahun Baru)
    mask_dec31 = (class_df['Date'].dt.month == 12) & (class_df['Date'].dt.day == 31)
    class_df.loc[mask_dec31, 'Promo'] = 1
    
    if len(class_df) <= HORIZON * 2:
        print(f"Skipping {dept} Class {class_name}: Not enough data for validation.")
        return []
        
    train_df = class_df.iloc[:-HORIZON].reset_index(drop=True)
    test_df = class_df.iloc[-HORIZON:].reset_index(drop=True)
    
    print(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")
    metrics_summary = []
    
    for target in ['Sales', 'Sales Qty']:
        y_actual = test_df[target].values
        
        print(f"\n--- Training SARIMAX {SARIMAX_ORDER} x {SARIMAX_SEASONAL} ({target}) ---")
        sarimax_pred = train_predict_sarimax(train_df, test_df, target_col=target)
        predictions_dict = {'SARIMAX': sarimax_pred}
        
        print(f"\n[ Range Check: {target} ]")
        print_range_check(f"Actual {target}", y_actual)
        for model_name, preds in predictions_dict.items():
            print_range_check(f"Pred {model_name}", preds)
            
        print(f"\n[ Error Metrics: {target} ]")
        for model_name, preds in predictions_dict.items():
            mape_val = compute_mape(y_actual, preds)
            mae_val = compute_mae(y_actual, preds)
            rmse_val = compute_rmse(y_actual, preds)
            
            print(f"  {model_name:10} -> MAPE: {mape_val:6.2f}%, MAE: {mae_val:9.2f}, RMSE: {rmse_val:9.2f}")
            metrics_summary.append({
                'Dept': dept,
                'Class': class_name,
                'Target': target,
                'Model': model_name,
                'MAPE': mape_val,
                'MAE': mae_val,
                'RMSE': rmse_val
            })
        
        test_dates = test_df['Date']
        plt.figure(figsize=(12, 6))
        plt.plot(test_dates, y_actual, label=f'Actual {target}', marker='o', color='black', linewidth=2)
        plt.plot(test_dates, sarimax_pred, label='SARIMAX', linestyle='--', color='blue', linewidth=2)
        
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
                    
    if all_metrics:
        df_metrics = pd.DataFrame(all_metrics)
        for cls in classes:
            cls_metrics = df_metrics[df_metrics['Class'] == cls]
            if not cls_metrics.empty:
                class_output_dir = os.path.join(OUTPUT_DIR, f"class_{cls}")
                if not os.path.exists(class_output_dir):
                    os.makedirs(class_output_dir)
                metrics_csv_path = os.path.join(class_output_dir, f"validation_metrics_summary_class_{cls}.csv")
                cls_metrics.to_csv(metrics_csv_path, index=False)

if __name__ == "__main__":
    main()
