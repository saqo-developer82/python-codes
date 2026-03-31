from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import Callable

import fitz
import pytesseract
from docx import Document
from PIL import Image, ImageOps
from pytesseract import TesseractNotFoundError


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
PDF_SUFFIXES = {".pdf"}
DOCX_SUFFIXES = {".docx"}


@dataclass
class ExtractionResult:
    file_path: str
    file_type: str
    text: str
    word_count: int
    used_ocr: bool

    def to_dict(self) -> dict[str, str | int | bool]:
        return asdict(self)


def normalize_text(text: str) -> str:
    stripped_lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in stripped_lines if line]
    normalized = "\n".join(non_empty_lines)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def preprocess_image(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    return grayscale.point(lambda value: 255 if value > 180 else 0)


def extract_image_text(image_path: Path, psm: int = 6) -> str:
    try:
        with Image.open(image_path) as image:
            processed = preprocess_image(image)
            return pytesseract.image_to_string(processed, config=f"--psm {psm}")
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available on PATH."
        ) from exc


def extract_docx_text(docx_path: Path) -> str:
    document = Document(docx_path)
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(parts)


def _ocr_pdf_page(page: fitz.Page, psm: int) -> str:
    try:
        pixmap = page.get_pixmap(dpi=300)
        image = Image.open(BytesIO(pixmap.tobytes("png")))
        processed = preprocess_image(image)
        return pytesseract.image_to_string(processed, config=f"--psm {psm}")
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available on PATH."
        ) from exc


def extract_pdf_text(pdf_path: Path, force_ocr: bool = False, psm: int = 6) -> tuple[str, bool]:
    page_text: list[str] = []
    used_ocr = False

    with fitz.open(pdf_path) as document:
        for page in document:
            text = "" if force_ocr else page.get_text("text")
            if text.strip():
                page_text.append(text)
                continue

            used_ocr = True
            page_text.append(_ocr_pdf_page(page, psm))

    return "\n".join(page_text), used_ocr


def detect_file_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in PDF_SUFFIXES:
        return "pdf"
    if suffix in DOCX_SUFFIXES:
        return "docx"
    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def extract_text_from_file(file_path: Path, force_pdf_ocr: bool = False, psm: int = 6) -> ExtractionResult:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_type = detect_file_type(file_path)
    extractor: Callable[[], tuple[str, bool]]

    if file_type == "image":
        extractor = lambda: (extract_image_text(file_path, psm=psm), True)
    elif file_type == "pdf":
        extractor = lambda: extract_pdf_text(file_path, force_ocr=force_pdf_ocr, psm=psm)
    else:
        extractor = lambda: (extract_docx_text(file_path), False)

    text, used_ocr = extractor()
    normalized_text = normalize_text(text)

    return ExtractionResult(
        file_path=str(file_path),
        file_type=file_type,
        text=normalized_text,
        word_count=count_words(normalized_text),
        used_ocr=used_ocr,
    )
