# ИИ-инженер: практический трек за неделю

Компактная серия из 7 книг-дней для перехода в профессию **AI/LLM-инженер** (найм в РФ, Python).
Сайт: https://ai-engineering.adelfos.ru · Движок и правила — из курса [devops](../dev-ops/).

## Зачем и для кого

Автор уже не «с нуля»: в проде работает multi-tenant RAG-платформа `web-agent`
(FastAPI, ChromaDB, PostgreSQL, OpenRouter, Telegram, CI/CD с Ansible), сервис памяти агентов
`ai-agent-memory` (FastAPI + ChromaDB + локальные эмбеддинги), эксплуатируется Hermes Agent,
написано 38 книг по DevOps. Не хватает не опыта, а **языка вакансий, 4–5 конкретных техник и упаковки**.

Позиционирование: **AI/LLM-инженер с DevOps-базой (LLMOps)** — доводит RAG и агентов до прода
и умеет их эксплуатировать: метрики качества, трейсинг, стоимость, безопасность.

## Правила недели

- **4–6 часов в день**, один день = одна книга. Не читать вперёд, не дописывать DevOps-серию.
- **Лабы делаются в своих проектах** (`~/proj/web-agent`, `~/proj/ai-agent-memory`, Ollama из книги 23 devops),
  а не в учебной песочнице: результат лабы = артефакт в портфолио.
- **Резюме v1 на hh.ru — вечером дня 1**, отклики со дня 2. Не ждать «когда всё выучу».
- Книга изучена, когда выполнены все пункты `## Что проверить` в четырёх главах.

## Карта недели

| День | Книга | Суть | Лаба | Артефакт |
|---|---|---|---|---|
| 1 | `01-map-and-llm-basics` Карта профессии + LLM-основы | Кто такой AI-инженер в РФ, стек вакансий; токены, контекст, sampling, structured outputs, function calling, prompt caching, стоимость | Скрипт через OpenRouter: Pydantic structured output, streaming, учёт токенов/стоимости, retry | `llm-lab/` + резюме v1 |
| 2 | `02-rag-deep` RAG глубоко | Chunking, эмбеддинги для русского, hybrid BM25+вектор, реранкинг, metadata filtering, recall@k / MRR / nDCG | Golden-датасет 20–30 Q/A по документам web-agent; baseline → hybrid → rerank | Таблица recall@k |
| 3 | `03-vector-stores-and-ingestion` Векторные хранилища и индексация | pgvector (HNSW/IVFFlat), Qdrant, границы Chroma; парсинг PDF/DOCX, инкрементальная переиндексация, дедуп, multi-tenant | pgvector в Postgres на homelab, те же чанки, сравнение с Chroma | Сравнение + план миграции |
| 4 | `04-agents-langgraph-mcp` Агенты, LangGraph, MCP | Function calling и Pydantic-схемы; LangGraph state/nodes/checkpoints/HITL; лимиты шагов и бюджета; память; MCP | LangGraph-агент с 2 инструментами (база web-agent + ai-agent-memory), max_steps, cost cap | Агент с трейсом шагов |
| 5 | `05-evals-observability` Evals и наблюдаемость | Golden-датасеты, RAGAS, LLM-as-judge и смещения, регрессия в CI, Langfuse, дрейф | Langfuse self-hosted на pxhome, трейсы `/api/chat`, RAGAS на датасете дня 2 | Дашборд + оценки |
| 6 | `06-models-serving-ru-security` Модели, инференс, РФ-реалии, безопасность | Open-weight vs API, память GPU, квантизация, vLLM/Ollama/llama.cpp, LoRA vs RAG; YandexGPT/GigaChat, геоблок, 152-ФЗ; OWASP Top 10 LLM | Замер tok/s на Ollama; вызов RU-провайдера через OpenAI-совместимый клиент; 10 prompt-injection атак на web-agent | Отчёт по инъекциям |
| 7 | `07-portfolio-interview` Портфолио и собеседование | Как читают резюме; кейс web-agent; STAR-истории; system design «RAG для поддержки»; план недель 2–4 | README-кейс web-agent с цифрами, резюме v2, mock-interview, 10 откликов | Резюме v2 + кейс |

Приложение к книге 07 — сводный банк 100+ вопросов собеседования с ответами.

## Формат книги-дня

```
0N-slug/
├── book.md          ← цель дня, тайминг, оглавление
├── chapter-01.md    ← Суть: конспект (1–1.5 ч)
├── chapter-02.md    ← Лаба: пошагово, в своих проектах (2–3 ч)
├── chapter-03.md    ← Вопросы собеседования: 15–20 с ответами (0.5–1 ч)
├── chapter-04.md    ← Что показать работодателю: артефакт + формулировки для резюме
└── glossary.md
```

## Как устроен проект

- `docs/books/` — книги, движок ридера (`index.html`, `reader.html`), манифест `files.json`,
  валидатор `validate-book.py`, правила для агента `AGENT-INSTRUCTIONS.md`.
- `AUTHORING-CONVENTIONS.md` — общие конвенции серий (палитра диаграмм, глоссарии, деплой).
- `deploy-pxhome.sh` — деплой на pxhome LXC 109, `SITE_DIR=ai-engineering.adelfos.ru`.
- `career/` — резюме, STAR-истории, список вакансий. **В `.gitignore`, не деплоится.**

Проверка книги: `cd docs/books && python3 validate-book.py 0N-slug` → `PASS`.
Публикация: книга в `files.json` → `COURSE_META` в `index.html` → бамп `ASSET_VERSION` → `./deploy-pxhome.sh`.

## Что сознательно НЕ входит в неделю

Математика ML, fine-tuning руками, TypeScript-фреймворки агентов, MongoDB, доучивание DevOps-книг.
Это — недели 2–4, план в книге 07.

## Статус

- 2026-09-06 — серия заложена (скаффолд из devops), план недели утверждён.
- 2026-09-06 — написаны все 7 книг (валидатор PASS), задеплоены на LXC 109, GitHub iRoboTron/ai-engineering. Публичный HTTPS ждёт proxy host в NPM (LXC 101).
