import os
import pandas as pd

# Define remapping dictionary
store_map = {
    1001: 'T-01', 1002: 'T-02', 1003: 'T-03', 1004: 'T-04', 1005: 'T-05',
    1006: 'T-06', 1007: 'T-07', 1008: 'T-08', 1009: 'T-09', 1010: 'T-10',
    '1001': 'T-01', '1002': 'T-02', '1003': 'T-03', '1004': 'T-04', '1005': 'T-05',
    '1006': 'T-06', '1007': 'T-07', '1008': 'T-08', '1009': 'T-09', '1010': 'T-10',
    '1001.0': 'T-01', '1002.0': 'T-02', '1003.0': 'T-03', '1004.0': 'T-04', '1005.0': 'T-05',
    '1006.0': 'T-06', '1007.0': 'T-07', '1008.0': 'T-08', '1009.0': 'T-09', '1010.0': 'T-10'
}

exclude_stores = {1011, 1012, 1013, '1011', '1012', '1013', '1011.0', '1012.0', '1013.0'}

files_to_convert = [
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Pemesanan\dataset\final_dataset_clean.csv",
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_clean.csv",
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\promo\promotion_discount_clean.csv",
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-abc\dataset_FRUIT_ABC.csv",
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-abc\dataset_VEGETABLE_ABC.csv",
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-abc\final_dataset_abc.csv",
    r"d:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_abc.csv"
]

def convert_file(path):
    if not os.path.exists(path):
        print(f"[WARN] File not found (skipped): {path}")
        return
        
    print(f"\nProcessing: {path}")
    # Load csv
    df = pd.read_csv(path)
    print(f"  Original shape: {df.shape}")
    
    # Store column check
    if 'Store' not in df.columns:
        print("  [WARN] 'Store' column not found in this file!")
        return
        
    # Check current store unique values
    print("  Original stores:", df['Store'].dropna().unique())
    
    # Filter out 1011, 1012, 1013
    df = df[~df['Store'].isin(exclude_stores)]
    
    # Remap 1001-1010 to T-01-T-10 (idempotent mapping)
    df['Store'] = df['Store'].map(store_map).fillna(df['Store'])
    
    # Verify mapping
    mapped_stores = df['Store'].dropna().unique()
    print("  Mapped stores:", mapped_stores)
    print(f"  Shape after mapping: {df.shape}")
    
    # Save back
    df.to_csv(path, index=False)
    print("  Successfully saved.")

if __name__ == "__main__":
    print("[INFO] Starting Store Remapping Pipeline...")
    for file_path in files_to_convert:
        convert_file(file_path)
    print("\n[INFO] Store Remapping Pipeline Finished Successfully!")
