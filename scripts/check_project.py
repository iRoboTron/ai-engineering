#!/usr/bin/env python3
"""Network-free release gate. Does NOT claim paid/provider end-to-end coverage."""
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / "docs/books"


def run(args, cwd=ROOT):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)


def main():
    for folder in sorted(BOOKS.glob("[0-9][0-9]-*")):
        run([sys.executable, "validate-book.py", folder.name], cwd=BOOKS)
    run([sys.executable, "scripts/sync_labs.py", "--check"])
    if (ROOT / "scripts/build_question_bank.py").exists():
        run([sys.executable, "scripts/build_question_bank.py", "--check"])
    for folder in (ROOT / "scripts", ROOT / "labs", ROOT / "tests"):
        for path in folder.rglob("*.py"):
            if any(part in {".venv", ".local"} for part in path.parts):
                continue
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    manifest = json.loads((BOOKS / "vendor/manifest.json").read_text())
    for name, meta in manifest.items():
        if hashlib.sha256((BOOKS / "vendor" / name).read_bytes()).hexdigest() != meta["sha256"]:
            raise ValueError(f"Vendor checksum mismatch: {name}")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"])
    versions = {
        "index.html": re.search(r"const ASSET_VERSION = '([^']+)'", (BOOKS / "index.html").read_text(encoding="utf-8")).group(1),
        "reader.html": re.search(r"const ASSET_VERSION = '([^']+)'", (BOOKS / "reader.html").read_text(encoding="utf-8")).group(1),
        "reader.html script tag": re.search(r'reader-links\.js\?v=([^"]+)"', (BOOKS / "reader.html").read_text(encoding="utf-8")).group(1),
    }
    if len(set(versions.values())) != 1:
        # A stale reader version keeps serving cached .md files after a content deploy.
        raise ValueError(f"ASSET_VERSION differs between files: {versions}")
    run(["node", "tests/reader-links.test.cjs"])
    run(["bash", "-n", "deploy-pxhome.sh"])
    print("PASS: offline gate (not a provider/GPU/production certification)")


if __name__ == "__main__":
    main()
