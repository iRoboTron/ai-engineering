# Глоссарий дня 5

Термины по алфавиту, с английским оригиналом и указанием, где встречаются. К каждому термину — схема-подсказка в палитре курса: серый — вход, синий — процесс, зелёный — результат, коричневый — ошибка/опасность, жёлтый — данные/хранение, фиолетовый — внешнее/сравнение.

---

**Answer correctness** — метрика совпадения ответа с эталоном по фактам и смыслу; требует reference. Глава 1.

```mermaid
flowchart LR
    A["Ответ модели"] --> CMP["Сравнение по фактам"]
    R["Эталон (reference)"] --> CMP
    CMP --> SC["Оценка совпадения"]
    style A fill:#2d2d2d,color:#fff
    style R fill:#7d6608,color:#fff
    style CMP fill:#4a235a,color:#fff
    style SC fill:#1e8449,color:#fff
```

---

**Calibration (калибровка судьи)** — измерение согласия оценок модели-судьи с ручной разметкой до масштабирования; порог доверия около 80 %. Глава 1, лаба шаг 5.

```mermaid
flowchart LR
    H["Человек размечает\n5 ответов вручную"] --> J["Судья оценивает\nте же 5 ответов"]
    H --> CMP["Сравнение оценок"]
    J --> CMP
    CMP --> AGREE["Согласие ≥ 80% →\nможно доверять судье\nна остальном наборе"]
    style H fill:#2d2d2d,color:#fff
    style J fill:#4a235a,color:#fff
    style CMP fill:#1a5276,color:#fff
    style AGREE fill:#1e8449,color:#fff
```

---

**Context precision / context recall** — метрики RAGAS: релевантные фрагменты стоят выше нерелевантных; контекст покрывает утверждения эталона. Глава 1.

```mermaid
flowchart LR
    CTX["Найденные фрагменты"] --> PREC["Precision: релевантные\nвыше в списке?"]
    CTX --> REC["Recall: все факты\nэталона покрыты?"]
    style CTX fill:#2d2d2d,color:#fff
    style PREC fill:#1a5276,color:#fff
    style REC fill:#1a5276,color:#fff
```

---

**Dataset / experiment run** — golden-набор внутри платформы трейсинга и прогон системы по нему; прогоны сравниваются между версиями. Лаба, шаг 3.

```mermaid
flowchart LR
    G["golden.jsonl"] --> DS["Dataset в Langfuse:\ngolden-rag-<hash>"]
    DS --> R1["Run: dense-v1"]
    DS --> R2["Run: hybrid-v1"]
    R1 --> CMP["Сравнение прогонов\nв UI"]
    R2 --> CMP
    style G fill:#2d2d2d,color:#fff
    style DS fill:#7d6608,color:#fff
    style R1 fill:#1a5276,color:#fff
    style R2 fill:#1a5276,color:#fff
    style CMP fill:#1e8449,color:#fff
```

---

**Drift (дрейф качества)** — деградация без изменения кода: обновление модели провайдером, новые типы вопросов, устаревший индекс; ловится трендами. Главы 1 и 3.

```mermaid
flowchart LR
    T1["Неделя 1: answered=90%"] --> T2["Неделя 2: answered=88%"]
    T2 --> T3["Неделя 3: answered=79%"]
    T3 --> ALERT["Тренд вниз без\nизменений в коде →\nдрейф, не баг"]
    style T1 fill:#1e8449,color:#fff
    style T2 fill:#7d6608,color:#fff
    style T3 fill:#6e2f1a,color:#fff
    style ALERT fill:#1a5276,color:#fff
```

---

**Evals** — систематическая оценка LLM-системы на наборе примеров с известным ожиданием; офлайн и онлайн, детерминированные и модельные. Главы 1–3.

```mermaid
flowchart TD
    E["Evals"] --> OFF["Офлайн: перед релизом,\nна golden-наборе"]
    E --> ON["Онлайн: на проде,\nвыборка трафика"]
    E --> DET["Детерминированные:\ncode-checks, без LLM"]
    E --> MOD["Модельные:\nLLM-судья, RAGAS"]
    style E fill:#2d2d2d,color:#fff
    style OFF fill:#1a5276,color:#fff
    style ON fill:#1a5276,color:#fff
    style DET fill:#1e8449,color:#fff
    style MOD fill:#4a235a,color:#fff
```

---

**Faithfulness** — доля утверждений ответа, подтверждённых контекстом; главная метрика против выдумок в RAG. Главы 1–2.

```mermaid
flowchart LR
    A["Ответ: 4 утверждения"] --> CHK["Каждое сверяется\nс контекстом"]
    CTX["Контекст (найденные\nфрагменты)"] --> CHK
    CHK --> R["3 из 4 подтверждены →\nfaithfulness = 0.75"]
    style A fill:#2d2d2d,color:#fff
    style CTX fill:#7d6608,color:#fff
    style CHK fill:#1a5276,color:#fff
    style R fill:#1e8449,color:#fff
```

---

**Gate (регрессионный гейт)** — автоматическая проверка в CI, блокирующая изменение при падении метрики ниже порога; детерминированная на PR, модельная на релиз. Лаба, шаг 6.

```mermaid
flowchart LR
    PR["Pull request"] --> TEST["Offline-тесты:\nбез LLM, быстро"]
    TEST -- PASS --> MERGE["Слияние разрешено"]
    TEST -- FAIL --> BLOCK["Слияние заблокировано"]
    REL["Перед релизом"] --> LIVE["Live-гейт:\nс реальной моделью"]
    style PR fill:#2d2d2d,color:#fff
    style TEST fill:#1a5276,color:#fff
    style MERGE fill:#1e8449,color:#fff
    style BLOCK fill:#6e2f1a,color:#fff
    style REL fill:#2d2d2d,color:#fff
    style LIVE fill:#4a235a,color:#fff
```

---

**Generation** — наблюдение в трейсе, соответствующее вызову модели: промпт, ответ, модель, токены, стоимость, TTFT. Глава 1.

```mermaid
flowchart LR
    CALL["Вызов модели"] --> GEN["Generation-span\nв трейсе"]
    GEN --> FIELDS["модель, токены,\nстоимость, TTFT"]
    style CALL fill:#1a5276,color:#fff
    style GEN fill:#7d6608,color:#fff
    style FIELDS fill:#1e8449,color:#fff
```

---

**Golden-набор с эталонами** — вопросы с указанием источника и эталонным ответом человека; версионируется в git, меняется осознанно. Глава 1.

```mermaid
flowchart LR
    Q["Вопрос"] --> DOC["doc: где ответ"]
    Q --> MUST["must: обязательная фраза"]
    Q --> REF["reference: эталонный\nответ человека"]
    REF --> GIT["Версионируется в git"]
    style Q fill:#2d2d2d,color:#fff
    style DOC fill:#7d6608,color:#fff
    style MUST fill:#7d6608,color:#fff
    style REF fill:#7d6608,color:#fff
    style GIT fill:#1e8449,color:#fff
```

---

**Implicit feedback (неявный сигнал)** — событие в проде, косвенно отражающее качество: честный отказ, передача оператору, повтор вопроса, оставленный контакт. Главы 1 и 3.

```mermaid
flowchart LR
    U["Пользователь в чате"] --> S1["Повторил вопрос\nдругими словами"]
    U --> S2["Попросил оператора"]
    U --> S3["Оставил контакт\nпосле отказа"]
    S1 --> SIG["Косвенный сигнал\nо качестве ответа"]
    S2 --> SIG
    S3 --> SIG
    style U fill:#2d2d2d,color:#fff
    style S1 fill:#7d6608,color:#fff
    style S2 fill:#7d6608,color:#fff
    style S3 fill:#7d6608,color:#fff
    style SIG fill:#1e8449,color:#fff
```

---

**Langfuse** — open source платформа наблюдаемости LLM: трейсы, генерации, оценки, датасеты, версии промптов; self-hosted через Docker Compose. Главы 1–2.

```mermaid
flowchart LR
    APP["Твоё приложение"] --> SDK["Langfuse SDK\n(@observe)"]
    SDK --> LF["Langfuse:\nтрейсы, оценки, датасеты"]
    LF --> UI["UI: сравнение\nпрогонов, тренды"]
    style APP fill:#2d2d2d,color:#fff
    style SDK fill:#1a5276,color:#fff
    style LF fill:#7d6608,color:#fff
    style UI fill:#1e8449,color:#fff
```

---

**LLM-as-judge** — использование модели для оценки ответов по рубрике; требует structured output, temperature 0, калибровки и знания смещений. Главы 1–3.

```mermaid
flowchart LR
    Q["Вопрос + ответ + эталон"] --> RUB["Рубрика: правила\nоценки 0/1/2"]
    RUB --> J["Судья: structured output,\ntemperature=0"]
    J --> V["Оценка + обоснование\nв одно предложение"]
    V -. проверить .-> CAL["Калибровка на\nручной разметке"]
    style Q fill:#2d2d2d,color:#fff
    style RUB fill:#7d6608,color:#fff
    style J fill:#4a235a,color:#fff
    style V fill:#1e8449,color:#fff
    style CAL fill:#1a5276,color:#fff
```

---

**Masking (маскирование PII)** — удаление или замена персональных данных в промптах и ответах до отправки в трейсы. Лаба, шаг 7.

```mermaid
flowchart LR
    RAW["«Мой телефон\n+7 900 123-45-67»"] --> MASK["Маскирование\nдо отправки в трейс"]
    MASK --> SAFE["«Мой телефон [PHONE]»"]
    SAFE --> LF["Уходит в Langfuse"]
    style RAW fill:#6e2f1a,color:#fff
    style MASK fill:#1a5276,color:#fff
    style SAFE fill:#1e8449,color:#fff
    style LF fill:#7d6608,color:#fff
```

---

**Observability (наблюдаемость)** — способность понять поведение системы по трейсам, метрикам и логам; для LLM — с содержимым промптов, токенами и стоимостью. Глава 1.

```mermaid
flowchart LR
    SYS["Система в проде"] --> TR["Трейсы: что\nпроизошло, шаг за шагом"]
    SYS --> MET["Метрики: сколько,\nкак быстро, почём"]
    TR --> UNDERSTAND["Понимание поведения\nбез повторного дебага вслепую"]
    MET --> UNDERSTAND
    style SYS fill:#2d2d2d,color:#fff
    style TR fill:#1a5276,color:#fff
    style MET fill:#1a5276,color:#fff
    style UNDERSTAND fill:#1e8449,color:#fff
```

---

**Position bias / verbosity bias** — смещения судьи: предпочтение первого варианта в паре и более длинного ответа. Глава 1.

```mermaid
flowchart LR
    A["Ответ A: короткий,\nвторой по порядку"] --> J["Судья"]
    B["Ответ B: длинный,\nпервый по порядку"] --> J
    J --> BIAS["Смещение: выбирает B\nне за качество, а за\nпорядок и длину"]
    style A fill:#2d2d2d,color:#fff
    style B fill:#2d2d2d,color:#fff
    style J fill:#4a235a,color:#fff
    style BIAS fill:#6e2f1a,color:#fff
```

---

**RAGAS** — библиотека метрик оценки RAG с моделью-судьёй; результаты сравнимы только внутри одной системы и судьи. Главы 1–2.

```mermaid
flowchart LR
    RUN["Прогон: вопрос,\nответ, контексты"] --> RAGAS["RAGAS + судья"]
    RAGAS --> M1["faithfulness"]
    RAGAS --> M2["answer_relevancy"]
    RAGAS --> M3["context_precision"]
    M1 -. сравнение только .-> SAME["с другим прогоном\nтой же системы"]
    style RUN fill:#2d2d2d,color:#fff
    style RAGAS fill:#4a235a,color:#fff
    style M1 fill:#1a5276,color:#fff
    style M2 fill:#1a5276,color:#fff
    style M3 fill:#1a5276,color:#fff
    style SAME fill:#7d6608,color:#fff
```

---

**Response relevancy (answer relevancy)** — метрика соответствия ответа вопросу через эмбеддинги сгенерированных вопросов; занижает честный отказ. Глава 1.

```mermaid
flowchart LR
    A["Ответ"] --> GQ["Модель генерирует\nвопросы к этому ответу"]
    GQ --> E["Эмбеддинги вопросов\nvs исходный вопрос"]
    E --> SC["Похожи → высокая\nrelevancy"]
    A -. честный отказ .-> LOW["Мало конкретики →\nrelevancy занижена"]
    style A fill:#2d2d2d,color:#fff
    style GQ fill:#1a5276,color:#fff
    style E fill:#1a5276,color:#fff
    style SC fill:#1e8449,color:#fff
    style LOW fill:#7d6608,color:#fff
```

---

**Score** — оценка, привязанная к трейсу: от пользователя, судьи или детерминированной проверки. Лаба, шаги 3–5.

```mermaid
flowchart LR
    TRACE["Трейс запроса"] --> S1["Score: retrieval_hit\n(код)"]
    TRACE --> S2["Score: faithfulness\n(RAGAS)"]
    TRACE --> S3["Score: correctness_judge\n(свой судья)"]
    style TRACE fill:#2d2d2d,color:#fff
    style S1 fill:#1e8449,color:#fff
    style S2 fill:#4a235a,color:#fff
    style S3 fill:#4a235a,color:#fff
```

---

**Span** — шаг внутри трейса с длительностью и входом-выходом: поиск, реранкинг, инструмент. Глава 1.

```mermaid
flowchart LR
    TRACE["Трейс: rag()"] --> SP1["Span: retrieve()"]
    TRACE --> SP2["Span: generate()"]
    SP1 --> DUR1["Длительность,\nвход-выход"]
    SP2 --> DUR2["Длительность,\nвход-выход"]
    style TRACE fill:#2d2d2d,color:#fff
    style SP1 fill:#1a5276,color:#fff
    style SP2 fill:#1a5276,color:#fff
    style DUR1 fill:#1e8449,color:#fff
    style DUR2 fill:#1e8449,color:#fff
```

---

**Trace** — один запрос пользователя целиком с метаданными: сессия, tenant, версия промпта, теги. Глава 1.

```mermaid
flowchart LR
    REQ["Запрос пользователя"] --> TR["Trace"]
    TR --> META["session, tenant,\nversion, tags"]
    TR --> SPANS["Вложенные spans:\nretrieve, generate"]
    style REQ fill:#2d2d2d,color:#fff
    style TR fill:#7d6608,color:#fff
    style META fill:#1a5276,color:#fff
    style SPANS fill:#1a5276,color:#fff
```

---

**Allowlist telemetry** — экспорт только явно разрешённых метрик/технических идентификаторов; отключение автоматического захвата аргументов, результатов и секретов. Лаба, шаг 7.

```mermaid
flowchart LR
    ALL["Всё, что можно\nзалогировать"] --> LIST["Allowlist: только\nmodel, tokens, id"]
    LIST --> SEND["Уходит в трейс"]
    ALL -. текст, ключи, PII .-> BLOCK["Не в allowlist →\nне уходит"]
    style ALL fill:#2d2d2d,color:#fff
    style LIST fill:#7d6608,color:#fff
    style SEND fill:#1e8449,color:#fff
    style BLOCK fill:#6e2f1a,color:#fff
```

---

**Ошибка проверки (ERROR)** — сценарий нельзя оценить из-за API/формата/данных; не равен провалу поведения (FAIL), пропуску (SKIPPED) или успеху (PASS). Главы 1–2.

```mermaid
flowchart LR
    T["Проверка"] --> PASS["PASS: поведение верное"]
    T --> FAIL["FAIL: поведение неверное"]
    T --> SKIP["SKIPPED: осознанно\nне запускалась"]
    T --> ERR["ERROR: нельзя оценить\n(сбой API/данных)"]
    style T fill:#2d2d2d,color:#fff
    style PASS fill:#1e8449,color:#fff
    style FAIL fill:#6e2f1a,color:#fff
    style SKIP fill:#7d6608,color:#fff
    style ERR fill:#4a235a,color:#fff
```
