import pandas as pd
import os

# Cek file-file di sales_clean yang mengandung data September 2025
sales_clean_folder = r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\sales_clean"

print("=== Mencari file yang mengandung data September 2025 ===\n")

files_with_sept_2025 = []

for file in os.listdir(sales_clean_folder):
    if file.endswith('.csv'):
        file_path = os.path.join(sales_clean_folder, file)
        try:
            # Baca hanya baris pertama untuk cek format
            df_sample = pd.read_csv(file_path, nrows=100)
            
            # Cek apakah ada kolom Date
            if 'Date' in df_sample.columns:
                df_sample['Date'] = pd.to_datetime(df_sample['Date'], errors='coerce')
                
                # Cek apakah ada data September 2025
                sept_2025_count = len(df_sample[(df_sample['Date'].dt.year == 2025) & 
                                                 (df_sample['Date'].dt.month == 9)])
                
                if sept_2025_count > 0:
                    # Hitung total baris di file
                    df_full = pd.read_csv(file_path)
                    df_full['Date'] = pd.to_datetime(df_full['Date'], errors='coerce')
                    total_sept = len(df_full[(df_full['Date'].dt.year == 2025) & 
                                              (df_full['Date'].dt.month == 9)])
                    
                    files_with_sept_2025.append({
                        'file': file,
                        'total_rows': len(df_full),
                        'sept_2025_rows': total_sept,
                        'date_range': f"{df_full['Date'].min()} to {df_full['Date'].max()}"
                    })
                    
                    print(f"File: {file}")
                    print(f"  Total rows: {len(df_full):,}")
                    print(f"  Sept 2025 rows: {total_sept:,}")
                    print(f"  Date range: {df_full['Date'].min()} to {df_full['Date'].max()}")
                    print()
        except Exception as e:
            pass

print(f"\n=== Total file dengan data September 2025: {len(files_with_sept_2025)} ===")
print(f"Total baris September 2025 dari semua file: {sum([f['sept_2025_rows'] for f in files_with_sept_2025]):,}")
