from __future__ import annotations

import argparse
import sys
from pathlib import Path

from text_extractor.text_extractors import ExtractionResult, extract_text_from_file


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract text and word count from a file stored in the data directory."
    )
    parser.add_argument(
        "filename",
        help="Name of the file inside the data directory, for example: index.jpg",
    )
    parser.add_argument(
        "--ocr-pdf",
        action="store_true",
        help="Force OCR for PDF files instead of using embedded text first.",
    )
    parser.add_argument(
        "--psm",
        type=int,
        default=6,
        help="Tesseract page segmentation mode to use for OCR (default: 6).",
    )
    return parser


def render_result(result: ExtractionResult) -> str:
    extracted_text = result.text if result.text else "[No text extracted]"
    lines = [
        f"File: {Path(result.file_path).name}",
        f"Location: {result.file_path}",
        f"Type: {result.file_type}",
        f"Word count: {result.word_count}",
        f"Used OCR: {'yes' if result.used_ocr else 'no'}",
    ]
    if result.processed_file_path:
        lines.append(f"Processed image: {result.processed_file_path}")

    lines.extend(
        [
            "",
            "Extracted text:",
            extracted_text,
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    file_path = DATA_DIR / args.filename
    if not file_path.exists():
        parser.exit(
            status=1,
            message=f"Error: File '{args.filename}' was not found in {DATA_DIR}\n",
        )

    try:
        result = extract_text_from_file(
            file_path,
            force_pdf_ocr=args.ocr_pdf,
            psm=args.psm,
        )
    except (RuntimeError, ValueError) as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")

    print(render_result(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
