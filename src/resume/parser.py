from pathlib import Path
from typing import Union

def parse_resume(file_path: Union[str, Path]) -> str:
    """
    Extract text from PDF or TXT resume.

    Args:
        file_path: Path to PDF or TXT file

    Returns:
        Extracted text

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path)
    elif suffix == ".txt":
        return _parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use PDF or TXT.")

def _parse_pdf(file_path: Path) -> str:
    """Extract text from PDF"""
    import pdfplumber

    text = []
    with pdfplumber.open(str(file_path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

    return "\n".join(text)

def _parse_txt(file_path: Path) -> str:
    """Extract text from TXT"""
    return file_path.read_text(encoding="utf-8")

def normalize_text(text: str) -> str:
    """
    Normalize resume text: remove extra whitespace, etc.
    """
    # Replace multiple spaces/newlines with single space
    text = " ".join(text.split())
    return text
