# ~/proj/ai-labs/day2-rag-eval/parse.py
from pathlib import Path

def parse(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if ext == ".docx":
        from docx import Document
        return "\n\n".join(p.text for p in Document(str(path)).paragraphs if p.text.strip())
    if ext in {".html", ".htm"}:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for node in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            node.decompose()
        return soup.get_text(separator="\n\n", strip=True)
    raise ValueError(f"неподдерживаемый формат: {ext}")
