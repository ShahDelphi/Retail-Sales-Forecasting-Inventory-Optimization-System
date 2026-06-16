import pandas as pd

# Load dataset
df = pd.read_csv(r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_clean.csv")

# Filter data September 2025
df['Date'] = pd.to_datetime(df['Date'])
df_sept_2025 = df[(df['Date'].dt.year == 2025) & (df['Date'].dt.month == 9)]

# Ambil contoh SKU yang duplikat
print("=== Contoh Duplikasi SKU 805414 pada 2025-09-06 ===")
sample = df_sept_2025[(df_sept_2025['SKU'] == 805414) & (df_sept_2025['Date'] == '2025-09-06')]
print(f"Jumlah baris: {len(sample)}")
print(sample)

print("\n=== Contoh Duplikasi SKU 800112 pada 2025-09-24 ===")
sample2 = df_sept_2025[(df_sept_2025['SKU'] == 800112) & (df_sept_2025['Date'] == '2025-09-24')]
print(f"Jumlah baris: {len(sample2)}")
print(sample2)

# Cek apakah ada perbedaan di kolom lain
print("\n=== Analisis Perbedaan ===")
if len(sample) > 1:
    print("Apakah semua kolom sama?")
    for col in sample.columns:
        unique_vals = sample[col].nunique()
        print(f"{col}: {unique_vals} unique values")
        if unique_vals > 1:
            print(f"  Values: {sample[col].unique()}")
