# Глоссарий дня 7

Термины по алфавиту, с английским оригиналом и указанием, где встречаются. К каждому термину — схема-подсказка в палитре курса: серый — вход, синий — процесс, зелёный — результат, коричневый — ошибка/опасность, жёлтый — данные/хранение, фиолетовый — внешнее.

---

**Follow-up** — вежливое напоминание работодателю через пять рабочих дней после отклика или интервью без ответа. Лаба, шаг 7.

```mermaid
flowchart LR
    A["Отклик отправлен"] --> WAIT["5 рабочих дней\nбез ответа"]
    WAIT --> FU["Вежливый follow-up:\n«уточняю статус»"]
    style A fill:#2d2d2d,color:#fff
    style WAIT fill:#7d6608,color:#fff
    style FU fill:#1e8449,color:#fff
```

---

**HR-скрининг (HR screening)** — первый звонок рекрутера: мотивация, зарплата, формат, адекватность; проверяется питч и диапазон. Глава 1.

```mermaid
flowchart LR
    APP["Отклик прошёл\nскрининг резюме"] --> HR["Звонок HR:\n15–20 минут"]
    HR --> M["Мотивация"]
    HR --> S["Зарплатная вилка"]
    HR --> F["Формат работы"]
    style APP fill:#2d2d2d,color:#fff
    style HR fill:#1a5276,color:#fff
    style M fill:#7d6608,color:#fff
    style S fill:#7d6608,color:#fff
    style F fill:#7d6608,color:#fff
```

---

**Live coding** — практическое задание в реальном времени, 30–60 минут; оценивают ход мысли и рабочий код, не идеальный. Глава 1.

```mermaid
flowchart LR
    TASK["Задача на 30–60 минут"] --> THINK["Ход мысли\nвслух"]
    THINK --> CODE["Рабочий код,\nне идеальный"]
    CODE --> EVAL["Оценивают процесс,\nне только результат"]
    style TASK fill:#2d2d2d,color:#fff
    style THINK fill:#1a5276,color:#fff
    style CODE fill:#1a5276,color:#fff
    style EVAL fill:#1e8449,color:#fff
```

---

**Mock-интервью (mock interview)** — тренировочное собеседование с оценкой ответов; в серии — 60 случайных вопросов из банка. Лаба, шаг 6.

```mermaid
flowchart LR
    BANK["Банк 132 вопросов"] --> PICK["60 случайных"]
    PICK --> ASK["Вопрос вслух →\nсвой ответ"]
    ASK --> SCORE["Оценка 0/1/2"]
    SCORE --> WEAK["Список слабых тем\nдля плана недель 2–4"]
    style BANK fill:#2d2d2d,color:#fff
    style PICK fill:#1a5276,color:#fff
    style ASK fill:#1a5276,color:#fff
    style SCORE fill:#7d6608,color:#fff
    style WEAK fill:#1e8449,color:#fff
```

---

**Оффер (offer)** — формальное предложение о работе: должность, деньги, дата, формат; просить письменно, сравнивать по нескольким критериям. Главы 1 и 4.

```mermaid
flowchart LR
    FINAL["Финальный этап\nпройден"] --> OFFER["Оффер: должность,\nсумма, дата, формат"]
    OFFER --> WRITTEN["Просить письменно"]
    WRITTEN --> CMP["Сравнить по критериям,\nне только по сумме"]
    style FINAL fill:#2d2d2d,color:#fff
    style OFFER fill:#1e8449,color:#fff
    style WRITTEN fill:#1a5276,color:#fff
    style CMP fill:#7d6608,color:#fff
```

---

**Питч (pitch)** — рассказ о себе на две минуты: кто, что в проде, чем отличаешься, что ищешь. Главы 1, 3, 4.

```mermaid
flowchart LR
    WHO["Кто я"] --> PITCH["Питч,\n2 минуты"]
    PROD["Что у меня в проде"] --> PITCH
    DIFF["Чем отличаюсь"] --> PITCH
    WANT["Что ищу"] --> PITCH
    style WHO fill:#2d2d2d,color:#fff
    style PROD fill:#2d2d2d,color:#fff
    style DIFF fill:#2d2d2d,color:#fff
    style WANT fill:#2d2d2d,color:#fff
    style PITCH fill:#1e8449,color:#fff
```

---

**Портфолио (portfolio)** — публичные артефакты, подтверждающие навыки: `ai-labs` с результатами, `CASE.md`, серия книг, Langfuse-демо. Главы 1–2.

```mermaid
flowchart LR
    SKILL["Заявленный навык\nв резюме"] --> PROOF{"Есть публичный\nартефакт?"}
    PROOF -- да --> LINK["ai-labs / CASE.md /\nсерия книг"]
    PROOF -- нет --> RISK["Слово без\nподтверждения"]
    style SKILL fill:#2d2d2d,color:#fff
    style PROOF fill:#7d6608,color:#fff
    style LINK fill:#1e8449,color:#fff
    style RISK fill:#6e2f1a,color:#fff
```

---

**Практическое (домашнее) задание (take-home assignment)** — задача на 4–8 часов; делается как лаба: README, тесты, Docker, измерения, ограничение по времени. Глава 1.

```mermaid
flowchart LR
    TASK["Задание на 4–8 часов"] --> LIMIT["Ограничение по времени —\nсоблюдать честно"]
    LIMIT --> DO["Делать как лабу:\nREADME, тесты, измерения"]
    DO --> SUBMIT["Сдать вовремя,\nдаже неидеально"]
    style TASK fill:#2d2d2d,color:#fff
    style LIMIT fill:#7d6608,color:#fff
    style DO fill:#1a5276,color:#fff
    style SUBMIT fill:#1e8449,color:#fff
```

---

**Скрининг резюме (resume screening)** — отбор рекрутером за секунды по ключевым словам, признакам прода и красным флагам. Глава 1.

```mermaid
flowchart LR
    CV["Резюме"] --> SCAN["Скан за секунды"]
    SCAN --> KW["Ключевые слова\nиз вакансии"]
    SCAN --> PROD["Признаки прода:\nчисла, ссылки"]
    SCAN --> RED["Красные флаги:\n«изучаю», без чисел"]
    style CV fill:#2d2d2d,color:#fff
    style SCAN fill:#7d6608,color:#fff
    style KW fill:#1e8449,color:#fff
    style PROD fill:#1e8449,color:#fff
    style RED fill:#6e2f1a,color:#fff
```

---

**Сопроводительное письмо (cover letter)** — три фразы: кто ты, что в проде с одной цифрой, ссылка на портфолио. Лаба, шаг 7.

```mermaid
flowchart LR
    F1["Фраза 1: кто ты"] --> LETTER["Сопроводительное\nписьмо"]
    F2["Фраза 2: что в проде,\nодна цифра"] --> LETTER
    F3["Фраза 3: ссылка\nна портфолио"] --> LETTER
    style F1 fill:#2d2d2d,color:#fff
    style F2 fill:#2d2d2d,color:#fff
    style F3 fill:#2d2d2d,color:#fff
    style LETTER fill:#1e8449,color:#fff
```

---

**STAR** — структура истории: Situation, Task, Action, Result, плюс изменение процесса; 60–90 секунд. Главы 1–3.

```mermaid
flowchart LR
    S["Situation:\nситуация"] --> T["Task:\nзадача"]
    T --> A["Action:\nдействия"]
    A --> R["Result:\nрезультат"]
    R --> CHG["Что изменилось\nв процессе"]
    style S fill:#2d2d2d,color:#fff
    style T fill:#1a5276,color:#fff
    style A fill:#1a5276,color:#fff
    style R fill:#1e8449,color:#fff
    style CHG fill:#7d6608,color:#fff
```

---

**System design interview** — разбор архитектуры системы по требованиям и ограничениям за 45 минут; оценивают способ мышления и trade-off. Главы 1–3.

```mermaid
flowchart TD
    REQ["Требования и\nограничения, 2 мин"] --> DATA["Данные и\nиндексация"]
    DATA --> SEARCH["Поиск"]
    SEARCH --> GEN["Генерация"]
    GEN --> STORE["Хранилище и\nmulti-tenancy"]
    STORE --> EVAL["Evals и\nнаблюдаемость"]
    style REQ fill:#2d2d2d,color:#fff
    style DATA fill:#1a5276,color:#fff
    style SEARCH fill:#1a5276,color:#fff
    style GEN fill:#1a5276,color:#fff
    style STORE fill:#1a5276,color:#fff
    style EVAL fill:#1e8449,color:#fff
```

---

**Вилка (salary range)** — диапазон зарплаты вакансии или ожиданий кандидата; называть диапазон, не число. Главы 1 и 3.

```mermaid
flowchart LR
    Q["«Какие ожидания\nпо зарплате?»"] --> BAD["Одно число:\nсужает переговоры"]
    Q --> GOOD["Диапазон:\nоставляет манёвр"]
    style Q fill:#2d2d2d,color:#fff
    style BAD fill:#6e2f1a,color:#fff
    style GOOD fill:#1e8449,color:#fff
```

---

**Воронка найма (hiring funnel)** — этапы от отклика до оффера с конверсией на каждом; из тридцати откликов — один-два финала. Глава 1.

```mermaid
flowchart TD
    A["30 откликов"] --> B["Ответы HR"]
    B --> C["Технические этапы"]
    C --> D["Финалы"]
    D --> E["1–2 оффера"]
    style A fill:#2d2d2d,color:#fff
    style B fill:#1a5276,color:#fff
    style C fill:#1a5276,color:#fff
    style D fill:#7d6608,color:#fff
    style E fill:#1e8449,color:#fff
```

---

**Кейс продукта (case study)** — структурированный рассказ о проекте: контекст, архитектура, решения с trade-off, инцидент, цифры, что дальше. Главы 1–2.

```mermaid
flowchart TD
    CTX["Контекст:\nдля кого и зачем"] --> ARCH["Архитектура"]
    ARCH --> DEC["Решения\nс trade-off"]
    DEC --> INC["Инцидент и фикс"]
    INC --> NUM["Цифры"]
    NUM --> NEXT["Что дальше"]
    style CTX fill:#2d2d2d,color:#fff
    style ARCH fill:#1a5276,color:#fff
    style DEC fill:#1a5276,color:#fff
    style INC fill:#6e2f1a,color:#fff
    style NUM fill:#7d6608,color:#fff
    style NEXT fill:#1e8449,color:#fff
```

---

**Красные флаги резюме (red flags)** — длинные списки технологий без глубины, «изучаю», отсутствие чисел и проектов, «промпт-инженер» как самоназвание. Глава 1.

```mermaid
flowchart LR
    CV["Резюме"] --> F1["Длинный список\nтехнологий без глубины"]
    CV --> F2["«Изучаю X»"]
    CV --> F3["Ни одного числа\nили проекта"]
    F1 --> FLAG["Красный флаг\nдля рекрутера"]
    F2 --> FLAG
    F3 --> FLAG
    style CV fill:#2d2d2d,color:#fff
    style F1 fill:#6e2f1a,color:#fff
    style F2 fill:#6e2f1a,color:#fff
    style F3 fill:#6e2f1a,color:#fff
    style FLAG fill:#7d6608,color:#fff
```
