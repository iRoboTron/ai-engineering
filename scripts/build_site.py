#!/usr/bin/env python3
"""Build only allowlisted public assets; never publish career, corpora, or local outputs."""
import argparse
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(destination):
    dest = Path(destination).resolve()
    source = ROOT / "docs/books"
    manifest = json.loads((source / "files.json").read_text())["courses"]
    files = [(source / name, Path(name)) for name in ("index.html", "reader.html", "reader-links.js", "files.json")]
    files += [(p, p.relative_to(source)) for p in (source / "vendor").rglob("*") if p.is_file()]
    for book, entries in manifest.items():
        if Path(book).name != book:
            raise ValueError("Invalid book path")
        for item in entries:
            name = item if isinstance(item, str) else item["file"]
            if Path(name).name != name:
                raise ValueError("Invalid chapter path")
            files.append((source / book / name, Path("books") / book / name))
    for path, relative in files:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing/unsafe publication input: {path}")
    if dest.exists() and any(dest.iterdir()):
        raise ValueError("Destination must be empty")
    dest.mkdir(parents=True, exist_ok=True)
    for path, relative in files:
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    labs = ROOT / "labs"
    lab_files = set(json.loads((labs / ".generated-files.json").read_text()))
    lab_files.update(str(p.relative_to(labs)) for p in (labs / "fixtures").rglob("*") if p.is_file())
    lab_files.update({"README.md", ".gitignore", "requirements.txt", "requirements.in", "day7-interview/question-bank.json"})
    with zipfile.ZipFile(dest / "labs.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(lab_files):
            path = labs / name
            if not path.resolve().is_relative_to(labs.resolve()) or path.is_symlink():
                raise ValueError(f"Unsafe laboratory archive input: {name}")
            archive.write(path, "ai-labs/" + name)
    print(f"Built {len(files)} public files and labs.zip in {dest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    build(parser.parse_args().destination)
