import pandas as pd
import os

by_dept_folder = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-dept"
output_folder  = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\new-dataset\split-dataset\by-abc"
os.makedirs(output_folder, exist_ok=True)

def abc_classify(x):
    if x <= 0.8:
        return "A"
    elif x <= 0.95:
        return "B"
    else:
        return "C"

all_abc = []

for dept in ["FRUIT", "VEGETABLE"]:
    input_path = os.path.join(by_dept_folder, f"dataset_{dept}.csv")
    print(f"\n{'='*52}")
    print(f"  ABC Analysis: {dept}")
    print(f"{'='*52}")

    df = pd.read_csv(input_path, dtype={"SKU": str})
    df["SKU"] = df["SKU"].str.zfill(8)
    print(f"  Loaded: {len(df):,} baris")

    # STEP 1 — Agregasi per Store + Category + SKU
    df_group = df.groupby(
        ["Store", "Dept", "Dept Name", "Category", "SKU", "SKU Name"],
        as_index=False
    )[["Sales", "Sales Qty"]].sum()

    # STEP 2 — Sort
    df_group = df_group.sort_values(
        ["Store", "Category", "Sales"],
        ascending=[True, True, False]
    ).reset_index(drop=True)

    # STEP 3 — Contribution per Store + Category
    df_group["Contribution (%)"] = df_group.groupby(
        ["Store", "Category"]
    )["Sales"].transform(lambda x: x / x.sum())

    # STEP 4 — Pareto kumulatif per Store + Category
    df_group["Pareto (%)"] = df_group.groupby(
        ["Store", "Category"]
    )["Contribution (%)"].cumsum()

    # STEP 5 — ABC Classification
    df_group["ABC"] = df_group["Pareto (%)"].apply(abc_classify)

    # Format ke persen string
    df_group["Contribution (%)"] = (df_group["Contribution (%)"] * 100).round(2).astype(str) + "%"
    df_group["Pareto (%)"]       = (df_group["Pareto (%)"] * 100).round(2).astype(str) + "%"

    # Summary
    summary = df_group.groupby("ABC").agg(
        Jumlah_SKU=("SKU", "count"),
        Total_Sales=("Sales", "sum"),
        Total_Qty=("Sales Qty", "sum")
    )
    summary["% SKU"] = (summary["Jumlah_SKU"] / len(df_group) * 100).round(1)
    print(summary.to_string())

    # Simpan gabungan A+B+C per Dept
    fname    = f"dataset_{dept}_ABC.csv"
    out_path = os.path.join(output_folder, fname)
    df_group.to_csv(out_path, index=False)
    print(f"  ✅ Saved: {fname} ({len(df_group):,} baris)")

    all_abc.append(df_group)

# Simpan combined ABC (referensi untuk time series)
df_all = pd.concat(all_abc, ignore_index=True)
df_all.to_csv(os.path.join(output_folder, "final_dataset_abc.csv"), index=False)
print(f"\n✅ Combined saved: final_dataset_abc.csv")
print(f"\n🎉 Selesai! Tersimpan di:\n   {output_folder}")
