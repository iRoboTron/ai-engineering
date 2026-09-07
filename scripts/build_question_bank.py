#!/usr/bin/env python3
"""Build the reviewed interview bank; no extraction/truncation of answer prose.

Edit question-rubrics.json deliberately. This generator verifies question coverage
against chapter-03 headings and emits the Markdown and portable mock data.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BOOKS = ROOT / 'docs/books'
SOURCE = ROOT / 'scripts/question-rubrics.json'


def render(records):
    expected = {}
    for chapter in sorted(BOOKS.glob('0[1-7]-*/chapter-03.md')):
        day = int(chapter.parent.name[:2])
        for n, question in enumerate(re.findall(r'^### (.+)$', chapter.read_text(encoding='utf-8'), re.M), 1):
            expected[f'd{day}-q{n:02d}'] = (day, question, f'{chapter.parent.name}/chapter-03.md')
    if len(records) != 132 or len(expected) != 132:
        raise ValueError('Expected all 132 reviewed questions; review coverage after curriculum changes')
    seen = set()
    for item in records:
        ident = item['id']
        if ident in seen:
            raise ValueError(f'Duplicate rubric: {ident}')
        seen.add(ident)
        actual = (item['day'], item['question'], item['source'])
        if expected.get(ident) != actual:
            raise ValueError(f'Question/source changed for {ident}; review the corresponding rubric')
        if len(item['criteria']) != 3 or any(len(v.strip()) < 15 for v in item['criteria']):
            raise ValueError(f'{ident}: three substantive criteria required')
        if len(item['mistake'].strip()) < 15:
            raise ValueError(f'{ident}: concrete mistake required')
    if seen != set(expected):
        raise ValueError('Missing or extra rubric IDs')
    lines = [
        '# Приложение A. 132 вопроса: рубрики для самопроверки', '',
        '> Это проверяемые тезисы, а не первые фразы ответов. Рубрики отредактированы отдельно от полных объяснений.',
        '> Генерация: `python3 scripts/build_question_bank.py`; контроль рассинхронизации: добавь `--check`.', '',
        '## Как оценивать', '',
        'Сначала ответь без подсказки. Затем засчитай по одному баллу за каждый из трёх тезисов, который действительно раскрыл правильно. '
        'Уверенность сама по себе балла не даёт. Указанная типичная ошибка ограничивает оценку нулём до исправления: '
        'это намеренно строгий учебный сигнал, не модель решения работодателя. '
        'Если критерий непонятен, открой полный ответ и первоисточник; не засчитывай спорный тезис автоматически.', '',
        'Minimum — 12 вопросов за 45 минут: около двух минут на ответ, минуты на сверку и остаток на разбор. '
        'Это малая выборка, не оценка квалификации. Stretch — 60 вопросов за 2–3 часа плюс разбор. '
        'Для system design краткий ответ здесь проверяет план; полноценное проектирование проводится отдельно.', '',
        'Клиент mock читает `question-bank.json`, сохраняет seed, выбранные вопросы, тезисы и оценки по дням. '
        'Результат по дню с одним-двумя вопросами — сигнал для повторения, не точный процент владения темой.', ''
    ]
    previous = None
    for item in records:
        if item['day'] != previous:
            previous = item['day']
            lines += [f'## День {previous}', '']
        lines += [f"### {item['id']}. {item['question']}", '', '**Обязательные тезисы:**', '']
        lines += [f'{n}. {criterion}.' for n, criterion in enumerate(item['criteria'], 1)]
        lines += ['', f"**Типичная ошибка:** {item['mistake']}.", '',
                  f"[Полный ответ и контекст — глава 3 дня {item['day']}](../{item['source']}).", '']
    lines += ['## Что проверить', '',
              '- [ ] Ответ дан до открытия рубрики; баллы выставлены за содержание, а не уверенность.',
              '- [ ] Все спорные места разобраны, типичная ошибка исправлена отдельно.',
              '- [ ] Известны размер выборки, seed и ограничения сравнения повторных mock.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    records = json.loads(SOURCE.read_text(encoding='utf-8'))
    outputs = {
        BOOKS / '07-portfolio-interview/appendix-a.md': render(records),
        ROOT / 'labs/day7-interview/question-bank.json': json.dumps(records, ensure_ascii=False, indent=2) + '\n',
    }
    outdated = []
    for path, body in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != body:
                outdated.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding='utf-8')
    if outdated:
        raise SystemExit('Question bank out of date: ' + ', '.join(outdated))
    print('Question bank: 132 rubrics, coverage verified' + (' (check)' if args.check else ' (written)'))


if __name__ == '__main__':
    main()
