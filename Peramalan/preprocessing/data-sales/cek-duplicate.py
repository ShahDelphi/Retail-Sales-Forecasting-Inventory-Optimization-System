import os
from collections import defaultdict

# Folder yang akan dicek
folder_path = r"D:\program\tesis\Data-Tesis\Data-Tesis\Sales"


def main():
    # Cek duplikat berdasarkan nama file (case-insensitive, termasuk yang ada (1), (2), dst)
    print("Cek duplikat berdasarkan nama file:")
    from collections import Counter
    all_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            all_files.append(file.lower())
    name_counts = Counter(all_files)
    dupe_names = [name for name, count in name_counts.items() if count > 1]
    if not dupe_names:
        print("Tidak ada nama file yang duplikat.")
    else:
        print("Nama file yang duplikat:")
        for name in dupe_names:
            print(f"{name} (jumlah: {name_counts[name]})")

if __name__ == "__main__":
    main()
