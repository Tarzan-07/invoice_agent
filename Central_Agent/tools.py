"""
Central_Agent/tools.py
"""

from pathlib import Path

SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff'}

def ingest_invoice(file_path: str):
    from Doc_Class_agent.tools import classify_document
    from PDF_Parser.tools import extract_text_from_pdf
    from Image_Parser.tools import extract_text_from_image
    from Invoice_Extractor.extractor import extract_invoice_data
    from Storage.db import store_invoice

    file_path = str(Path(file_path).resolve())

    classification = classify_document(file_path)
    file_type = classification.get('file_type', 'unknown')

    if file_type not in ('pdf', 'image'):
        return {
            'success': False,
            'error': f"Unsupported file type '{classification.get('extension', 'unknown')}'."
                    f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            'file': file_path,
        }
    
    if file_type == "pdf":
        result = extract_text_from_pdf(file_path)
    else:
        result = extract_text_from_image(file_path)
    
    if not result.get('success'):
        return {'success': False, 'error': result.get('error'), 'file': file_path}
    
    raw_text = result['text']

    invoice_data = extract_invoice_data(raw_text)
    if 'error' in invoice_data:
        return {'success': False, 'error': invoice_data['error'], 'file': file_path}
    
    invoice_id = store_invoice(file_path, invoice_data, raw_text)

    return {
        'success': True,
        'invoice_id': invoice_data.get('vendor_name'),
        'invoice_number': invoice_data.get('invoice_number'),
        'invoice_date': invoice_data.get('invoice_date'),
        'total': invoice_data.get('total'),
        'currency': invoice_data.get('currency'),
        'file': file_path,
    }