import os
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

INPUT_FOLDER = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\Promo"
OUTPUT_FOLDER = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\promotion discount\output"
KEYWORD = "Promotion Discount"

# pastikan folder output ada
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for filename in os.listdir(INPUT_FOLDER):
    if filename.endswith(".pdf"):
        input_path = os.path.join(INPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"filtered_{filename}")

        reader = PdfReader(input_path)
        writer = PdfWriter()

        print(f"Memproses: {filename}")

        with pdfplumber.open(input_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                
                if text and KEYWORD.lower() in text.lower():
                    writer.add_page(reader.pages[i])

        # hanya simpan kalau ada halaman yang cocok
        if len(writer.pages) > 0:
            with open(output_path, "wb") as f:
                writer.write(f)
            print(f"✔ Disimpan: {output_path}")
        else:
            print(f"✘ Tidak ada keyword di: {filename}")

print("\nSelesai semua!")