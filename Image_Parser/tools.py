"""
Image_parser/tools.py

Extracts text from image-based invoices using a vision LLM.
"""

import base64
import os
import logging
from pathlib import Path
import litellm

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.webp'}


def _encode_image_base64(file_path: str) -> str:
    """Read an image file and retures it's base64-encoded string."""


    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def _mime_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    return {
        '.jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.tiff': 'image/tiff',
        '.webp': 'image/webp'
    }.get(ext, 'image/png')

def extract_text_from_image(file_path: str) -> dict:
    """
    Extract all text from an invoice image using a vision LLM.

    Args: 
        file_path: Absolute path to the image file.

    Returns:
        dict with 'success' (bool), 'text' (str), and optionally 'error' (str)
    """

    path = Path(file_path)
    if not path.exists():
        return {'success': False, 'error': f'File not found: {file_path}', 'text': ''}
    
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return {'success': False, 'error': f'Unsupported image type: {path.suffix}', 'text': ''}
    
    try:
        b64 = _encode_image_base64(file_path=file_path)
        mime = _mime_type(file_path=file_path)
        model = os.getenv('VIS_MODEL')
        response = litellm.completion(
            model=f'openrouter/{model}',
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': (
                            'Extract ALL text from the invoice image exactly as it appears. '
                            'Preserve the layout, line items, amounts, dates, addresses, '
                            'and any other text. Return only the extracted text, no commentary.'
                        ),
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:{mime};base64,{b64}',
                        },
                    },
                ],
            }],
            api_key=os.getenv('OPENROUTER_API_KEY'),
            api_base='https://openrouter.ai/api/v1',
            temperature=0,
            max_tokens=4000
        )

        content = response.choices[0].message.content or ""
        return {'success': True, 'text': content.strip(), 'file_path': file_path}
    
    except Exception as e:
        logger.error("Vision extraction failed for %s: %s", file_path, e)
        return {'success': False, 'error': str(e), 'text': ""}