from pathlib import Path
import sys

import pytesseract
from PIL import Image, ImageOps


def extract_text(image_path: Path) -> str:
    img = Image.open(image_path)
    width, height = img.size

    # The sample image has the text in the lower white banner.
    text_panel = img.crop((0, int(height * 0.48), width, height))
    gray = ImageOps.grayscale(text_panel)
    bw = gray.point(lambda x: 255 if x > 180 else 0)

    return pytesseract.image_to_string(bw, config="--psm 6")


image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/color-text.jpg")
ocr_result = extract_text(image_path)

print(ocr_result)