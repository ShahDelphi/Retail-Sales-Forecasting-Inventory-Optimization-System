import os
import re
from PyPDF2 import PdfReader, PdfWriter

# Base directory
BASE_DIR = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\promotion discount"
INPUT_FOLDER = os.path.join(BASE_DIR, "output")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "combined")

def extract_effective_date(pdf_path):
    """Extract the effective date from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                match = re.search(r"EFFECTIVE DATE\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"  [ERROR] Gagal membaca {os.path.basename(pdf_path)}: {e}")
    return None

def combine_and_sort_pdfs(input_folder, output_folder):
    """Combine and sort PDFs by effective date, save to output_folder."""

    # Create output folder if not exists
    os.makedirs(output_folder, exist_ok=True)

    pdf_files = sorted([
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.lower().endswith('.pdf')
    ])

    print(f"\nDitemukan {len(pdf_files)} file PDF di folder: {input_folder}")
    print("-" * 60)

    # Extract effective dates and associate them with file paths
    pdf_with_dates = []
    no_date_files = []

    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        effective_date = extract_effective_date(pdf_file)
        if effective_date:
            pdf_with_dates.append((pdf_file, effective_date))
            print(f"  [OK] {filename}  ->  Effective Date: {effective_date}")
        else:
            no_date_files.append(pdf_file)
            print(f"  [SKIP] {filename}  ->  Effective Date tidak ditemukan")

    print("-" * 60)
    print(f"\nTotal berhasil dibaca: {len(pdf_with_dates)} file")
    print(f"Total dilewati (tidak ada tanggal): {len(no_date_files)} file")

    if not pdf_with_dates:
        print("\n[GAGAL] Tidak ada PDF yang memiliki effective date. Proses dibatalkan.")
        return

    # Sort PDFs by effective date (ascending)
    pdf_with_dates.sort(key=lambda x: x[1])

    print("\nUrutan PDF setelah diurutkan berdasarkan Effective Date:")
    for i, (pdf_file, date) in enumerate(pdf_with_dates, 1):
        print(f"  {i:3}. [{date}] {os.path.basename(pdf_file)}")

    # Combine sorted PDFs
    writer = PdfWriter()
    total_pages = 0
    for pdf_file, date in pdf_with_dates:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            writer.add_page(page)
        total_pages += len(reader.pages)

    # Save combined PDF
    output_filename = "combined_sorted.pdf"
    output_path = os.path.join(output_folder, output_filename)

    with open(output_path, 'wb') as output_pdf:
        writer.write(output_pdf)

    print(f"\n{'='*60}")
    print(f"[SELESAI] Combined PDF berhasil disimpan!")
    print(f"  Path    : {output_path}")
    print(f"  Total   : {len(pdf_with_dates)} PDF digabungkan, {total_pages} halaman")
    print(f"{'='*60}")

if __name__ == "__main__":
    combine_and_sort_pdfs(INPUT_FOLDER, OUTPUT_FOLDER)