# GET THE PDF FROM GOVERNMENT WEBSITE ON TENANCY ACT AND READ THE TEXT FROM IT AND SAVE THE EXTRACTED DATA ON DATABASE TO USE IT LATER

from pypdf import PdfReader

def get_pdf_text(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file and returns it as a single string.
    """
    try:
        reader = PdfReader("notice.pdf")
        full_text = []

        # Loop through pages and extract text
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)

        # Join all pages with a newline
        print("\n".join(full_text).strip())
    
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


get_pdf_text("notice.pdf")