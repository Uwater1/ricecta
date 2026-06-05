import pypdf

def parse_pdf(pdf_path, txt_path):
    reader = pypdf.PdfReader(pdf_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for idx, page in enumerate(reader.pages):
            f.write(f"--- PAGE {idx+1} ---\n")
            text = page.extract_text()
            f.write(text)
            f.write("\n\n")
    print(f"Successfully parsed {pdf_path} into {txt_path}")

if __name__ == '__main__':
    parse_pdf('P116_Evaluating_trading_strategies.pdf', 'parsed_pdf.txt')
