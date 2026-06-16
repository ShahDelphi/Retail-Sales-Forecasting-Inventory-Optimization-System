import os
import re
import csv
import pdfplumber

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_DIR    = r"D:\program\tesis\Data-Tesis\Data-Tesis\Peramalan\preprocessing\promotion discount"
INPUT_PDF   = os.path.join(BASE_DIR, "combined", "promotion_discount.pdf")
OUTPUT_DIR  = os.path.join(BASE_DIR, "combined")
OUTPUT_CSV  = os.path.join(OUTPUT_DIR, "promotion_discount.csv")

# ─── COLUMN MAPPING ───────────────────────────────────────────────────────────
# Table rows have 14 columns (including None filler cols). 
# Meaningful indices:
#   0  = SHORT_SKU
#   1  = DESCRIPTION
#   3  = BARCODE
#   5  = STORE
#   7  = ORIGINAL_PRICE
#   8  = NEW_PRICE
#   10 = CHANGE_VALUE
#   11 = CLOSING_STOCK_QTY
#   13 = UOM

DATA_INDICES = {
    "SHORT_SKU"          : 0,
    "DESCRIPTION"        : 1,
    "BARCODE"            : 3,
    "STORE"              : 5,
    "ORIGINAL_PRICE"     : 7,
    "NEW_PRICE"          : 8,
    "CHANGE_VALUE"       : 10,
    "CLOSING_STOCK_QTY"  : 11,
    "UOM"                : 13,
}

CSV_COLUMNS = [
    "PAGE_NUM",
    "PRICE_CHANGE_NUMBER",
    "DEPARTMENT_CODE",
    "DEPARTMENT_NAME",
    "STATUS",
    "PRICE_CHANGE_TYPE",
    "EFFECTIVE_DATE",
    "ENDING_DATE",
    "SHORT_SKU",
    "DESCRIPTION",
    "BARCODE",
    "STORE",
    "ORIGINAL_PRICE",
    "NEW_PRICE",
    "CHANGE_VALUE",
    "CLOSING_STOCK_QTY",
    "UOM",
]


def parse_header_row(row):
    """
    Parse a header row from the table.
    Row structure example:
      ['DEPARTMENT CODE :', None, '2038', None, 'FRUIT', None,
       'PRICE CHANGE NUMBER :', None, None, '505943', None, None, None, None]
    Returns dict with parsed values or empty dict if not a header row.
    """
    if not row or len(row) < 10:
        return {}

    label = str(row[0]).strip() if row[0] else ""

    # Check DEPARTMENT CODE row
    if "DEPARTMENT CODE" in label:
        return {
            "DEPARTMENT_CODE" : str(row[2]).strip() if row[2] else "",
            "DEPARTMENT_NAME" : str(row[4]).strip() if row[4] else "",
            "PRICE_CHANGE_NUMBER": str(row[9]).strip() if len(row) > 9 and row[9] else "",
        }

    # Check STATUS row
    if "STATUS" in label:
        return {
            "STATUS"           : str(row[2]).strip() if row[2] else "",
            "PRICE_CHANGE_TYPE": str(row[12]).strip() if len(row) > 12 and row[12] else "",
        }

    # Check EFFECTIVE DATE row
    if "EFFECTIVE DATE" in label:
        return {
            "EFFECTIVE_DATE": str(row[2]).strip() if row[2] else "",
            "ENDING_DATE"   : str(row[9]).strip() if len(row) > 9 and row[9] else "",
        }

    return {}


def is_header_row(row):
    """Check if this row is a column-header row (SHORT SKU, DESCRIPTION, etc.)"""
    if not row or len(row) == 0:
        return False
    first = str(row[0]).strip() if row[0] else ""
    return first in ("SHORT SKU", "SHORT_SKU")


def is_data_row(row):
    """Check if this row contains actual item data (starts with SHORT SKU number)."""
    if not row or len(row) < 14:
        return False
    first = str(row[0]).strip() if row[0] else ""
    # SKU is typically numeric 8 digits
    return bool(re.match(r"^\d{6,12}$", first))


def safe_get(row, idx):
    """Safely get value from row by index."""
    if idx < len(row) and row[idx] is not None:
        return str(row[idx]).strip()
    return ""


def extract_page(page, page_num):
    """Extract all data rows from a single PDF page. Returns list of dicts."""
    tables = page.extract_tables()
    rows_out = []

    for table in tables:
        header_info = {}

        for row in table:
            if not row:
                continue

            # Try parsing header metadata rows
            parsed = parse_header_row(row)
            if parsed:
                header_info.update(parsed)
                continue

            # Skip the column-label row
            if is_header_row(row):
                continue

            # Extract actual data rows
            if is_data_row(row):
                record = {
                    "PAGE_NUM"            : page_num,
                    "PRICE_CHANGE_NUMBER" : header_info.get("PRICE_CHANGE_NUMBER", ""),
                    "DEPARTMENT_CODE"     : header_info.get("DEPARTMENT_CODE", ""),
                    "DEPARTMENT_NAME"     : header_info.get("DEPARTMENT_NAME", ""),
                    "STATUS"              : header_info.get("STATUS", ""),
                    "PRICE_CHANGE_TYPE"   : header_info.get("PRICE_CHANGE_TYPE", ""),
                    "EFFECTIVE_DATE"      : header_info.get("EFFECTIVE_DATE", ""),
                    "ENDING_DATE"         : header_info.get("ENDING_DATE", ""),
                    "SHORT_SKU"           : safe_get(row, DATA_INDICES["SHORT_SKU"]),
                    "DESCRIPTION"         : safe_get(row, DATA_INDICES["DESCRIPTION"]),
                    "BARCODE"             : safe_get(row, DATA_INDICES["BARCODE"]),
                    "STORE"               : safe_get(row, DATA_INDICES["STORE"]),
                    "ORIGINAL_PRICE"      : safe_get(row, DATA_INDICES["ORIGINAL_PRICE"]),
                    "NEW_PRICE"           : safe_get(row, DATA_INDICES["NEW_PRICE"]),
                    "CHANGE_VALUE"        : safe_get(row, DATA_INDICES["CHANGE_VALUE"]),
                    "CLOSING_STOCK_QTY"   : safe_get(row, DATA_INDICES["CLOSING_STOCK_QTY"]),
                    "UOM"                 : safe_get(row, DATA_INDICES["UOM"]),
                }
                rows_out.append(record)

    return rows_out


def convert_pdf_to_csv(input_pdf, output_csv):
    """Main function: read PDF page by page, extract data, write to CSV."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    print(f"\n{'='*65}")
    print(f" PDF → CSV CONVERTER")
    print(f"{'='*65}")
    print(f" Input  : {input_pdf}")
    print(f" Output : {output_csv}")
    print(f"{'='*65}\n")

    all_records = []
    error_pages = []

    with pdfplumber.open(input_pdf) as pdf:
        total_pages = len(pdf.pages)
        print(f" Total halaman: {total_pages:,}")
        print(f" Memproses...\n")

        for i, page in enumerate(pdf.pages):
            page_num = i + 1

            # Progress report every 100 pages
            if page_num % 100 == 0 or page_num == 1:
                pct = page_num / total_pages * 100
                print(f"  [{pct:5.1f}%] Halaman {page_num:,} / {total_pages:,} "
                      f"| Records: {len(all_records):,}")

            try:
                records = extract_page(page, page_num)
                all_records.extend(records)
            except Exception as e:
                error_pages.append((page_num, str(e)))

    # Write to CSV
    print(f"\n Menulis {len(all_records):,} records ke CSV...")
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"\n{'='*65}")
    print(f" [SELESAI]")
    print(f"  Total records : {len(all_records):,}")
    print(f"  Error pages   : {len(error_pages)}")
    if error_pages:
        for pg, err in error_pages[:10]:
            print(f"    - Page {pg}: {err}")
    print(f"  Output file   : {output_csv}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    convert_pdf_to_csv(INPUT_PDF, OUTPUT_CSV)
