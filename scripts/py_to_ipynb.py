#!/usr/bin/env python3
"""Converts a plain .py entry-point script into a runnable .ipynb (nbformat v4), stdlib only.

Splitting rule, chosen to match how these scripts are already written (docstring/imports/
"# --- НАСТРОЙКИ ---" block, then function/class defs, then the executable body):
  1. Everything up to the first top-level `def`/`class` is one cell (imports + settings).
     If there is no def/class in the file, this rule does not apply and step 3 covers everything.
  2. Each top-level `def`/`class` is its own cell.
  3. Everything after the last top-level `def`/`class` (the executable body, including any
     `if __name__ == "__main__":` guard — `__name__` is `"__main__"` in a notebook kernel too,
     so the guard still runs) is split into cells at blank-line boundaries between top-level
     statements: a statement preceded by a blank line starts a new cell.
No cell is ever split inside a def/class body — only at top-level statement boundaries.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

NBFORMAT_MINOR = 5


def _cell_id(source: str, index: int) -> str:
    """Deterministic 8-char id (nbformat >=4.5 requires one per cell) so re-generation is stable."""
    return hashlib.sha256(f"{index}:{source}".encode("utf-8")).hexdigest()[:8]


def _lines(source: str, start: int, end: int) -> list[str]:
    """1-indexed inclusive line range -> list of raw source lines."""
    return source.splitlines(keepends=True)[start - 1:end]


def _code_cell(text: str, index: int) -> dict:
    text = text.rstrip("\n")
    return {"id": _cell_id(text, index), "cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


def _markdown_cell(text: str, index: int) -> dict:
    text = text.rstrip("\n")
    return {"id": _cell_id(text, index), "cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def split_cells(source: str) -> list[str]:
    """Returns a list of code-cell source strings (each may span multiple top-level statements)."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    body = tree.body
    if not body:
        return [source]

    def_idx = [i for i, n in enumerate(body) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    cells: list[str] = []

    if def_idx:
        first_def, last_def = def_idx[0], def_idx[-1]
        header_end = body[first_def].lineno - 1  # last line before the first def, allowing for decorators
        if def_idx and isinstance(body[first_def], (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and body[first_def].decorator_list:
            header_end = body[first_def].decorator_list[0].lineno - 1
        if header_end > 0:
            cells.append("".join(_lines(source, 1, header_end)))
        for i in def_idx:
            node = body[i]
            start = node.decorator_list[0].lineno if node.decorator_list else node.lineno
            cells.append("".join(_lines(source, start, node.end_lineno)))
        tail_start_idx = last_def + 1
    else:
        tail_start_idx = 0

    tail_nodes = body[tail_start_idx:]
    if tail_nodes:
        group_start = tail_nodes[0].lineno
        prev_end = tail_nodes[0].end_lineno
        for node in tail_nodes[1:]:
            gap = lines[prev_end:node.lineno - 1]  # lines strictly between prev node and this one
            if any(gap_line.strip() == "" for gap_line in gap) and len(gap) >= 1 and all(g.strip() == "" for g in gap):
                cells.append("".join(_lines(source, group_start, prev_end)))
                group_start = node.lineno
            prev_end = node.end_lineno
        cells.append("".join(_lines(source, group_start, prev_end)))
    return [c for c in cells if c.strip()]


def convert(source: str, title: str | None = None) -> dict:
    ast.parse(source)  # fail loudly on syntax errors before building the notebook
    cells = []
    if title:
        cells.append(_markdown_cell(f"# {title}", 0))
    cells.extend(_code_cell(c, i) for i, c in enumerate(split_cells(source), start=len(cells)))
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3 (ai-labs)", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": NBFORMAT_MINOR,
    }


def convert_file(path: Path, title: str | None = None) -> str:
    nb = convert(path.read_text(encoding="utf-8"), title=title)
    return json.dumps(nb, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".ipynb")
    out.write_text(convert_file(src), encoding="utf-8")
    print(f"{src} -> {out}")
