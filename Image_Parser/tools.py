"""

"""

import cv2
import pytesseract as pts
from pytesseract import Output

def validate_image(file_path: str):
    return

def preprocess_image():
    return

def _extract_data_from_image(processed):
    data = pts.image_to_data(processed, output_type=Output.dict)
    return data

def extract_text_from_image(processed):
    text = pts.image_to_string(processed)
    return text

