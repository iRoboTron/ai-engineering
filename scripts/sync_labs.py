#!/usr/bin/env python3
"""Export named, complete book snippets; --check detects documentation/code drift."""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / "docs/books"
LABS = ROOT / "labs"
MANIFEST = LABS / ".generated-files.json"
FENCE = re.compile(r"^```([\w+-]+)\s*\n(.*?)^```\s*$", re.M | re.S)
MARKER = re.compile(r"^(?:#|--) ~/proj/ai-labs/([^\n]+)\n")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from py_to_ipynb import convert as _py_to_ipynb  # noqa: E402

# Entry-point scripts the reader runs and reads output from, and that no other lab file
# imports (`from <module> import ...`) — safe to ship as a notebook instead of a .py file.
# Files any other script imports (client.py, common.py, embed.py, retrievers.py, tools.py,
# memory_backend.py, agent.py, rag_pipeline.py, eval.py, rag_logic.py, pgstore.py, ...) stay
# .py: a notebook cannot be `import`ed by another script without extra tooling.
NOTEBOOK_ENTRYPOINTS = {
    "day1-llm-basics/01_basics.py",
    "day1-llm-basics/02_structured.py",
    "day1-llm-basics/03_streaming.py",
    "day1-llm-basics/04_cost.py",
    "day1-llm-basics/05_retry.py",
    "day2-rag-eval/index.py",
    "day3-pgvector/load.py",
    "day3-pgvector/eval_pg.py",
    "day4-agent/agent_mcp.py",
    "day5-evals/experiment.py",
    "day5-evals/judge.py",
    "day5-evals/ragas_eval.py",
    "day6-serving-security/vram.py",
    "day6-serving-security/bench_ollama.py",
    "day6-serving-security/ru_provider.py",
    "day6-serving-security/red_team.py",
    "day7-interview/mock.py",
}


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


def _notebook_json(content: str) -> str:
    """.py source (with its leading `# ~/proj/ai-labs/...` marker line stripped) -> nbformat JSON text."""
    body = MARKER.sub("", content, count=1)
    nb = _py_to_ipynb(body)
    return json.dumps(nb, ensure_ascii=False, indent=1) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = collect()
    # Map export name -> (final file content, book source). Entry-point scripts become
    # <name>.ipynb instead of <name>.py; everything else is unchanged.
    outputs: dict[str, tuple[str, str]] = {}
    for name, (content, source) in expected.items():
        if name in NOTEBOOK_ENTRYPOINTS:
            outputs[name[:-len(".py")] + ".ipynb"] = (_notebook_json(content), source)
        else:
            outputs[name] = (content, source)
    missing = NOTEBOOK_ENTRYPOINTS - set(expected)
    if missing:
        raise ValueError(f"NOTEBOOK_ENTRYPOINTS names not found among exported lab files: {sorted(missing)}")
    old = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    problems = []
    for name, (content, source) in outputs.items():
        target = LABS / name
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                problems.append(name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    stale = sorted(set(old) - set(outputs))
    if args.check:
        problems += stale
        if old != {name: source for name, (_, source) in outputs.items()}:
            problems.append(".generated-files.json")
    else:
        for name in stale:
            path = (LABS / name).resolve()
            if not path.is_relative_to(LABS.resolve()):
                raise ValueError("Unsafe stale manifest path")
            path.unlink(missing_ok=True)
        MANIFEST.write_text(json.dumps({n: s for n, (_, s) in outputs.items()}, ensure_ascii=False, indent=2) + "\n")
    if problems:
        print("FAIL: run python3 scripts/sync_labs.py; drift: " + ", ".join(problems))
        return 1
    print(f"PASS: {len(outputs)} executable examples {'in sync' if args.check else 'exported'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
