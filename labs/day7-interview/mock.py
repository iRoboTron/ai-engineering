# ~/proj/ai-labs/day7-interview/mock.py
import random
import re
import sys
from pathlib import Path

BANK = Path.home() / "Documents/lessons/ai-engineering/docs/books/07-portfolio-interview/appendix-a.md"
n = int(sys.argv[1]) if len(sys.argv) > 1 else 60

items = []
section = ""
for line in BANK.read_text(encoding="utf-8").splitlines():
    if line.startswith("## "):
        section = line[3:].strip()
    m = re.match(r"- \*\*(.+?)\*\* — (.+)", line)
    if m:
        items.append((section, m.group(1), m.group(2)))

picked = random.sample(items, min(n, len(items)))
scores = []
for i, (section, q, a) in enumerate(picked, 1):
    input(f"\n[{i}/{len(picked)}] ({section})\n{q}\n— отвечай вслух, Enter когда закончишь ")
    print(f"суть: {a}")
    s = input("оценка 0 (не смог) / 1 (частично) / 2 (уверенно): ").strip()
    scores.append((section, q, int(s) if s in "012" and s else 0))

total = sum(s for _, _, s in scores)
print(f"\nитого: {total}/{2 * len(scores)} ({100 * total / (2 * len(scores)):.0f} %)")
weak = [(sec, q) for sec, q, s in scores if s < 2]
print("слабые вопросы:")
for sec, q in weak:
    print(f"  - [{sec}] {q}")
