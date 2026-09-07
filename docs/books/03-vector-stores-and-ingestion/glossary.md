# Глоссарий дня 3

Термины по алфавиту, с английским оригиналом и указанием, где встречаются. К каждому термину — схема-подсказка в палитре курса: серый — вход, синий — процесс, зелёный — результат, коричневый — ошибка/опасность, жёлтый — данные/хранение, фиолетовый — внешнее.

---

**ANN (approximate nearest neighbours)** — приближённый поиск ближайших соседей: быстрее точного перебора ценой пропуска части настоящих соседей; качество измеряется recall индекса. Глава 1.

```mermaid
flowchart LR
    Q["Вектор запроса"] --> EX["Точный перебор:\nвсе векторы, медленно"]
    Q --> ANN["ANN-индекс:\nграф/кластеры, быстро"]
    EX --> R1["100% верных соседей"]
    ANN --> R2["~95% верных соседей,\nв разы быстрее"]
    style Q fill:#2d2d2d,color:#fff
    style EX fill:#7d6608,color:#fff
    style ANN fill:#1a5276,color:#fff
    style R1 fill:#1e8449,color:#fff
    style R2 fill:#1e8449,color:#fff
```

---

**BYPASSRLS** — атрибут роли PostgreSQL, позволяющий обходить политики row-level security; нужен загрузчикам и администраторам, не приложению. Лаба, шаг 3.

```mermaid
flowchart LR
    ADMIN["rag_admin\nBYPASSRLS"] --> ALL["Видит все строки\nвсех tenant"]
    APP["rag_app\nNOBYPASSRLS"] --> POL["Видит только строки\nсвоего tenant по политике"]
    style ADMIN fill:#4a235a,color:#fff
    style APP fill:#2d2d2d,color:#fff
    style ALL fill:#6e2f1a,color:#fff
    style POL fill:#1e8449,color:#fff
```

---

**DLQ (dead-letter queue)** — очередь для задач, которые не удалось обработать после повторов (битые файлы, недоступный источник); разбирается отдельно. Главы 1 и 3.

```mermaid
flowchart LR
    T["Задача индексации"] --> P["Попытка обработать"]
    P -- успех --> DONE["Готово"]
    P -- ошибка, повтор 1..N --> P
    P -- все повторы исчерпаны --> DLQ["Dead-letter queue"]
    DLQ --> H["Разбор человеком"]
    style T fill:#2d2d2d,color:#fff
    style P fill:#1a5276,color:#fff
    style DONE fill:#1e8449,color:#fff
    style DLQ fill:#6e2f1a,color:#fff
    style H fill:#7d6608,color:#fff
```

---

**Docling** — открытый инструмент IBM для преобразования документов: раскладка, порядок чтения, таблицы в Markdown или JSON без тяжёлого GPU. Лаба, шаг 8.

```mermaid
flowchart LR
    PDF["PDF с таблицей"] --> PY["pypdf: текст одним\nпотоком, таблица склеена"]
    PDF --> DL["Docling: раскладка\nи порядок чтения"]
    DL --> MD["Markdown-таблица,\nструктура сохранена"]
    style PDF fill:#2d2d2d,color:#fff
    style PY fill:#6e2f1a,color:#fff
    style DL fill:#4a235a,color:#fff
    style MD fill:#1e8449,color:#fff
```

---

**ef_search / ef_construction / m** — параметры HNSW: ширина поиска при запросе (меняет recall без перестроения), ширина поиска при построении, число связей на узел. Глава 1.

```mermaid
flowchart LR
    M["m: связей на узел\n(задан при создании)"] --> BUILD["ef_construction:\nширина при построении"]
    BUILD --> IDX["Готовый индекс"]
    IDX --> SEARCH["ef_search: ширина\nпри каждом запросе"]
    SEARCH -. выше — точнее, медленнее .-> IDX
    style M fill:#7d6608,color:#fff
    style BUILD fill:#7d6608,color:#fff
    style IDX fill:#1a5276,color:#fff
    style SEARCH fill:#1e8449,color:#fff
```

---

**GIN-индекс** — обобщённый инвертированный индекс PostgreSQL; используется для `tsvector` в полнотекстовом поиске. Лаба, шаг 4.

```mermaid
flowchart LR
    ROWS["Строки с tsvector"] --> GIN["GIN-индекс:\nслово → список строк"]
    Q["Запрос: «порт»"] --> GIN
    GIN --> R["Строки, где встречается\n«порт», без полного скана"]
    style ROWS fill:#2d2d2d,color:#fff
    style Q fill:#2d2d2d,color:#fff
    style GIN fill:#7d6608,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**halfvec** — тип pgvector с 16-битными компонентами: вдвое меньше памяти, снимает лимит 2000 измерений для индекса. Глава 1, практика.

```mermaid
flowchart LR
    V32["vector: 32 бита\nна компоненту"] --> SIZE1["Полный размер"]
    V16["halfvec: 16 бит\nна компоненту"] --> SIZE2["Вдвое меньше памяти,\nблизкое качество"]
    style V32 fill:#2d2d2d,color:#fff
    style V16 fill:#1a5276,color:#fff
    style SIZE1 fill:#7d6608,color:#fff
    style SIZE2 fill:#1e8449,color:#fff
```

---

**HNSW (hierarchical navigable small world)** — многоуровневый граф ближайших соседей; индекс по умолчанию для векторного поиска в pgvector, Qdrant, Chroma. Глава 1.

```mermaid
flowchart TD
    TOP["Верхний слой:\nредкие «дальние» связи"] --> MID["Средний слой"]
    MID --> BOT["Нижний слой:\nвсе точки, плотные связи"]
    Q["Запрос входит сверху"] --> TOP
    BOT --> R["Ближайшие соседи\nнайдены за log(N) шагов"]
    style TOP fill:#4a235a,color:#fff
    style MID fill:#1a5276,color:#fff
    style BOT fill:#1a5276,color:#fff
    style Q fill:#2d2d2d,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**Идемпотентность (idempotency)** — повтор операции даёт тот же результат; в индексации достигается детерминированными id чанков и upsert. Главы 1 и 3.

```mermaid
flowchart LR
    R1["Запрос записи\nid=doc:3"] --> S["Строка id=doc:3\nсоздана"]
    R2["Тот же запрос\nповторно (сбой сети)"] --> S2["Та же строка\nобновлена, не задвоена"]
    style R1 fill:#2d2d2d,color:#fff
    style R2 fill:#2d2d2d,color:#fff
    style S fill:#1e8449,color:#fff
    style S2 fill:#1e8449,color:#fff
```

---

**Итеративный скан (iterative index scan)** — режим pgvector 0.8+: обход индекса продолжается, пока после фильтра не наберётся LIMIT строк; `hnsw.iterative_scan = strict_order | relaxed_order`. Глава 1, лаба шаг 4.

```mermaid
flowchart LR
    Q["Запрос + фильтр\n(один tenant) + LIMIT 5"] --> SCAN["Обход HNSW"]
    SCAN --> CHK{"Набралось 5\nпосле фильтра?"}
    CHK -- нет --> SCAN
    CHK -- да --> R["5 строк"]
    style Q fill:#2d2d2d,color:#fff
    style SCAN fill:#1a5276,color:#fff
    style CHK fill:#7d6608,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**IVFFlat** — индекс на кластерах (центроидах): параметры `lists` и `probes`; быстрее строится, меньше памяти, ниже recall, требует построения по заполненной таблице. Глава 1.

```mermaid
flowchart LR
    ALL["Все векторы"] --> CL["Разбиты на lists\nкластеров по центроидам"]
    Q["Запрос"] --> P["Ищет только\nв probes ближайших\nкластерах"]
    CL --> P
    P --> R["Кандидаты\n(не все векторы)"]
    style ALL fill:#2d2d2d,color:#fff
    style CL fill:#7d6608,color:#fff
    style Q fill:#2d2d2d,color:#fff
    style P fill:#1a5276,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**Квантизация (quantization)** — сжатие векторов: half (16 бит), int8, бинарная; экономит память ценой точности, компенсируемой переранжированием. Глава 1.

```mermaid
flowchart LR
    V["Вектор fp32"] --> H["half: 16 бит"]
    V --> I["int8: 8 бит"]
    V --> B["бинарная: 1 бит"]
    H --> M["Меньше памяти,\nбольше — точнее"]
    I --> M
    B --> M
    M -. точность теряется .-> RR["Компенсация:\nреранжирование\nна полных векторах"]
    style V fill:#2d2d2d,color:#fff
    style H fill:#1a5276,color:#fff
    style I fill:#1a5276,color:#fff
    style B fill:#1a5276,color:#fff
    style M fill:#7d6608,color:#fff
    style RR fill:#1e8449,color:#fff
```

---

**MinHash** — техника поиска почти-дублей текстов через хэширование множеств шинглов; для дедупликации версий документов. Главы 1 и 3.

```mermaid
flowchart LR
    D1["Документ v1"] --> SH1["Шинглы → MinHash-сигнатура"]
    D2["Документ v2\n(почти копия)"] --> SH2["Шинглы → MinHash-сигнатура"]
    SH1 --> CMP["Сравнение сигнатур"]
    SH2 --> CMP
    CMP --> DUP["Высокое сходство →\nпочти-дубль"]
    style D1 fill:#2d2d2d,color:#fff
    style D2 fill:#2d2d2d,color:#fff
    style SH1 fill:#1a5276,color:#fff
    style SH2 fill:#1a5276,color:#fff
    style CMP fill:#7d6608,color:#fff
    style DUP fill:#1e8449,color:#fff
```

---

**Multi-tenancy** — обслуживание нескольких клиентов одним инстансом с изоляцией данных: коллекция на tenant, ключ + фильтр, RLS, схема или база на tenant. Глава 1.

```mermaid
flowchart LR
    ONE["Один инстанс\nбазы/сервиса"] --> T1["Tenant 1: своя\nколлекция/RLS-фильтр"]
    ONE --> T2["Tenant 2: своя\nколлекция/RLS-фильтр"]
    ONE --> T3["Tenant 3: своя\nколлекция/RLS-фильтр"]
    style ONE fill:#2d2d2d,color:#fff
    style T1 fill:#1e8449,color:#fff
    style T2 fill:#1e8449,color:#fff
    style T3 fill:#1e8449,color:#fff
```

---

**pgvector** — расширение PostgreSQL с типами `vector`, `halfvec`, `sparsevec`, операторами `<=>`, `<->`, `<#>` и индексами HNSW и IVFFlat. Главы 1–3.

```mermaid
flowchart LR
    PG["PostgreSQL"] --> EXT["CREATE EXTENSION\nvector"]
    EXT --> TY["Типы: vector,\nhalfvec, sparsevec"]
    EXT --> OP["Операторы: <=>,\n<->, <#>"]
    EXT --> IDX["Индексы: HNSW,\nIVFFlat"]
    style PG fill:#2d2d2d,color:#fff
    style EXT fill:#7d6608,color:#fff
    style TY fill:#1a5276,color:#fff
    style OP fill:#1a5276,color:#fff
    style IDX fill:#1a5276,color:#fff
```

---

**Qdrant** — векторная БД на Rust: фильтруемый HNSW, payload-индексы, sparse-векторы, квантизация, снапшоты, multi-tenancy через tenant-ключ. Глава 1, практика.

```mermaid
flowchart LR
    C["Коллекция Qdrant"] --> V["Векторы + payload\n(tenant_id, метаданные)"]
    V --> IDX["Payload-индекс\nна tenant_id"]
    Q["Запрос + фильтр\nby tenant_id"] --> IDX
    IDX --> R["Только строки\nсвоего tenant"]
    style C fill:#2d2d2d,color:#fff
    style V fill:#7d6608,color:#fff
    style IDX fill:#1a5276,color:#fff
    style Q fill:#2d2d2d,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**RLS (row-level security)** — политики PostgreSQL, фильтрующие строки на уровне базы; `FORCE ROW LEVEL SECURITY` применяет их и к владельцу. Лаба, шаги 2 и 7.

```mermaid
flowchart LR
    Q["SELECT * FROM chunks"] --> POL{"Политика:\ntenant_id = текущий?"}
    POL -- да --> VIS["Строка видна"]
    POL -- нет --> HID["Строка скрыта\n(не ошибка, просто не видна)"]
    style Q fill:#2d2d2d,color:#fff
    style POL fill:#7d6608,color:#fff
    style VIS fill:#1e8449,color:#fff
    style HID fill:#6e2f1a,color:#fff
```

---

**RRF в SQL** — слияние dense- и полнотекстового списков через CTE и `row_number()`; тот же алгоритм, что вчера, но внутри базы. Лаба, шаг 5.

```mermaid
flowchart LR
    D["CTE dense:\nrow_number() по <=>"] --> J["JOIN по id"]
    F["CTE fts:\nrow_number() по ts_rank_cd"] --> J
    J --> SC["COALESCE(1/(60+r), 0)\nсумма по обоим спискам"]
    SC --> R["ORDER BY score\nLIMIT k — один SQL-запрос"]
    style D fill:#1a5276,color:#fff
    style F fill:#1a5276,color:#fff
    style J fill:#7d6608,color:#fff
    style SC fill:#1a5276,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**tsvector / tsquery** — типы полнотекстового поиска PostgreSQL; конфигурация `russian` даёт стемминг; `ts_rank_cd` — ранжирование (не BM25). Главы 1–2.

```mermaid
flowchart LR
    TXT["Текст чанка"] --> TSV["to_tsvector('russian', text)\n→ tsvector"]
    Q["Запрос"] --> TSQ["plainto_tsquery('russian', q)\n→ tsquery"]
    TSV --> M["tsv @@ tsquery"]
    TSQ --> M
    M --> RANK["ts_rank_cd:\nранжирование совпадений"]
    style TXT fill:#2d2d2d,color:#fff
    style Q fill:#2d2d2d,color:#fff
    style TSV fill:#1a5276,color:#fff
    style TSQ fill:#1a5276,color:#fff
    style M fill:#7d6608,color:#fff
    style RANK fill:#1e8449,color:#fff
```

---

**Upsert** — вставка с обновлением при конфликте ключа (`ON CONFLICT ... DO UPDATE`); основа идемпотентной записи чанков. Лаба, шаг 3.

```mermaid
flowchart LR
    W["INSERT id=doc:3"] --> EX{"id уже\nсуществует?"}
    EX -- нет --> INS["Новая строка"]
    EX -- да --> UPD["ON CONFLICT DO UPDATE:\nобновить существующую"]
    style W fill:#2d2d2d,color:#fff
    style EX fill:#7d6608,color:#fff
    style INS fill:#1e8449,color:#fff
    style UPD fill:#1e8449,color:#fff
```

---

**Watcher** — компонент, отслеживающий изменения источника (файлы, sitemap) по времени или хэшу и ставящий задачи индексации; в web-agent — `doc-parser/app/watcher.py`. Глава 1.

```mermaid
flowchart LR
    SRC["Источник: файлы,\nsitemap"] --> W["Watcher: проверяет\nвремя/хэш периодически"]
    W --> CHG{"Изменилось?"}
    CHG -- да --> TASK["Задача индексации\nв очередь"]
    CHG -- нет --> W
    style SRC fill:#2d2d2d,color:#fff
    style W fill:#1a5276,color:#fff
    style CHG fill:#7d6608,color:#fff
    style TASK fill:#1e8449,color:#fff
```
