import os
import pandas as pd
import numpy as np
from datetime import timedelta
import statsmodels.api as sm
import warnings
import holidays

warnings.filterwarnings('ignore')

# Configuration
CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
BASE_DATA_DIR = os.path.join(CURR_DIR, "dataset", "time-series")
DEPARTMENTS = ["fruit", "vegetable"]
OUTPUT_DIR = os.path.join(CURR_DIR, "forecast_output")
HORIZON = 30
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
    df_future['Operating_Hours'] = df_future['Date'].apply(
        lambda x: 10 if id_holidays.get(x) == 'Hari Raya Idul Fitri'
                 else (16 if (x.month == 12 and x.day == 31) else 14)
    )
    df_future['NYE'] = ((df_future['Date'].dt.month == 12) & (df_future['Date'].dt.day == 31)).astype(int)
    return df_future

def train_predict_sarimax(train_df, future_df, target_col='Sales'):
    endog = train_df[target_col]
    exog_cols = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours', 'NYE']
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
    
    forecast = result.get_forecast(steps=HORIZON, exog=exog_future)
    pred_mean = forecast.predicted_mean
    return pred_mean.values

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
    
    sku_sales['Proportion_Sales'] = np.where(total_sales > 0, sku_sales['Sales'] / total_sales, 0)
    sku_sales['Proportion_Qty'] = np.where(total_qty > 0, sku_sales['Sales_Qty'] / total_qty, 0)
    sku_metadata = sku_sales.drop(columns=['Sales', 'Sales_Qty'])
    
    print("Aggregating data to class level...")
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
    target_cols = ['Sales', 'Sales Qty']
    
    for target in target_cols:
        target_suffix = "Sales" if target == 'Sales' else "Qty"
        
        print(f"\n--- Modeling Class {class_name}: SARIMAX ({target}) ---")
        sarimax_pred = train_predict_sarimax(class_df, future_df, target_col=target)
        forecasts[f'Predicted_{target_suffix}_SARIMAX'] = sarimax_pred
        
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
    classes = ['B', 'C']
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
