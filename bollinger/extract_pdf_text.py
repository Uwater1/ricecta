import pypdf
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

reader = pypdf.PdfReader(os.path.join(_SCRIPT_DIR, 'bollinger.pdf'))
print(f"Total pages: {len(reader.pages)}")

with open(os.path.join(_SCRIPT_DIR, 'pdf_text.txt'), 'w', encoding='utf-8') as f:
    for i, page in enumerate(reader.pages):
        f.write(f"--- PAGE {i+1} ---\n")
        f.write(page.extract_text() or "")
        f.write("\n\n")

print("Done. Text saved to bollinger/pdf_text.txt")
