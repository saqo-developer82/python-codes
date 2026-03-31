from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from .text_extractors import ExtractionResult, extract_text_from_file
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from text_extractor.text_extractors import ExtractionResult, extract_text_from_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract text and word count from PDF, image, or DOCX files."
    )
    parser.add_argument("file", type=Path, help="Path to the input file")
    parser.add_argument(
        "--ocr-pdf",
        action="store_true",
        help="Force OCR for all PDF pages instead of using embedded text first.",
    )
    parser.add_argument(
        "--psm",
        type=int,
        default=6,
        help="Tesseract page segmentation mode to use for OCR (default: 6).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path for the extracted text.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON instead of plain text.",
    )
    return parser


def render_plain_text(result: ExtractionResult) -> str:
    text = result.text if result.text else "[No text extracted]"
    return "\n".join(
        [
            f"File: {result.file_path}",
            f"Type: {result.file_type}",
            f"Word count: {result.word_count}",
            f"Used OCR: {'yes' if result.used_ocr else 'no'}",
            "",
            "Extracted text:",
            text,
        ]
    )


def write_output(output_path: Path, text: str) -> None:
    output_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = extract_text_from_file(
            args.file,
            force_pdf_ocr=args.ocr_pdf,
            psm=args.psm,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")

    if args.output:
        write_output(args.output, result.text)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=True))
    else:
        print(render_plain_text(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())
