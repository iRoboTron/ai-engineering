# Глоссарий дня 1

Термины по алфавиту, с английским оригиналом и тем, где они встречаются в книге. К каждому термину добавлена схема-подсказка: она не заменяет определение, а даёт картинку, за которую цепляется память. Палитра та же, что в главах: серый — вход, синий — процесс, зелёный — результат, коричневый — ошибка или опасность, жёлтый — внимание и хранение, фиолетовый — внешнее.

---

**AI-инженер (AI engineer, LLM engineer)** — строит продукты на готовых языковых моделях: RAG, агенты, интеграции; отвечает за качество ответов, стоимость, латентность и безопасность. Отличается от ML-инженера тем, что не обучает модели. Глава 1.

```mermaid
flowchart LR
    ML["ML-инженер"] -- обучает --> M["Модель"]
    AI["AI-инженер"] -- строит --> P["Продукт на готовой модели:\nRAG, агенты, интеграции"]
    M --> P
    P --> Q["Зона ответственности:\nкачество · стоимость ·\nлатентность · безопасность"]
    style ML fill:#4a235a,color:#fff
    style M fill:#4a235a,color:#fff
    style AI fill:#2d2d2d,color:#fff
    style P fill:#1a5276,color:#fff
    style Q fill:#1e8449,color:#fff
```

---

**Batch API** — режим провайдера для офлайн-обработки большого числа запросов в течение суток со скидкой. Подходит для переиндексации и массового извлечения данных. Глава 1, вопрос о проектировании в главе 3.

```mermaid
flowchart LR
    R["Тысячи запросов:\nпереиндексация, извлечение"] --> F["Один файл-задание"]
    F --> B["Batch API"]
    B -- до суток --> OUT["Результаты со скидкой"]
    R -. нужен ответ сейчас .-> ON["Онлайн-запрос:\nсразу, полная цена"]
    style R fill:#2d2d2d,color:#fff
    style F fill:#1a5276,color:#fff
    style B fill:#1a5276,color:#fff
    style OUT fill:#1e8449,color:#fff
    style ON fill:#4a235a,color:#fff
```

---

**Галлюцинация (hallucination)** — правдоподобный, но неверный ответ модели; следствие предсказания следующего токена при отсутствии нужной информации в контексте. Лечится RAG, structured outputs и разрешением сказать «не знаю». Главы 1 и 3.

```mermaid
flowchart LR
    Q["Вопрос, а фактов\nв контексте нет"] --> M["Модель всё равно\nпредсказывает следующий токен"]
    M --> H["Правдоподобно,\nно неверно"]
    H -. лечение .-> RAG["RAG: положить факты\nв контекст"]
    H -. лечение .-> SO["Structured outputs:\nсхема ограничивает ответ"]
    H -. лечение .-> NO["Разрешить сказать\n«не знаю»"]
    style Q fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style H fill:#6e2f1a,color:#fff
    style RAG fill:#1e8449,color:#fff
    style SO fill:#1e8449,color:#fff
    style NO fill:#1e8449,color:#fff
```

---

**Контекстное окно (context window)** — максимум токенов на один вызов: системный промпт, история, документы и ответ вместе. Глава 1.

```mermaid
flowchart LR
    S["Системный промпт"] --> SUM
    H["История диалога"] --> SUM
    D["Документы из RAG"] --> SUM
    A["Ответ модели"] --> SUM
    SUM["Всё вместе не больше\nконтекстного окна"] --> OK["Помещается:\nвызов проходит"]
    SUM --> NO["Не помещается:\nрезать историю или документы"]
    style S fill:#2d2d2d,color:#fff
    style H fill:#1a5276,color:#fff
    style D fill:#1a5276,color:#fff
    style A fill:#1a5276,color:#fff
    style SUM fill:#7d6608,color:#fff
    style OK fill:#1e8449,color:#fff
    style NO fill:#6e2f1a,color:#fff
```

---

**Exponential backoff** — стратегия повторов с растущей паузой (обычно удвоение) и случайным джиттером, чтобы не бить провайдера синхронными повторами. Глава 2, шаг 7.

```mermaid
flowchart TD
    R["Запрос"] --> E{"Ошибка 429 или 5xx?"}
    E -- нет --> OK["Ответ"]
    E -- да --> W["Пауза\n+ случайный джиттер"]
    W --> R2["Повтор"] --> E2{"Снова ошибка?"}
    E2 -- нет --> OK
    E2 -- да --> W2["Пауза в два раза длиннее\n+ джиттер"] --> R3["Повтор…"]
    R3 --> L["Лимит попыток исчерпан:\nвернуть ошибку наверх"]
    style R fill:#2d2d2d,color:#fff
    style E fill:#7d6608,color:#fff
    style E2 fill:#7d6608,color:#fff
    style W fill:#1a5276,color:#fff
    style W2 fill:#1a5276,color:#fff
    style R2 fill:#1a5276,color:#fff
    style R3 fill:#1a5276,color:#fff
    style OK fill:#1e8449,color:#fff
    style L fill:#6e2f1a,color:#fff
```

---

**Few-shot** — два-три примера «вход → выход» в промпте вместо длинных инструкций. Глава 1.

```mermaid
flowchart LR
    subgraph P["Промпт"]
        direction TB
        E1["Пример 1: вход → выход"]
        E2["Пример 2: вход → выход"]
        E3["Пример 3: вход → выход"]
        N["Новый вход"]
    end
    P --> M["Модель"] --> O["Выход в том же формате,\nчто и примеры"]
    style E1 fill:#1a5276,color:#fff
    style E2 fill:#1a5276,color:#fff
    style E3 fill:#1a5276,color:#fff
    style N fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style O fill:#1e8449,color:#fff
```

---

**Function calling (tool use)** — модель возвращает имя инструмента и аргументы по схеме, код выполняет и возвращает результат; основа агентов. Главы 1 и 3.

```mermaid
flowchart LR
    U["Вопрос пользователя"] --> M["Модель"]
    M -- выбирает инструмент --> C["Имя инструмента\n+ аргументы по JSON-схеме"]
    C --> X["Ваш код выполняет:\nAPI, БД, поиск"]
    X -- результат --> M
    M --> A["Итоговый ответ"]
    style U fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style C fill:#7d6608,color:#fff
    style X fill:#4a235a,color:#fff
    style A fill:#1e8449,color:#fff
```

---

**JSON Schema / structured outputs** — режим, в котором провайдер ограничивает генерацию под переданную схему; схему получают из Pydantic-модели, ответ валидируют ею же. Глава 1, шаг 4 лабы.

```mermaid
flowchart LR
    P["Pydantic-модель"] -- model_json_schema --> S["JSON Schema"]
    S --> PR["Провайдер ограничивает\nгенерацию под схему"]
    PR --> J["JSON-ответ"]
    J -- model_validate --> P2["Та же Pydantic-модель:\nвалидация"]
    P2 --> OK["Типизированный объект\nв коде"]
    style P fill:#2d2d2d,color:#fff
    style S fill:#1a5276,color:#fff
    style PR fill:#4a235a,color:#fff
    style J fill:#1a5276,color:#fff
    style P2 fill:#7d6608,color:#fff
    style OK fill:#1e8449,color:#fff
```

---

**KV-cache** — сохранённые представления уже обработанных токенов, чтобы не пересчитывать attention; занимает память GPU пропорционально длине контекста; основа prompt caching. Главы 1 и 3.

```mermaid
flowchart LR
    T["Токены промпта"] --> KV["Attention: ключи и значения\nпосчитаны один раз"]
    KV --> MEM["Память GPU:\nрастёт с длиной контекста"]
    N["Каждый новый токен"] -- читает кэш, не пересчитывает --> KV
    MEM -. общий префикс между запросами .-> PC["Prompt caching"]
    style T fill:#2d2d2d,color:#fff
    style KV fill:#1a5276,color:#fff
    style MEM fill:#7d6608,color:#fff
    style N fill:#1a5276,color:#fff
    style PC fill:#1e8449,color:#fff
```

---

**LLMOps** — эксплуатация LLM-приложений в проде: деплой, мониторинг качества и стоимости, трейсинг, безопасность. Позиционирование автора. Глава 1.

```mermaid
flowchart TD
    DEV["База DevOps:\nCI/CD, контейнеры, мониторинг"] --> C["LLMOps:\nLLM-приложение в проде"]
    C --> D["Деплой модели\nи сервиса"]
    C --> Q["Мониторинг качества\nи стоимости"]
    C --> T["Трейсинг запросов\nи вызовов инструментов"]
    C --> S["Безопасность:\nprompt injection, доступы"]
    style DEV fill:#4a235a,color:#fff
    style C fill:#2d2d2d,color:#fff
    style D fill:#1a5276,color:#fff
    style Q fill:#1a5276,color:#fff
    style T fill:#1a5276,color:#fff
    style S fill:#6e2f1a,color:#fff
```

---

**OpenAI-совместимый API (OpenAI-compatible API)** — формат chat completions, ставший стандартом; поддерживается OpenRouter, Ollama, vLLM и большинством провайдеров, что позволяет менять модель сменой base_url. Главы 2 и 3.

```mermaid
flowchart LR
    CODE["Ваш код:\nchat completions"] --> BU["Меняется только\nbase_url и ключ"]
    BU --> OR["OpenRouter"]
    BU --> OL["Ollama\nлокально"]
    BU --> VL["vLLM\nсвой сервер"]
    BU --> OTHER["Другой провайдер"]
    OR & OL & VL & OTHER --> SAME["Один формат\nзапроса и ответа"]
    style CODE fill:#2d2d2d,color:#fff
    style BU fill:#7d6608,color:#fff
    style OR fill:#4a235a,color:#fff
    style OL fill:#4a235a,color:#fff
    style VL fill:#4a235a,color:#fff
    style OTHER fill:#4a235a,color:#fff
    style SAME fill:#1e8449,color:#fff
```

---

**Prompt caching** — переиспользование KV-cache для совпадающего префикса промпта; чтение из кэша дешевле обычного ввода в разы; требует совпадения префикса байт в байт. Глава 1.

```mermaid
flowchart LR
    R1["Запрос 1:\nпрефикс A + вопрос 1"] --> KV["KV-cache префикса A"]
    R2["Запрос 2:\nтот же префикс A байт в байт\n+ вопрос 2"] --> HIT["Чтение из кэша:\nдешевле в разы"]
    KV --> HIT
    R3["Запрос 3:\nпрефикс A с одним\nизменённым байтом"] --> MISS["Кэш мимо:\nполная цена ввода"]
    style R1 fill:#2d2d2d,color:#fff
    style KV fill:#7d6608,color:#fff
    style R2 fill:#1a5276,color:#fff
    style HIT fill:#1e8449,color:#fff
    style R3 fill:#1a5276,color:#fff
    style MISS fill:#6e2f1a,color:#fff
```

---

**Prompt injection** — попытка через пользовательский ввод или документ переписать инструкции модели; первая защита — разделение доверенного и недоверенного в промпте. Глава 1, подробно в день 6.

```mermaid
flowchart LR
    SYS["Системный промпт:\nдоверенный"] --> M["Модель"]
    DOC["Документ или ввод пользователя:\nнедоверенный"] --> M
    INJ["Внутри документа:\n«игнорируй инструкции\nи сделай другое»"] -.-> DOC
    M --> BAD["Модель выполняет\nчужую инструкцию"]
    SEP["Защита: явно разделить\nдоверенное и недоверенное,\nданные — не команды"] --> M
    style SYS fill:#2d2d2d,color:#fff
    style DOC fill:#7d6608,color:#fff
    style INJ fill:#6e2f1a,color:#fff
    style M fill:#1a5276,color:#fff
    style BAD fill:#6e2f1a,color:#fff
    style SEP fill:#1e8449,color:#fff
```

---

**RAG (retrieval-augmented generation)** — поиск релевантных фрагментов документов и подмешивание их в промпт перед генерацией. Упоминается как контекст, подробно в день 2.

```mermaid
flowchart LR
    Q["Вопрос"] --> S["Поиск по документам"]
    S --> F["Релевантные фрагменты"]
    F --> P["Промпт:\nвопрос + фрагменты"]
    Q --> P
    P --> M["Модель"] --> A["Ответ с опорой\nна источники"]
    style Q fill:#2d2d2d,color:#fff
    style S fill:#1a5276,color:#fff
    style F fill:#7d6608,color:#fff
    style P fill:#1a5276,color:#fff
    style M fill:#1a5276,color:#fff
    style A fill:#1e8449,color:#fff
```

---

**Temperature / top_p** — параметры случайности выбора следующего токена: temperature масштабирует распределение, top_p отсекает хвост по суммарной вероятности. Глава 1, шаг 3 лабы.

```mermaid
flowchart LR
    D["Вероятности\nследующего токена"] --> T["temperature"]
    T -- ниже --> T0["Острее: почти всегда\nсамый вероятный токен"]
    T -- выше --> T1["Плоское: больше\nразнообразия и риска"]
    D --> P["top_p"]
    P --> P1["Отсечь хвост: оставить\nверхние токены с суммой\nвероятностей не меньше p"]
    T0 & T1 & P1 --> C["Выбор токена"]
    style D fill:#2d2d2d,color:#fff
    style T fill:#1a5276,color:#fff
    style P fill:#1a5276,color:#fff
    style T0 fill:#1e8449,color:#fff
    style T1 fill:#7d6608,color:#fff
    style P1 fill:#1a5276,color:#fff
    style C fill:#1e8449,color:#fff
```

---

**Токен (token)** — единица текста для модели, обычно фрагмент слова по алгоритму BPE; в токенах измеряются цена и контекст; русский текст занимает больше токенов, чем английский. Главы 1–3.

```mermaid
flowchart LR
    TXT["Текст"] -- BPE --> TK["Токены:\nфрагменты слов"]
    TK --> PRICE["Цена: за токены\nввода и вывода"]
    TK --> CTX["Контекстное окно:\nлимит в токенах"]
    RU["Русский текст"] -- больше токенов, чем английский --> TK
    style TXT fill:#2d2d2d,color:#fff
    style TK fill:#1a5276,color:#fff
    style PRICE fill:#7d6608,color:#fff
    style CTX fill:#7d6608,color:#fff
    style RU fill:#4a235a,color:#fff
```

---

**TTFT (time to first token)** — время от отправки запроса до первого токена ответа; ключевая метрика латентности для чата; скрывается streaming. Глава 2, шаг 5.

```mermaid
flowchart LR
    S["Отправка запроса"] -- ожидание TTFT --> F["Первый токен"]
    F -- генерация --> L["Последний токен"]
    F -. streaming показывает сразу .-> U["Пользователь видит\nначало ответа"]
    S -. без streaming .-> W["Пользователь ждёт\nвесь ответ до конца"]
    style S fill:#2d2d2d,color:#fff
    style F fill:#1e8449,color:#fff
    style L fill:#1a5276,color:#fff
    style U fill:#1e8449,color:#fff
    style W fill:#6e2f1a,color:#fff
```
