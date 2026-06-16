import pandas as pd
import os

input_path    = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\final_dataset_clean.csv"
output_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-dept"
os.makedirs(output_folder, exist_ok=True)

# Load data
df = pd.read_csv(input_path, dtype={"SKU": str})
df["SKU"] = df["SKU"].str.zfill(8)
print(f"Total data : {len(df):,} baris")
print(f"Dept unik  : {df['Dept Name'].unique().tolist()}")

# Split & simpan per Dept
for dept in df["Dept Name"].unique():
    df_dept = df[df["Dept Name"] == dept].reset_index(drop=True)
    out_path = os.path.join(output_folder, f"dataset_{dept}.csv")
    df_dept.to_csv(out_path, index=False)
    print(f"\n✅ {dept}: {len(df_dept):,} baris → {out_path}")

print(f"\n🎉 Selesai! Tersimpan di:\n   {output_folder}")
