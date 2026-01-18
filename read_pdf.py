# read_pdf.py
from pypdf import PdfReader
import tempfile
import os

def extract_text_from_pdf_file(file_storage) -> str:
    temp_path = None
    text = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            file_storage.save(temp_path)

        reader = PdfReader(temp_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return text.strip()
