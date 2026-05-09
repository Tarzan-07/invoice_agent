"""

"""

import cv2
import pytesseract as pts
from pytesseract import Output
from pathlib import Path

def validate_image(file_path: str)-> bool:
    """Checks whether a file can be loaded as an image."""
    img = cv2.imread(file_path)
    return img is not None

def preprocess_image(file_path: str):
    """Load and preprocess image to improve OCR accuracy."""
    img = cv2.imread(file_path)
    state = validate_image(file_path)
    if not state:
        raise ValueError(f"Cannot read image at {file_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return thresh

def extract_data_from_image(processed):
    data = pts.image_to_data(processed, output_type=Output.dict)
    return data

def extract_text_from_image(file_path):
    """
    Extract text from image file. 
    """
    if not validate_image(file_path):
        return {
            'success': False,
            'error': f'Cannot read image at {file_path}',
            'text': "",
        }
    processed = preprocess_image(file_path)
    text = pts.image_to_string(processed)
    return {
        'success': True,
        'text': text.strip(),
        'file_path': file_path
    }

