"""

"""

from pathlib import Path
import fitz
import magic
import mimetypes

def detect_mime_type(file_path: str):
    mime, _ = mimetypes.guess_type(mime=True)
    return mime or 'application/octet-stream'

def detect_file_extension(file_path: str):
    return Path(file_path).suffix.lower()

def get_page_count(file_path: str):
    doc = fitz.open(file_path)
    return len(doc)

def is_scanned_pdf(file_path: str):
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text().strip()

        if text:
            return False
    return True

def classify_document(file_path: str):
    mime_type = detect_mime_type(file_path=file_path)
    extension = detect_file_extension(file_path=file_path)

    result = {
        'file_path': file_path,
        'mime_type': mime_type,
        'extension': extension,
        'file_type': None,
        'doc_subtype': None,
        'requires_ocr': False
    }

    if extension == ".pdf":
        result['file_type'] = 'pdf'

        scanned = is_scanned_pdf(file_path=file_path)
        
        if scanned:
            result['doc_subtype'] = 'scanned_pdf'
            result['requires_ocr'] = True
        else:
            result['doc_subtype'] = 'digital_pdf'

    elif extension in ['.jpg', '.jpeg', '.png', '.tiff']:
        result['file_type'] = 'image'
        result['doc_subtype'] = 'image_invoice'
        result['requires_ocr'] = True
    
    else:
        result['file_type'] = 'unknown'

    return result

