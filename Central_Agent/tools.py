"""
Central_Agent/tools.py

Lightweight tools for the Central Agent - storage after sub-agents have 
already classified and extracted text from the invoice document.
"""

from pathlib import Path

SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff'}

def store_parsed_invoice(file_path: str, raw_text: str) -> dict:
    """
    Take raw extracted text from an invoice, parse it into structured fields using an LLM,
    and store it in the database. 

    Args: 
        file_path: Absolute path to the original invoice file.
        raw_text: The full text content extracted from the invoice.

    Returns:
        A dict with success status, invoice metadata, or an error message.
    """

    from Invoice_Extractor.extractor import extract_invoice_data
    from Storage.db import store_invoice
    from Doc_Class_agent.tools import classify_document
    from PDF_Parser.tools import extract_text_from_pdf
    from Image_Parser.tools import extract_text_from_image
    from Invoice_Extractor.extractor import extract_invoice_data
    from Storage.db import store_invoice

    file_path = str(Path(file_path).resolve())

    invoice_data = extract_invoice_data(raw_text)
    if 'error' in invoice_data:
        return {'success': False, 'error': invoice_data['error'], 'file': file_path}
    
    invoice_id = store_invoice(file_path, invoice_data, raw_text)

    return {
        'success': True,
        'invoice_id': invoice_id,
        'vendor_name': invoice_data.get('vendor_name'),
        'invoice_number': invoice_data.get('invoice_number'),
        'invoice_date': invoice_data.get('invoice_date'),
        'total': invoice_data.get('total'),
        'currency': invoice_data.get('currency'),
        'file': file_path,
    }