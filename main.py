"""
main.py
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff'}

def process_file(file_path: str)->dict:
    from Doc_Class_agent.tools import classify_document
    from PDF_Parser.tools import extract_text_from_pdf
    from Image_Parser.tools import extract_text_from_image
    from Invoice_Extractor.extractor import extract_invoice_data
    from Storage.db import store_invoice

    file_path = str(Path(file_path).resolve())

    logger.info("Processing: %s", file_path)

    classification = classify_document(file_path)
    file_type = classification.get('file_type', 'unknown')
    logger.info(" Type %s / %s", file_type, classification.get('doc_subtype'))

    if file_type == 'pdf':
        result = extract_text_from_pdf(file_path)
    elif file_type == "image":
        result = extract_text_from_image(file_path)
    else:
        logger.warning(" Unsupported file type - skipping.")
        return {'success': False, 'error': 'Unsupported file type', 'file': file_path}
    
    if not result.get('success'):
        logger.error("  Text extraction failed: %s", result.get("error"))
        return {'success': False, 'error': result.get('error'), 'file': file_path}
    
    raw_text = result['text']
    logger.info("   Extracted %d characters.", len(raw_text))

    invoice_data = extract_invoice_data(raw_text)
    if 'error' in invoice_data:
        logger.error("  Invoice parsing failed: %s", invoice_data['error'])
        return {'success': False, 'error': invoice_data['error'], 'file': file_path}
    
    logger.info(
        "   Parsed: vendor=%s  total=%s %s",
        invoice_data.get('vendor_name'),
        invoice_data.get('total'),
        invoice_data.get('currency'),
    )

    invoice_id = store_invoice(file_path, invoice_data, raw_text)
    logger.info("   Saved as invoice id=%d", invoice_id)

    return {'success': True, 'invoice_id': invoice_id, 'file': file_path}

def process_path(path: str)->list:
    p = Path(path)
    if p.is_file():
        return [process_file(str(p))]
    
    if p.is_dir():
        results = []
        for fp in p.glob("*"):
            if fp.suffix.lower() in SUPPORTED_EXTENSIONS:
                results.append(process_file(str(fp)))

        if not results:
            logger.warning("No supported invoice files found in %s", p)

        return results
    
    logger.error("Path not found: %s", path)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        prog='invoice_agent',
        description=(
            "Invoice Agent - process and store invoice documents.\n"
            "To query, run: adk web (then open http://localhost:8000)"
        ),
    )

    sub = parser.add_subparsers(dest='command', required=True)
    proc = sub.add_parser('process', help="Extract and store invoices from files")
    proc.add_argument(
        '--path',
        required=True,
        metavar="PATH",
        help="Path to an invoice file or a directory of invoice files.",
    )

    args = parser.parse_args()

    if args.command == 'process':
        results = process_path(args.path)
        ok = sum(1 for r in results if r.get('success'))
        print(f"\nDone. {ok}/{len(results)} file(s) processed successfully")

if __name__=='__main__':
    main()