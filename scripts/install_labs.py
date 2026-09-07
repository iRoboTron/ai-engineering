#!/usr/bin/env python3
"""Copy course labs without overwriting existing work. Never invokes APIs or Docker."""
import argparse
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "labs"
EXCLUDE = {"__pycache__", ".venv", ".local", ".env", ".generated-files.json"}


def install(source, dest):
    source, dest = Path(source).resolve(), Path(dest).expanduser().resolve()
    if dest == source or dest.is_relative_to(source):
        raise ValueError("Destination must be outside the source labs directory")
    files = [p for p in sorted(source.rglob("*"))
             if p.is_file() and not any(part in EXCLUDE for part in p.relative_to(source).parts)]
    conflicts, pending = [], []
    for path in files:
        if path.is_symlink():
            raise ValueError(f"Source symlink is not allowed: {path}")
        target = dest / path.relative_to(source)
        if not target.resolve().is_relative_to(dest) or any(p.is_symlink() for p in [target, *target.parents] if p != dest.parent):
            raise ValueError(f"Destination symlink is not allowed: {target}")
        if target.exists():
            if not target.is_file() or path.read_bytes() != target.read_bytes():
                conflicts.append(target)
        else:
            pending.append((path, target))
    if conflicts:
        raise ValueError("Existing files differ; nothing copied. Choose a fresh --dest or merge manually:\n" + "\n".join(map(str, conflicts)))
    for path, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return len(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=Path.home() / "proj/ai-labs")
    args = parser.parse_args()
    try:
        count = install(SOURCE, args.dest)
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    print(f"Copied {count} files to {args.dest.expanduser()}; identical files unchanged.")
    print("No dependencies installed; no API requests made. See README.md in the destination.")


if __name__ == "__main__":
    main()
