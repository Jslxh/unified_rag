from pathlib import Path
from pypdf import PdfReader

def load_pdf_file(file_path: str) -> list:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    reader = PdfReader(path)
    docs = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            docs.append({
                "content": text,
                "metadata": {
                    "source": path.name,
                    "page": i + 1,
                    "type": "pdf"
                }
            })

    return docs
