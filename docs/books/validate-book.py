#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Механическая проверка книги перед сдачей. Слабый агент ОБЯЗАН прогнать
этот скрипт и добиться строки "PASS" (код возврата 0). Ошибки (ERROR)
блокируют сдачу, предупреждения (WARN) — на усмотрение.

Использование (из папки docs/books/):
    python3 validate-book.py <папка-книги>                 # проверить всю книгу
    python3 validate-book.py <папка-книги> <chapter-NN.md> # проверить одну главу

Примеры:
    python3 validate-book.py backend
    python3 validate-book.py backend chapter-03.md
"""
import sys, os, re, glob

# --- пороги (можно поднимать по мере зрелости серии) ---
PALETTE = {"#2d2d2d", "#1a5276", "#1e8449", "#6e2f1a", "#7d6608", "#4a235a"}
MIN_DIAGRAMS      = 2    # минимум mermaid-диаграмм на книгу (компактный формат «день»)
MIN_GLOSSARY      = 6    # минимум терминов в glossary.md
MIN_CHAPTER_WORDS = 250  # глава короче — почти наверняка заглушка

REQUIRED_AUX = ["glossary.md"]
FORBIDDEN = [
    (r"\bfoo\b", "плейсхолдер foo"),
    (r"\bfoobar\b", "плейсхолдер foobar"),
    (r"\bbaz\b", "плейсхолдер baz"),
    (r"lorem ipsum", "рыба lorem ipsum"),
    (r"\bTODO\b", "оставленный TODO"),
    (r"\bFIXME\b", "оставленный FIXME"),
    (r"здесь будет", "незаполненная заглушка «здесь будет»"),
    (r"\bНАПИСАТЬ\b", "заглушка НАПИСАТЬ"),
    (r"<placeholder", "тег placeholder"),
]

# Строки-инструкции из шаблона главы: в готовом тексте их быть НЕ должно
# (слабый агент склонен копировать шаблон и не дописывать содержание).
TEMPLATE_LEAKS = [
    "Объясняй по схеме",
    "Код — только в блоках",
    "Минимум одна диаграмма Mermaid",
    "конкретных проверяемых задани",
    "Маркированный список: как читатель",
    "Короткое название",
    "что именно сделать руками",
    "2–4 предложения",
]
# Иероглифы/кана (CJK, хангыль) — артефакт генерации, в русском тексте недопустимы
CJK_RE = re.compile(r"[぀-ヿ㐀-鿿가-힯]")

errors, warns = [], []
def err(f, m):  errors.append(f"ERROR  {f}: {m}")
def warn(f, m): warns.append(f"WARN   {f}: {m}")


def parse_fences(text):
    """Возвращает (сбалансированы?, mermaid-блоки[str], всего фенсов, все блоки[str])."""
    lines = text.split("\n")
    in_fence = False
    lang = ""
    buf = []
    mermaids = []
    blocks = []
    total = 0
    for ln in lines:
        s = ln.lstrip()
        if s.startswith("```"):
            total += 1
            if not in_fence:
                in_fence = True
                lang = s[3:].strip().lower()
                buf = []
            else:
                body = "\n".join(buf)
                blocks.append(body)
                if lang == "mermaid":
                    mermaids.append(body)
                in_fence = False
                lang = ""
        elif in_fence:
            buf.append(ln)
    balanced = (total % 2 == 0) and (not in_fence)
    return balanced, mermaids, total, blocks


def check_mermaid(fname, block):
    # у диаграммы должны быть стилизованные узлы из палитры курса
    styles = re.findall(r"style\s+\S+\s+fill:(#[0-9a-fA-F]{6})", block)
    if not styles:
        err(fname, "mermaid-диаграмма без единой строки style … fill:#… (нужна палитра курса)")
        return
    bad = [c for c in styles if c.lower() not in PALETTE]
    if bad:
        warn(fname, f"цвета вне палитры курса: {', '.join(sorted(set(bad)))}")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def check_md(path):
    """Проверки одного .md-файла. Возвращает число mermaid-диаграмм в нём."""
    fn = os.path.basename(path)
    text = read(path)
    low = text.lower()

    balanced, mermaids, _, blocks = parse_fences(text)
    if not balanced:
        err(fn, "несбалансированные ``` (открыт код-блок не закрыт)")
    for blk in mermaids:
        check_mermaid(fn, blk)

    # дубли код-блоков (копипаст: например, дважды вставленное дерево файлов)
    seen = {}
    for b in blocks:
        key = b.strip()
        if key and len(key.splitlines()) >= 3:
            seen[key] = seen.get(key, 0) + 1
    for key, cnt in seen.items():
        if cnt > 1:
            err(fn, f"код-блок повторяется {cnt} раза (дубль/копипаст)")
    # несколько блоков дерева файлов в одном файле — почти всегда забытый дубль
    tree_blocks = [b for b in blocks if "├──" in b or "└──" in b]
    if len(tree_blocks) > 1:
        err(fn, f"несколько блоков файловой структуры ({len(tree_blocks)}) — оставь один")

    for pat, human in FORBIDDEN:
        if re.search(pat, text, re.IGNORECASE):
            err(fn, f"запрещено: {human}")
    if re.search(r"example\.com", low):
        warn(fn, "example.com — замени реальным контекстом (свои проекты: web-agent, ai-agent-memory)")
    for leak in TEMPLATE_LEAKS:
        if leak in text:
            err(fn, f"в тексте осталась строка-инструкция из шаблона: «{leak}…» — замени содержанием")
    if CJK_RE.search(text):
        err(fn, "иероглифы/кана (CJK) в тексте — артефакт генерации, убери")
    if "<<" in text:  # маркер плейсхолдера «<< … >>»; ">>" отдельно не проверяем — это SQL-оператор ->>
        err(fn, "остался незаполненный плейсхолдер << … >>")

    # правила глав
    if re.match(r"chapter-\d+\.md$", fn):
        first = next((l for l in text.split("\n") if l.strip()), "")
        if not first.startswith("# "):
            err(fn, "первая строка должна быть заголовком '# …'")
        n_check = len(re.findall(r"(?m)^#{2,3}\s+что проверить", low))
        if n_check == 0:
            err(fn, "нет заголовка '## Что проверить' (обязателен в каждой главе)")
        elif n_check > 1:
            err(fn, f"заголовок '## Что проверить' повторяется {n_check} раза — оставь один")
        n_prac = len(re.findall(r"(?m)^#{2,3}\s+практика", low))
        if n_prac > 1:
            err(fn, f"заголовок '## Практика' повторяется {n_prac} раза — оставь один")
        elif n_prac == 0:
            warn(fn, "нет заголовка '## Практика'")
        words = len(re.findall(r"\S+", text))
        if words < MIN_CHAPTER_WORDS:
            warn(fn, f"глава очень короткая ({words} слов) — возможно, заглушка")
        if "```" not in text:
            warn(fn, "в главе нет ни одного код-блока/примера")

    return len(mermaids)


def report(scope, diagrams=None):
    for line in errors:
        print(line)
    for line in warns:
        print(line)
    print("-" * 48)
    tail = f"диаграмм: {diagrams} | " if diagrams is not None else ""
    print(f"[{scope}] {tail}ошибок: {len(errors)} | предупреждений: {len(warns)}")
    if errors:
        print("FAIL — исправь ERROR и запусти снова")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 validate-book.py <папка-книги> [chapter-NN.md]")
        sys.exit(2)
    book = sys.argv[1].rstrip("/")
    if not os.path.isdir(book):
        print(f"ERROR: папки '{book}' нет (запускай из docs/books/)")
        sys.exit(2)
    name = os.path.basename(book)

    # --- режим одной главы: проверяем только указанный файл ---
    single = sys.argv[2] if len(sys.argv) > 2 else None
    if single:
        path = os.path.join(book, single)
        if not os.path.isfile(path):
            print(f"ERROR: файла '{path}' нет")
            sys.exit(2)
        check_md(path)
        report(f"{name}/{single}")
        return

    # --- полная проверка книги ---
    # 1. Обязательные файлы
    if not os.path.isfile(os.path.join(book, "book.md")):
        err(name, "нет book.md (оглавление книги)")
    for aux in REQUIRED_AUX:
        if not os.path.isfile(os.path.join(book, aux)):
            err(name, f"нет обязательного файла {aux}")

    # 2. Главы: смежная нумерация с chapter-00
    nums = sorted(int(m.group(1))
                  for p in glob.glob(os.path.join(book, "chapter-*.md"))
                  for m in [re.search(r"chapter-(\d+)\.md$", p)] if m)
    if not nums:
        err(name, "нет ни одной chapter-NN.md")
    else:
        if nums[0] not in (0, 1):
            err(name, "главы должны начинаться с chapter-00.md или chapter-01.md")
        gaps = [i for i in range(nums[0], nums[-1] + 1) if i not in nums]
        if gaps:
            err(name, f"разрыв в нумерации глав: не хватает {', '.join(f'chapter-{i:02d}.md' for i in gaps)}")

    # 3. Проверка каждого .md
    total_diagrams = 0
    for p in sorted(glob.glob(os.path.join(book, "*.md"))):
        total_diagrams += check_md(p)

    # 4. Диаграммы на книгу
    if total_diagrams < MIN_DIAGRAMS:
        err(name, f"мало диаграмм: {total_diagrams} из минимум {MIN_DIAGRAMS} (mermaid с палитрой)")

    # 5. Глоссарий
    gpath = os.path.join(book, "glossary.md")
    if os.path.isfile(gpath):
        gterms = len(re.findall(r"^\s*(?:[-*]\s*)?\*\*.+?\*\*", read(gpath), re.MULTILINE))
        if gterms < MIN_GLOSSARY:
            err("glossary.md", f"мало терминов: {gterms} из минимум {MIN_GLOSSARY} (формат '**Термин** — …')")

    # 6. files.json (регистрация в каталоге) — мягкая проверка
    if os.path.isfile("files.json"):
        if f'"{name}"' not in read("files.json"):
            warn(name, f"книга не зарегистрирована в files.json (ключ \"{name}\" в courses) — нужно для показа в каталоге")

    report(name, total_diagrams)


if __name__ == "__main__":
    main()
