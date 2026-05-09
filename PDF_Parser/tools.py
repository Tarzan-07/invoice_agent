"""
Tools for extracting text from PDF invoice documents.
Handles both digital (text-layer) PDFs and scanned (image-only) PDFs
"""

import fitz
import cv2
import numpy as np
import pytesseract as pts

def _is_scanned(file_path: str)->bool:
    """
    Return True if the PDF contains no extractable text (i.e, it is scanned).
    """
    doc = fitz.open(file_path)
    for page in doc:
        if page.get_text().strip():
            doc.close()
            return False
    doc.close()
    return True

def _extract_digital_pdf_text(file_path: str)->str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text.strip()

def _extract_scanned_pdf_text(file_path):
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes('png')

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

        page_text = pts.image_to_string(thresh)
        text += page_text + "\n"
    doc.close()
    return text.strip()

def extract_text_from_pdf(file_path: str):
    try:
        scanned = _is_scanned(file_path=file_path)
        if scanned:
            text = _extract_scanned_pdf_text(file_path=file_path)
        else:
            text = _extract_digital_pdf_text(file_path=file_path)

        return {
            'success': True,
            'text': text,
            'is_scanned': scanned,
            'file_path': file_path
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'text': "",
            'file_path': file_path
        }