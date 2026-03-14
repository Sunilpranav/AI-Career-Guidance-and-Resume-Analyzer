import pypdf
from docx import Document

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return ""

def parse_resume(file_path, extension):
    if extension.lower() == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension.lower() == ".docx":
        return extract_text_from_docx(file_path)
    return ""
