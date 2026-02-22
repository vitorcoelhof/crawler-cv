import pytest
from pathlib import Path
from src.resume.parser import parse_resume

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal PDF with text"""
    try:
        import pdfplumber
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_file = tmp_path / "sample.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=letter)
        c.drawString(100, 750, "Python Developer")
        c.drawString(100, 730, "5 years experience")
        c.save()
        return pdf_file
    except ImportError:
        pytest.skip("reportlab not installed")

@pytest.fixture
def sample_txt(tmp_path):
    """Create a sample TXT resume"""
    txt_file = tmp_path / "resume.txt"
    txt_file.write_text(
        "John Doe\n"
        "Senior Backend Engineer\n"
        "8 years experience\n"
        "Skills: Python, Django, AWS, PostgreSQL\n"
    )
    return txt_file

def test_parse_txt_resume(sample_txt):
    text = parse_resume(str(sample_txt))
    assert "John Doe" in text
    assert "Senior Backend Engineer" in text

def test_parse_pdf_resume(sample_pdf):
    text = parse_resume(str(sample_pdf))
    assert "Python Developer" in text

def test_parse_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        parse_resume("/nonexistent/file.pdf")

def test_parse_unsupported_format(tmp_path):
    unsupported = tmp_path / "file.doc"
    unsupported.write_text("test")
    with pytest.raises(ValueError, match="Unsupported file format"):
        parse_resume(str(unsupported))
