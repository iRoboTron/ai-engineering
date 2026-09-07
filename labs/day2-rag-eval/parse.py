# ~/proj/ai-labs/day2-rag-eval/parse.py
"""Один файл → один текст. Каждый формат разбирается своей библиотекой, все они уже в requirements.txt."""
from pathlib import Path

def parse(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".md", ".txt"}:                              # уже текст, просто читаем
        return path.read_text(encoding="utf-8")
    if ext == ".pdf":
        from pypdf import PdfReader                          # достаёт текстовый слой PDF
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if ext == ".docx":
        from docx import Document                            # python-docx: абзацы Word-документа
        return "\n\n".join(p.text for p in Document(str(path)).paragraphs if p.text.strip())
    if ext in {".html", ".htm"}:
        from bs4 import BeautifulSoup                         # разбирает HTML в дерево тегов
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for node in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            node.decompose()                                  # убираем не-контент перед извлечением текста
        return soup.get_text(separator="\n\n", strip=True)
    raise ValueError(f"неподдерживаемый формат: {ext}")
