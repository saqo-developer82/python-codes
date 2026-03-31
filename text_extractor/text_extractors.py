from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import Any, Callable

try:
    import fitz
except ImportError:
    fitz = None

try:
    import pytesseract
    from pytesseract import TesseractNotFoundError
except ImportError:
    pytesseract = None

    class TesseractNotFoundError(RuntimeError):
        pass

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    Image = None
    ImageFilter = None
    ImageOps = None


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
    processed_file_path: str | None = None

    def to_dict(self) -> dict[str, str | int | bool]:
        return asdict(self)


def normalize_text(text: str) -> str:
    stripped_lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in stripped_lines if line]
    normalized = "\n".join(non_empty_lines)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def cleanup_ocr_text(text: str) -> str:
    cleaned_lines: list[str] = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue

        alpha_numeric_count = len(re.findall(r"[A-Za-z0-9]", line))
        if alpha_numeric_count == 0:
            continue

        symbol_count = len(re.findall(r"[^A-Za-z0-9\s]", line))
        if alpha_numeric_count < 2 and symbol_count > alpha_numeric_count:
            continue

        cleaned_lines.append(line)

    return normalize_text("\n".join(cleaned_lines))


def extract_confident_ocr_text(image: Image.Image, psm: int) -> tuple[str, float]:
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed, so OCR cannot be performed.")

    data = pytesseract.image_to_data(
        image,
        config=f"--oem 3 --psm {psm} preserve_interword_spaces=1",
        output_type=pytesseract.Output.DICT,
    )

    grouped_words: dict[tuple[int, int, int], list[str]] = {}
    confidences: list[float] = []

    for index in range(len(data["text"])):
        word = data["text"][index].strip()
        confidence_text = str(data["conf"][index]).strip()
        try:
            confidence = float(confidence_text)
        except ValueError:
            confidence = -1.0

        if not word or confidence < 45:
            continue

        cleaned_word = re.sub(r"[^A-Za-z0-9.,:;!?()'\"/&\-]+", "", word)
        if not cleaned_word:
            continue

        confidences.append(confidence)
        key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
        grouped_words.setdefault(key, []).append(cleaned_word)

    lines = [" ".join(words) for _, words in sorted(grouped_words.items()) if words]
    result = cleanup_ocr_text("\n".join(lines))
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    word_count = len(re.findall(r"[A-Za-z]{2,}", result))
    score = avg_conf * (1.0 + word_count / 10.0)
    return result, score


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def preprocess_image(image: Image.Image, binarize: bool = True) -> Image.Image:
    if ImageOps is None:
        raise RuntimeError("Pillow is not installed, so image files cannot be read.")
    if ImageFilter is None:
        raise RuntimeError("Pillow image filters are not available.")

    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode not in ("L", "RGB"):
        image = image.convert("RGB")

    grayscale = ImageOps.grayscale(image)
    enlarged = grayscale.resize(
        (grayscale.width * 2, grayscale.height * 2),
        Image.Resampling.LANCZOS,
    )
    enhanced = ImageOps.autocontrast(enlarged)
    if not binarize:
        return enhanced
    denoised = enhanced.filter(ImageFilter.MedianFilter(size=3))
    return denoised.point(lambda value: 255 if value > 165 else 0)


def ensure_temp_dir(file_path: Path) -> Path:
    temp_dir = file_path.resolve().parent.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def save_processed_image(source_path: Path, processed: Image.Image) -> Path:
    temp_dir = ensure_temp_dir(source_path)
    processed_path = temp_dir / f"{source_path.stem}_processed.png"
    processed.save(processed_path)
    return processed_path


def extract_image_text(image_path: Path, psm: int = 6) -> tuple[str, Path]:
    if Image is None:
        raise RuntimeError("Pillow is not installed, so image files cannot be read.")
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed, so OCR cannot be performed.")

    try:
        with Image.open(image_path) as image:
            best_text = ""
            best_score = -1
            best_processed = None

            strategies = [
                (preprocess_image(image, binarize=True), psm),
                (preprocess_image(image, binarize=False), 3),
                (preprocess_image(image, binarize=False), 4),
            ]

            for processed, strategy_psm in strategies:
                text, score = extract_confident_ocr_text(processed, psm=strategy_psm)
                if score > best_score:
                    best_score = score
                    best_text = text
                    best_processed = processed

            processed_path = save_processed_image(image_path, best_processed)
            return best_text, processed_path
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available on PATH."
        ) from exc


def extract_docx_text(docx_path: Path) -> str:
    if Document is None:
        raise RuntimeError("python-docx is not installed, so DOCX files cannot be read.")

    document = Document(docx_path)
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(parts)


def _ocr_pdf_page(page: Any, psm: int) -> str:
    if Image is None:
        raise RuntimeError("Pillow is not installed, so PDF OCR cannot be performed.")
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed, so PDF OCR cannot be performed.")

    try:
        pixmap = page.get_pixmap(dpi=300)
        image = Image.open(BytesIO(pixmap.tobytes("png")))
        processed = preprocess_image(image, binarize=True)
        text, _ = extract_confident_ocr_text(processed, psm=psm)
        return text
    except TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed or not available on PATH."
        ) from exc


def extract_pdf_text(pdf_path: Path, force_ocr: bool = False, psm: int = 6) -> tuple[str, bool]:
    if fitz is None:
        raise RuntimeError("PyMuPDF is not installed, so PDF files cannot be read.")

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
    processed_file_path: str | None = None

    if file_type == "image":
        image_text, processed_path = extract_image_text(file_path, psm=psm)
        text = image_text
        used_ocr = True
        processed_file_path = str(processed_path)
    elif file_type == "pdf":
        extractor = lambda: extract_pdf_text(file_path, force_ocr=force_pdf_ocr, psm=psm)
        text, used_ocr = extractor()
    else:
        extractor = lambda: (extract_docx_text(file_path), False)
        text, used_ocr = extractor()

    normalized_text = text if file_type == "image" else normalize_text(text)

    return ExtractionResult(
        file_path=str(file_path),
        file_type=file_type,
        text=normalized_text,
        word_count=count_words(normalized_text),
        used_ocr=used_ocr,
        processed_file_path=processed_file_path,
    )
