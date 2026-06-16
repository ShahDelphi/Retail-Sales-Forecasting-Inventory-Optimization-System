import pandas as pd

path = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\data-sales\fix_data-sales\final_dataset.csv"
df = pd.read_csv(path)

print("=" * 50)
print("SHAPE:", df.shape)
print("=" * 50)

print("\n📋 DATA TYPES:")
print(df.dtypes)

print("\n📊 INFO LENGKAP:")
df.info()

print("\n🔍 SAMPLE DATA (5 baris pertama):")
print(df.head(5).to_string(index=False))

print("\n❓ MISSING VALUES:")
missing = df.isna().sum()
pct = (missing / len(df) * 100).round(2)
summary = pd.DataFrame({"Missing": missing, "Persen (%)": pct})
print(summary[summary["Missing"] > 0] if missing.any() else "✅ Tidak ada missing value")

print("\n📈 STATISTIK NUMERIK:")
print(df.describe())

print("\n🗓️ RANGE DATE:")
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
print(f"  Dari : {df['Date'].min()}")
print(f"  Sampai: {df['Date'].max()}")

print("\n🏪 STORE UNIK:", sorted(df["Store"].unique().tolist()))
print("📦 JUMLAH SKU UNIK:", df["SKU"].nunique())
print("🏷️ DEPT UNIK:", df["Dept"].unique().tolist())
print("🏷️ DEPT NAME UNIK:", df["Dept Name"].unique().tolist())
