import os
import fitz  # PyMuPDF

pdf_files = ["customservis.pdf", "siparisservis.pdf", "urunservis.pdf"]
for pdf_file in pdf_files:
    txt_file = pdf_file.replace(".pdf", ".txt")
    print(f"Reading {pdf_file}...")
    doc = fitz.open(pdf_file)
    with open(txt_file, "w", encoding="utf-8") as f:
        for page in doc:
            f.write(page.get_text())
    doc.close()
    print(f"Saved to {txt_file}")
