#!/usr/bin/env python3
"""Converts a plain .py entry-point script into a runnable .ipynb (nbformat v4), stdlib only.

Two modes:

1. Manual (preferred, used by every file that has explanatory markdown): the source contains
   jupytext-style percent markers on their own line —

       # %% [markdown]
       # ## Заголовок
       #
       # Пояснение обычным текстом, без `#` в начале строки не будет — снимается автоматически.
       # %%
       код_ячейки = 1

   Each marker starts a new cell; text between a `# %% [markdown]` marker and the next marker
   is a markdown cell (the leading `# ` on each line is stripped); text after a bare `# %%` is a
   code cell, taken verbatim. Content before the first marker (if any — typically just the
   `# ~/proj/ai-labs/...` marker line sync_labs.py strips before calling convert()) becomes an
   implicit leading code cell. Every code cell is ast.parsed on its own, so a marker placed
   mid-statement fails loudly at export time instead of producing a broken notebook.

2. Automatic (fallback for a file with no percent markers at all): split at top-level
   `def`/`class` boundaries and blank-line gaps between top-level statements. Kept only so an
   unannotated file still converts to something runnable; every NOTEBOOK_ENTRYPOINTS file is
   expected to use the manual mode instead.
"""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

NBFORMAT_MINOR = 5
MARKER_RE = re.compile(r"^# %%(\s*\[markdown\])?[ \t]*$")


def _cell_id(source: str, index: int) -> str:
    """Deterministic 8-char id (nbformat >=4.5 requires one per cell) so re-generation is stable."""
    return hashlib.sha256(f"{index}:{source}".encode("utf-8")).hexdigest()[:8]


def _lines(source: str, start: int, end: int) -> list[str]:
    """1-indexed inclusive line range -> list of raw source lines."""
    return source.splitlines(keepends=True)[start - 1:end]


def _code_cell(text: str, index: int) -> dict:
    text = text.rstrip("\n")
    ast.parse(text)  # a marker placed mid-statement breaks a single cell's syntax; fail at export time
    return {"id": _cell_id(text, index), "cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


def _markdown_cell(text: str, index: int) -> dict:
    text = text.rstrip("\n")
    return {"id": _cell_id(text, index), "cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def _dedent_markdown(text: str) -> str:
    """Strips the leading '# ' (or bare '#') each markdown-cell line carries to stay valid Python."""
    out = []
    for line in text.splitlines():
        if line == "#":
            out.append("")
        elif line.startswith("# "):
            out.append(line[2:])
        elif line.startswith("#"):
            out.append(line[1:])
        else:
            out.append(line)  # tolerate a stray non-comment line rather than mangle it
    return "\n".join(out)


def has_manual_markers(source: str) -> bool:
    return any(MARKER_RE.match(line) for line in source.splitlines())


def split_manual(source: str) -> list[tuple[str, str]]:
    """Splits on `# %%` / `# %% [markdown]` marker lines. Returns [(kind, raw_text), ...]."""
    segments: list[tuple[str, str]] = []
    kind, buf = "code", []
    for line in source.splitlines(keepends=True):
        m = MARKER_RE.match(line.rstrip("\n"))
        if m:
            segments.append((kind, "".join(buf)))
            kind, buf = ("markdown" if m.group(1) else "code"), []
            continue
        buf.append(line)
    segments.append((kind, "".join(buf)))
    return [(k, t) for k, t in segments if t.strip()]


def split_cells_auto(source: str) -> list[str]:
    """Fallback for files with no percent markers: def/class boundaries + blank-line gaps."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    body = tree.body
    if not body:
        return [source]

    def_idx = [i for i, n in enumerate(body) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    cells: list[str] = []

    if def_idx:
        first_def, last_def = def_idx[0], def_idx[-1]
        header_end = body[first_def].lineno - 1
        if body[first_def].decorator_list:
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
            gap = lines[prev_end:node.lineno - 1]
            if gap and all(g.strip() == "" for g in gap):
                cells.append("".join(_lines(source, group_start, prev_end)))
                group_start = node.lineno
            prev_end = node.end_lineno
        cells.append("".join(_lines(source, group_start, prev_end)))
    return [c for c in cells if c.strip()]


def convert(source: str, title: str | None = None) -> dict:
    ast.parse(source)  # fail loudly on syntax errors (markdown-cell '#' lines don't count) before building the notebook
    cells = []
    if title:
        cells.append(_markdown_cell(f"# {title}", 0))
    if has_manual_markers(source):
        for kind, text in split_manual(source):
            if kind == "markdown":
                cells.append(_markdown_cell(_dedent_markdown(text), len(cells)))
            else:
                cells.append(_code_cell(text, len(cells)))
    else:
        cells.extend(_code_cell(c, i) for i, c in enumerate(split_cells_auto(source), start=len(cells)))
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
