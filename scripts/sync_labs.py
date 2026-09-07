#!/usr/bin/env python3
"""Export named, complete book snippets; --check detects documentation/code drift."""
import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / "docs/books"
LABS = ROOT / "labs"
MANIFEST = LABS / ".generated-files.json"
FENCE = re.compile(r"^```([\w+-]+)\s*\n(.*?)^```\s*$", re.M | re.S)
MARKER = re.compile(r"^(?:#|--) ~/proj/ai-labs/([^\n]+)\n")


def collect(books=BOOKS):
    result = {}
    for source in sorted(books.glob("[0-9][0-9]-*/*.md")):
        text = source.read_text(encoding="utf-8")
        for match in FENCE.finditer(text):
            language, body = match.group(1, 2)
            marker = MARKER.match(body)
            preceding = re.search(r"<!-- lab: ([^>]+) -->\s*$", text[:match.start()])
            if not marker and not preceding:
                continue
            name = (marker or preceding).group(1).strip()
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or not re.fullmatch(r"[\w./-]+", name):
                raise ValueError(f"Unsafe lab path: {name}")
            if language not in {"python", "bash", "sql", "yaml", "json", "text", "toml"}:
                raise ValueError(f"Unsupported executable language: {language} ({source})")
            if language == "python":
                tree = ast.parse(body, filename=name)
                if any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                       and n.value.value is Ellipsis for n in ast.walk(tree)):
                    raise ValueError(f"Incomplete executable example: {name}")
            if language == "json":
                try:
                    json.loads(body)          # a normal pretty-printed JSON document (e.g. settings.json)
                except json.JSONDecodeError:
                    for line in body.splitlines():   # fall back to JSON Lines (e.g. attacks.jsonl)
                        if line.strip():
                            json.loads(line)
            if name in result:
                raise ValueError(f"Duplicate lab file: {name}")
            result[name] = (body.rstrip() + "\n", str(source.relative_to(ROOT)))
    if not result:
        raise ValueError("No named executable snippets found")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = collect()
    old = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    problems = []
    for name, (content, source) in expected.items():
        target = LABS / name
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                problems.append(name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    stale = sorted(set(old) - set(expected))
    if args.check:
        problems += stale
        if old != {name: source for name, (_, source) in expected.items()}:
            problems.append(".generated-files.json")
    else:
        for name in stale:
            path = (LABS / name).resolve()
            if not path.is_relative_to(LABS.resolve()):
                raise ValueError("Unsafe stale manifest path")
            path.unlink(missing_ok=True)
        MANIFEST.write_text(json.dumps({n: s for n, (_, s) in expected.items()}, ensure_ascii=False, indent=2) + "\n")
    if problems:
        print("FAIL: run python3 scripts/sync_labs.py; drift: " + ", ".join(problems))
        return 1
    print(f"PASS: {len(expected)} executable examples {'in sync' if args.check else 'exported'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
