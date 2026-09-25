"""
extractor.py
------------
Turns an uploaded file (PDF, DOCX, TXT, PNG/JPG) into plain text.

Strategy for PDFs (the tricky case):
  1. Try native text extraction with PyMuPDF (fast, exact).
  2. If the extracted text is suspiciously short (a strong signal the PDF
     is actually a scanned image with no text layer), fall back to
     rendering each page as an image and running Tesseract OCR on it.

This dual-path approach is the difference between "works on clean text
templates" and "works on real-world scanned forms/certificates too".
"""
import io
import os
from dataclasses import dataclass

import pymupdf as fitz  # PyMuPDF (new import name; 'fitz' alias kept for readability below)
import docx  # python-docx
import pytesseract
from PIL import Image

# Below this many characters per page, we assume the PDF has no usable
# text layer and treat it as a scanned document.
MIN_CHARS_PER_PAGE_THRESHOLD = 20


@dataclass
class ExtractionResult:
    text: str
    method: str  # "native_text" | "ocr" | "docx" | "txt" | "image_ocr"


def _extract_pdf(file_bytes: bytes) -> ExtractionResult:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    native_text_parts = []
    for page in doc:
        native_text_parts.append(page.get_text())
    native_text = "\n".join(native_text_parts).strip()

    avg_chars_per_page = len(native_text) / max(len(doc), 1)

    if avg_chars_per_page >= MIN_CHARS_PER_PAGE_THRESHOLD:
        return ExtractionResult(text=native_text, method="native_text")

    # Fallback: scanned PDF -> render pages to images -> OCR
    ocr_parts = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        ocr_parts.append(pytesseract.image_to_string(img))
    return ExtractionResult(text="\n".join(ocr_parts).strip(), method="ocr")


def _extract_docx(file_bytes: bytes) -> ExtractionResult:
    document = docx.Document(io.BytesIO(file_bytes))
    parts = [p.text for p in document.paragraphs]
    # Also pull text out of tables (common in form-like templates)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return ExtractionResult(text="\n".join(parts).strip(), method="docx")


def _extract_txt(file_bytes: bytes) -> ExtractionResult:
    text = file_bytes.decode("utf-8", errors="ignore")
    return ExtractionResult(text=text.strip(), method="txt")


def _extract_image(file_bytes: bytes) -> ExtractionResult:
    img = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(img)
    return ExtractionResult(text=text.strip(), method="image_ocr")


def extract_text(filename: str, file_bytes: bytes) -> ExtractionResult:
    """
    Dispatch to the right extractor based on file extension.
    Raises ValueError for unsupported types.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_bytes)
    elif ext == ".docx":
        return _extract_docx(file_bytes)
    elif ext == ".txt":
        return _extract_txt(file_bytes)
<<<<<<< HEAD
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
        return _extract_image(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: .pdf, .docx, .txt, .png, .jpg, .jpeg, .webp"
=======
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return _extract_image(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: .pdf, .docx, .txt, .png, .jpg, .jpeg"
>>>>>>> ba5f726fc4c60de617d94b6f15883cd8ae6b35d2
        )
