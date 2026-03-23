import pdfplumber
import docx
import os


def extract_text_from_pdf(path: str) -> str:
    """Estrae testo da PDF."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(path: str) -> str:
    """Estrae testo da DOCX."""
    doc = docx.Document(path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def extract_text(path: str) -> str:
    """Estrae testo da PDF o DOCX in base all'estensione."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    else:
        raise ValueError(f"Formato non supportato: {ext} — usa PDF o DOCX")


def split_into_clauses(text: str) -> dict:
    """
    Divide il testo in sezioni basandosi su pattern comuni
    di numerazione clausole (1., 2., 1.1, Article 1, ecc.)
    """
    import re
    clauses = {}
    current_title = "preamble"
    current_text = []

    lines = text.split("\n")
    clause_pattern = re.compile(
        r"^(\d+\.[\d\.]*\s+\w|Article\s+\d+|Section\s+\d+|ARTICLE\s+\d+|SECTION\s+\d+)",
        re.IGNORECASE
    )

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if clause_pattern.match(line):
            if current_text:
                clauses[current_title] = " ".join(current_text)
            current_title = line[:80]
            current_text = [line]
        else:
            current_text.append(line)

    if current_text:
        clauses[current_title] = " ".join(current_text)

    return clauses