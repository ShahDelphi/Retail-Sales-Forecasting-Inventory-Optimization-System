import os
import pandas as pd
from datetime import timedelta
import statsmodels.api as sm
import warnings

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
    """Create a dataframe of future dates with weekend feature."""
    future_dates = [last_date + timedelta(days=x) for x in range(1, horizon + 1)]
    df_future = pd.DataFrame({'Date': future_dates})
    df_future['Weekend'] = df_future['Date'].dt.dayofweek.apply(lambda x: 1 if x >= 5 else 0)
    return df_future

def train_predict_sarimax(train_df, future_df):
    """Train and predict using SARIMAX."""
    endog = train_df['Sales']
    exog_cols = ['Weekend']
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
    
    # Predict future
    forecast = result.get_forecast(steps=HORIZON, exog=exog_future)
    pred_mean = forecast.predicted_mean
    return pred_mean.values

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
        Weekend=('Weekend', 'max')
    ).reset_index()
    
    class_df = class_df.sort_values('Date').reset_index(drop=True)
    
    last_date = class_df['Date'].max()
    future_df = create_future_dataframe(last_date, HORIZON)
    
    forecasts = {}
    
    # Class B & C: SARIMAX only (no promo)
    print(f"\n--- Modeling Class {class_name}: SARIMAX ---")
    sarimax_pred = train_predict_sarimax(class_df, future_df)
    forecasts['Predicted_Sales_SARIMAX'] = sarimax_pred
        
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
            # Distribute forecast proportionally
            predicted_total = sarimax_pred[i]
            # Avoid negative forecasts
            predicted_total = max(0, predicted_total)
            result_row['Predicted_Sales_SARIMAX'] = predicted_total * sku_row['Proportion']
            
            all_results.append(result_row)
            
    final_df = pd.DataFrame(all_results)
    
    # Save output
    output_path = os.path.join(OUTPUT_DIR, f"forecast_{dept}_class_{class_name}.csv")
    final_df.to_csv(output_path, index=False)
    print(f"Saved forecasts for Dept {dept}, Class {class_name} to {output_path}")


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
