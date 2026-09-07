# Глоссарий дня 2

Термины по алфавиту, с английским оригиналом и указанием, где встречаются. К каждому термину — схема-подсказка в палитре курса: серый — вход, синий — процесс, зелёный — результат, коричневый — ошибка, жёлтый — данные/хранение, фиолетовый — внешнее/сравнение.

---

**Bi-encoder** — модель эмбеддингов: кодирует запрос и документ независимо в векторы, близость которых сравнивается. Быстрая, но не видит взаимодействия запроса и текста. Глава 1.

```mermaid
flowchart LR
    Q["Запрос"] --> EQ["Вектор запроса"]
    D["Документ"] --> ED["Вектор документа"]
    EQ --> S["Сравнение векторов\n(независимо кодированных)"]
    ED --> S
    style Q fill:#2d2d2d,color:#fff
    style D fill:#2d2d2d,color:#fff
    style EQ fill:#1a5276,color:#fff
    style ED fill:#1a5276,color:#fff
    style S fill:#4a235a,color:#fff
```

---

**BM25** — классическая функция ранжирования полнотекстового поиска: частота слова с насыщением, вес редких слов (IDF), нормализация на длину. Для русского требует стемминга или лемматизации. Главы 1–2.

```mermaid
flowchart LR
    T["Текст запроса и документов"] --> TOK["Токены → основы слов\n(стемминг)"]
    TOK --> F["Частота слова\nс насыщением"]
    TOK --> IDF["Вес редких слов\n(IDF)"]
    F --> SC["Скор BM25"]
    IDF --> SC
    style T fill:#2d2d2d,color:#fff
    style TOK fill:#1a5276,color:#fff
    style F fill:#1a5276,color:#fff
    style IDF fill:#1a5276,color:#fff
    style SC fill:#1e8449,color:#fff
```

---

**Condense question** — переформулировка уточняющего вопроса с учётом истории диалога в самостоятельный перед поиском. Пробел web-agent. Главы 1 и 3.

```mermaid
flowchart LR
    H["История: «А для чего этот порт?»"] --> M["Модель: перефразирует\nс учётом контекста"]
    M --> Q["Самостоятельный вопрос:\n«Для чего порт 11434 Ollama?»"]
    Q --> S["Поиск"]
    style H fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style Q fill:#1e8449,color:#fff
    style S fill:#4a235a,color:#fff
```

---

**Cross-encoder (реранкер, reranking)** — модель, читающая пару «запрос + фрагмент» вместе и выдающая релевантность; точнее bi-encoder, применяется к 20–50 кандидатам. В лабе — `BAAI/bge-reranker-v2-m3`. Главы 1–3.

```mermaid
flowchart LR
    C["20–50 кандидатов\nиз hybrid-поиска"] --> P["Модель читает пару\n(вопрос, фрагмент) вместе"]
    P --> R["Скор релевантности\nдля каждой пары"]
    R --> TOP["Топ-k после\nпереранжирования"]
    style C fill:#2d2d2d,color:#fff
    style P fill:#4a235a,color:#fff
    style R fill:#1a5276,color:#fff
    style TOP fill:#1e8449,color:#fff
```

---

**Dimension mismatch** — ошибка при вставке вектора другой размерности в коллекцию: следствие смены модели эмбеддингов без переиндексации. Инцидент web-agent. Главы 1 и 3.

```mermaid
flowchart LR
    OLD["Коллекция: векторы\nмодели A, размер 1536"] --> INS["Вставка вектора\nмодели B, размер 1024"]
    INS --> ERR["Dimension mismatch"]
    ERR -. фикс .-> NEW["Новая коллекция\nдля модели B"]
    style OLD fill:#7d6608,color:#fff
    style INS fill:#1a5276,color:#fff
    style ERR fill:#6e2f1a,color:#fff
    style NEW fill:#1e8449,color:#fff
```

---

**Golden-набор (golden set)** — набор пар «вопрос → где ответ» для регрессионной оценки поиска и ответов; собирается из реальных вопросов пользователей, хранится в git. Глава 2.

```mermaid
flowchart LR
    U["Реальные вопросы\nпользователей"] --> G["golden.jsonl:\nвопрос → документ → фраза"]
    G --> E["eval.py прогоняет\nчерез каждый ретривер"]
    E --> R["Hit@k, MRR:\nодно и то же мерило\nдо и после правок"]
    style U fill:#2d2d2d,color:#fff
    style G fill:#7d6608,color:#fff
    style E fill:#1a5276,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**Grounding** — привязка ответа модели к предоставленному контексту: инструкция отвечать только по документам, цитаты, честный отказ при отсутствии ответа. Глава 1.

```mermaid
flowchart LR
    CTX["Контекст: чанки\nиз поиска"] --> M["Модель: «отвечай\nтолько по контексту»"]
    Q["Вопрос"] --> M
    M --> A["Ответ с цитатой\n[файл #чанк]"]
    M -. нет ответа в контексте .-> REF["Честный отказ"]
    style CTX fill:#2d2d2d,color:#fff
    style Q fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style A fill:#1e8449,color:#fff
    style REF fill:#7d6608,color:#fff
```

---

**Гибридный поиск (hybrid search)** — объединение векторного и полнотекстового поиска; закрывает слабость dense на точных терминах и слабость BM25 на синонимах. Главы 1–2.

```mermaid
flowchart LR
    Q["Запрос"] --> D["Dense: по смыслу"]
    Q --> B["BM25: по словам"]
    D --> RRF["RRF: слияние\nдвух списков"]
    B --> RRF
    RRF --> K["Топ-k гибрида"]
    style Q fill:#2d2d2d,color:#fff
    style D fill:#1a5276,color:#fff
    style B fill:#1a5276,color:#fff
    style RRF fill:#4a235a,color:#fff
    style K fill:#1e8449,color:#fff
```

---

**HyDE** — генерация гипотетического ответа моделью и поиск по его эмбеддингу вместо эмбеддинга вопроса. Глава 1.

```mermaid
flowchart LR
    Q["Вопрос"] --> M["Модель придумывает\nправдоподобный ответ"]
    M --> H["Гипотетический ответ\n(может быть неверным)"]
    H --> E["Эмбеддинг ответа,\nне вопроса"]
    E --> S["Поиск по этому вектору"]
    style Q fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style H fill:#7d6608,color:#fff
    style E fill:#1a5276,color:#fff
    style S fill:#1e8449,color:#fff
```

---

**Изоляция tenant (tenant isolation)** — разделение данных клиентов в мультитенантной системе; в web-agent — коллекция на tenant, а не фильтр в общей. Главы 1 и 3.

```mermaid
flowchart LR
    T1["Tenant 1"] --> C1["Своя коллекция"]
    T2["Tenant 2"] --> C2["Своя коллекция"]
    C1 -. нет общего пространства .-x C2
    style T1 fill:#2d2d2d,color:#fff
    style T2 fill:#2d2d2d,color:#fff
    style C1 fill:#1e8449,color:#fff
    style C2 fill:#1e8449,color:#fff
```

---

**Контекстная нарезка (contextual chunking)** — добавление названия документа и секции к чанку перед эмбеддингом, чтобы фрагмент без заголовка не терял смысл. Лаба, шаг 7.

```mermaid
flowchart LR
    CH["Чанк: «…порт 11434…»\nбез заголовка"] --> ADD["+ имя файла и секция\nперед эмбеддингом"]
    ADD --> CTX["«01-retrieval.md\nОтвет: …порт 11434…»"]
    CTX --> E["Эмбеддинг с контекстом"]
    style CH fill:#2d2d2d,color:#fff
    style ADD fill:#1a5276,color:#fff
    style CTX fill:#7d6608,color:#fff
    style E fill:#1e8449,color:#fff
```

---

**Косинусное сходство (cosine similarity)** — мера близости векторов по углу; для нормализованных векторов эквивалентна по порядку скалярному произведению и L2. Chroma по умолчанию использует L2. Глава 1.

```mermaid
flowchart LR
    V1["Вектор запроса"] --> A["Угол между\nвекторами"]
    V2["Вектор документа"] --> A
    A --> S["Меньше угол →\nближе по смыслу"]
    style V1 fill:#2d2d2d,color:#fff
    style V2 fill:#2d2d2d,color:#fff
    style A fill:#1a5276,color:#fff
    style S fill:#1e8449,color:#fff
```

---

**Lost in the middle** — снижение внимания модели к информации в середине длинного контекста; влияет на порядок фрагментов при сборке контекста. Главы 1 и 3.

```mermaid
flowchart LR
    S["Начало контекста:\nвнимание высокое"] --> M["Середина:\nвнимание падает"]
    M --> E["Конец:\nвнимание снова высокое"]
    F["Важный факт в середине"] -. риск .-> M
    style S fill:#1e8449,color:#fff
    style M fill:#6e2f1a,color:#fff
    style E fill:#1e8449,color:#fff
    style F fill:#2d2d2d,color:#fff
```

---

**Metadata filtering** — сужение поиска по атрибутам чанка: документ, дата, тип, tenant. Глава 1.

```mermaid
flowchart LR
    Q["Запрос + фильтр:\ntenant=5, дата > 2026-01"] --> F["Фильтр по метаданным"]
    F --> S["Поиск только\nсреди подходящих чанков"]
    style Q fill:#2d2d2d,color:#fff
    style F fill:#7d6608,color:#fff
    style S fill:#1e8449,color:#fff
```

---

**MRR (mean reciprocal rank)** — среднее по вопросам от `1 / позиция первого релевантного результата`; показывает, насколько высоко стоит нужное. Главы 1–2.

```mermaid
flowchart LR
    Q1["Вопрос 1: ответ на месте 1"] --> R1["1/1 = 1.0"]
    Q2["Вопрос 2: ответ на месте 3"] --> R2["1/3 ≈ 0.33"]
    Q3["Вопрос 3: не найден"] --> R3["0"]
    R1 --> AVG["Среднее = MRR"]
    R2 --> AVG
    R3 --> AVG
    style Q1 fill:#2d2d2d,color:#fff
    style Q2 fill:#2d2d2d,color:#fff
    style Q3 fill:#2d2d2d,color:#fff
    style R1 fill:#1e8449,color:#fff
    style R2 fill:#7d6608,color:#fff
    style R3 fill:#6e2f1a,color:#fff
    style AVG fill:#1a5276,color:#fff
```

---

**nDCG@k** — метрика ранжирования с учётом градаций релевантности и позиций; нужна при нескольких неравноценных релевантных фрагментах. Глава 1.

```mermaid
flowchart LR
    R["Результаты с разной\nстепенью релевантности\n(не только да/нет)"] --> W["Вес по позиции:\nвыше — важнее"]
    W --> D["Скидка (discount)\nза дальнюю позицию"]
    D --> N["Нормировка на\nидеальный порядок = nDCG"]
    style R fill:#2d2d2d,color:#fff
    style W fill:#1a5276,color:#fff
    style D fill:#1a5276,color:#fff
    style N fill:#1e8449,color:#fff
```

---

**Overlap (перекрытие)** — общая часть соседних чанков, чтобы разрезанный границей факт целиком попал хотя бы в один. Глава 1.

```mermaid
flowchart LR
    C1["Чанк 1: «…порт\n11434 слушает…»"] --- OV["Перекрытие:\nобщие 50 символов"]
    OV --- C2["Чанк 2: «…11434\nслушает Ollama…»"]
    style C1 fill:#1a5276,color:#fff
    style OV fill:#7d6608,color:#fff
    style C2 fill:#1a5276,color:#fff
```

---

**recall@k** — доля вопросов, для которых релевантный фрагмент попал в топ-k результатов; при одном релевантном на вопрос совпадает с hit rate. Главная метрика поиска для RAG. Главы 1–2.

```mermaid
flowchart LR
    ALL["10 вопросов golden-набора"] --> HIT["8 попали\nв топ-5"]
    ALL --> MISS["2 не попали"]
    HIT --> R["recall@5 = 8/10 = 0.8"]
    style ALL fill:#2d2d2d,color:#fff
    style HIT fill:#1e8449,color:#fff
    style MISS fill:#6e2f1a,color:#fff
    style R fill:#1a5276,color:#fff
```

---

**RRF (reciprocal rank fusion)** — слияние ранжированных списков суммой `1 / (k + позиция)`, обычно k = 60; не требует нормализации скорингов. Главы 1–2.

```mermaid
flowchart LR
    D["Dense: документ X\nна месте 2"] --> S1["1/(60+2)"]
    B["BM25: документ X\nна месте 5"] --> S2["1/(60+5)"]
    S1 --> SUM["Сумма = итоговый\nскор документа X"]
    S2 --> SUM
    style D fill:#1a5276,color:#fff
    style B fill:#1a5276,color:#fff
    style S1 fill:#7d6608,color:#fff
    style S2 fill:#7d6608,color:#fff
    style SUM fill:#1e8449,color:#fff
```

---

**Стемминг (stemming)** — отсечение окончаний до основы слова (snowball); минимальная морфология для BM25 по русскому. Лаба, шаг 5.

```mermaid
flowchart LR
    W1["«нашёл»"] --> ST["Стеммер"]
    W2["«находит»"] --> ST
    W3["«находил»"] --> ST
    ST --> ROOT["Одна основа:\n«наход»"]
    style W1 fill:#2d2d2d,color:#fff
    style W2 fill:#2d2d2d,color:#fff
    style W3 fill:#2d2d2d,color:#fff
    style ST fill:#1a5276,color:#fff
    style ROOT fill:#1e8449,color:#fff
```

---

**Чанк (chunk), нарезка (chunking)** — фрагмент документа как единица индексации и поиска; стратегии: фиксированная, рекурсивная, по заголовкам, семантическая, родитель–потомок. Глава 1.

```mermaid
flowchart LR
    DOC["Документ:\nдлинный текст"] --> SPLIT["Нарезка\n(рекурсивная, 500/50)"]
    SPLIT --> C1["Чанк 1"]
    SPLIT --> C2["Чанк 2"]
    SPLIT --> C3["Чанк 3"]
    style DOC fill:#2d2d2d,color:#fff
    style SPLIT fill:#1a5276,color:#fff
    style C1 fill:#7d6608,color:#fff
    style C2 fill:#7d6608,color:#fff
    style C3 fill:#7d6608,color:#fff
```

---

**Эмбеддинг (embedding)** — вектор фиксированной размерности, представляющий смысл текста; для русского — text-embedding-3, bge-m3, USER-bge-m3, multilingual-e5 (с префиксами), FRIDA (с префиксами). Глава 1.

```mermaid
flowchart LR
    T["Текст: «порт Ollama»"] --> M["Модель эмбеддингов"]
    M --> V["Вектор: [0.02, -0.14, …]\nфиксированная длина"]
    V --> SIM["Похожие по смыслу тексты →\nблизкие векторы"]
    style T fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style V fill:#7d6608,color:#fff
    style SIM fill:#1e8449,color:#fff
```
