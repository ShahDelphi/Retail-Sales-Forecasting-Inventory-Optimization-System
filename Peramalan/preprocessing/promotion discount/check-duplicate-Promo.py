import os
import hashlib

# Folder path to check for duplicate PDFs
folder_path = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\Promo"

def file_hash(filepath, block_size=65536):
    """Generate MD5 hash for a file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()

def find_duplicate_pdfs(folder):
    hashes = {}
    duplicates = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                path = os.path.join(root, file)
                h = file_hash(path)
                if h in hashes:
                    duplicates.append((path, hashes[h]))
                else:
                    hashes[h] = path
    return duplicates

def main():
    duplicates = find_duplicate_pdfs(folder_path)
    if duplicates:
        print("Duplicate PDF files found:")
        for dup, orig in duplicates:
            print(f"Duplicate: {dup}\nOriginal: {orig}\n")
    else:
        print("No duplicate PDF files found.")

if __name__ == "__main__":
    main()
