import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
import warnings
import tensorflow as tf
from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate # type: ignore
from tensorflow.keras.models import Model # type: ignore
import holidays

warnings.filterwarnings('ignore')

CURR_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\modelling"
file_path = os.path.join(CURR_DIR, "dataset", "time-series", "vegetable", "timeseries_A.csv")

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

# 31 Desember ditetapkan sebagai hari promo
mask_dec31 = (class_df['Date'].dt.month == 12) & (class_df['Date'].dt.day == 31)
class_df.loc[mask_dec31, 'Promo'] = 1

# Tambahkan Operating_Hours
def get_operating_hours(date):
    if date.month == 12 and date.day == 31:
        return 16
    elif date.month == 12 and date.day == 25:
        return 10
    else:
        return 14

class_df['Operating_Hours'] = class_df['Date'].apply(get_operating_hours)

target = 'Sales Qty'
year, month = 2025, 12

mask_test = (class_df['Date'].dt.year == year) & (class_df['Date'].dt.month == month)
test_df  = class_df[mask_test].reset_index(drop=True)
train_df = class_df[class_df['Date'] < test_df['Date'].min()].reset_index(drop=True)

# ----------------- MODEL TANPA OPERATING HOURS -----------------
print("=== TANPA OPERATING HOURS ===")
exog_cols_old = ['Weekend', 'Holiday', 'Promo']
# SARIMAX
model_s_old = sm.tsa.statespace.SARIMAX(
    train_df[target],
    exog=train_df[exog_cols_old],
    order=(1, 1, 1),
    seasonal_order=(1, 1, 1, 7),
    enforce_stationarity=False,
    enforce_invertibility=False
)
res_s_old = model_s_old.fit(disp=False)
fc_s_old = res_s_old.get_forecast(steps=len(test_df), exog=test_df[exog_cols_old]).predicted_mean.values

print("SARIMAX Dec 31 prediction:", fc_s_old[-1])
print("Actual Dec 31 sales:", test_df[target].values[-1])


# ----------------- MODEL DENGAN OPERATING HOURS -----------------
print("\n=== DENGAN OPERATING HOURS ===")
exog_cols_new = ['Weekend', 'Holiday', 'Promo', 'Operating_Hours']
# SARIMAX
model_s_new = sm.tsa.statespace.SARIMAX(
    train_df[target],
    exog=train_df[exog_cols_new],
    order=(1, 1, 1),
    seasonal_order=(1, 1, 1, 7),
    enforce_stationarity=False,
    enforce_invertibility=False
)
res_s_new = model_s_new.fit(disp=False)
fc_s_new = res_s_new.get_forecast(steps=len(test_df), exog=test_df[exog_cols_new]).predicted_mean.values

print("SARIMAX Dec 31 prediction:", fc_s_new[-1])
print("Actual Dec 31 sales:", test_df[target].values[-1])
