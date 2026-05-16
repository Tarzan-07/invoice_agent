"""
PDF_Parser/tools.py

Extracts text from PDF invoices.
- Digital PDFs: uses PyMuPDF text extraction directly.
- Scanned PDFs: renders pages as images and sends to a vision LLM.
"""

import base64
import os
import logging

import fitz
import litellm

logger = logging.getLogger(__name__)

def _is_scanned(file_path: str) -> bool:
    """Return True if the PDF contains no extractable text."""
    doc = fitz.open(file_path)
    for page in doc:
        if page.get_text().strip():
            doc.close()
            return False
    doc.close()
    return True

def _extract_digital_pdf_text(file_path: str) -> str:
    """Extract text from a digital (text-layer) PDF."""
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text.strip()

def _extract_scanned_pdf_text(file_path: str) -> str:
    """Render each page as an image and extract text via a vision LLM."""
    doc = fitz.open(file_path)

    all_text = []

    for page in doc:
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes(img_bytes).decode('utf-8')
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        model = os.getenv('VIS_MODEL')
        response = litellm.completion(
            model = f'openrouter/{model}',
            messages = [{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': (
                            'Extract ALL text from this scanned invoice page exactly as it appears. '
                            'Preserve the layout, line items, amounts, dates, addresses, ' 
                            'and any other text, Return only the extracted text, no commentary.'
                        ),
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/png;base64, {b64}'
                        },
                    },
                ],
            }],
            api_key=os.getenv('OPENROUTER_API_KEY'),
            api_base='https://openrouter.ai/api/v1',
            temperature=0,
            max_tokens=2000
        )

        content = response.choices[0].message.content or ""
        all_text.append(content.strip())

    doc.close()
    return "\n\n".join(all_text)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF invoice (digital or scanned).

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        dict with 'success', 'text', 'is_scanned', 'file_path', and optionally 'error'.
    """

    try:
        scanned = _is_scanned()
        if scanned:
            text = _extract_scanned_pdf_text(file_path)
        else:
            text = _extract_digital_pdf_text(file_path)
        return {
            'success': True,
            'text': text,
            'is_scanned': scanned,
            'file_path': file_path
        }
    except Exception as e:
        logger.error('PDF extractikkon failed for %s: %s', file_path. e)
        return {
            'success': False,
            'error': str(e),
            'text': "",
            'file_path': file_path
        }