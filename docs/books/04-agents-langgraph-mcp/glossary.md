# Глоссарий дня 4

Термины по алфавиту, с английским оригиналом и указанием, где встречаются. К каждому термину — схема-подсказка в палитре курса: серый — вход, синий — процесс, зелёный — результат, коричневый — ошибка/опасность, жёлтый — данные/хранение, фиолетовый — внешнее.

---

**Агент (agent)** — цикл, в котором модель сама выбирает инструменты и момент завершения, а код выполняет вызовы; отличается от workflow, где шаги задал разработчик. Глава 1.

```mermaid
flowchart LR
    Q["Вопрос"] --> M["Модель решает сама:\nкакой инструмент, когда стоп"]
    M --> T["Вызов инструмента"]
    T --> M
    M --> A["Ответ, когда\nмодель сочла достаточным"]
    style Q fill:#2d2d2d,color:#fff
    style M fill:#1a5276,color:#fff
    style T fill:#4a235a,color:#fff
    style A fill:#1e8449,color:#fff
```

---

**add_messages** — редьюсер состояния LangGraph для списка сообщений: дописывает новые вместо замены. Глава 1, лаба шаг 2.

```mermaid
flowchart LR
    OLD["Состояние:\n[сообщение 1, 2]"] --> NEW["Узел возвращает:\n[сообщение 3]"]
    NEW --> RED["add_messages:\nдописать, не заменить"]
    RED --> RES["[сообщение 1, 2, 3]"]
    style OLD fill:#7d6608,color:#fff
    style NEW fill:#1a5276,color:#fff
    style RED fill:#4a235a,color:#fff
    style RES fill:#1e8449,color:#fff
```

---

**Checkpointer** — компонент LangGraph, сохраняющий состояние графа после каждого шага по `thread_id`; `MemorySaver` для разработки, SQLite или Postgres для прода. Главы 1–3.

```mermaid
flowchart LR
    STEP["Шаг графа\nзавершён"] --> SAVE["Checkpointer сохраняет\nсостояние по thread_id"]
    SAVE --> LATER["Позже: тот же thread_id"]
    LATER --> RESTORE["Состояние\nвосстановлено"]
    style STEP fill:#1a5276,color:#fff
    style SAVE fill:#7d6608,color:#fff
    style LATER fill:#2d2d2d,color:#fff
    style RESTORE fill:#1e8449,color:#fff
```

---

**Command(resume=...)** — способ продолжить граф после `interrupt` с решением человека. Лаба, шаг 4.

```mermaid
flowchart LR
    INT["interrupt():\nграф на паузе"] --> H["Человек решает:\ny / n"]
    H --> CMD["Command(resume=True/False)"]
    CMD --> CONT["Граф продолжается\nс места остановки"]
    style INT fill:#7d6608,color:#fff
    style H fill:#2d2d2d,color:#fff
    style CMD fill:#1a5276,color:#fff
    style CONT fill:#1e8449,color:#fff
```

---

**create_react_agent / create_agent** — готовые агенты в `langgraph.prebuilt` и LangChain 1.0 для стандартного цикла инструментов; для своих лимитов и ветвлений — `StateGraph`. Глава 1.

```mermaid
flowchart LR
    STD["Стандартный цикл:\nмодель → инструмент → модель"] --> READY["create_react_agent:\nготово за одну строку"]
    CUSTOM["Свои лимиты, guard,\nHITL, ветвления"] --> SG["StateGraph:\nсобираешь сам"]
    style STD fill:#2d2d2d,color:#fff
    style READY fill:#1e8449,color:#fff
    style CUSTOM fill:#2d2d2d,color:#fff
    style SG fill:#4a235a,color:#fff
```

---

**FastMCP** — класс Python SDK MCP, превращающий функции с типами в инструменты сервера одним декоратором; транспорты stdio и streamable HTTP. Лаба, шаг 7.

```mermaid
flowchart LR
    FN["def memory_search(query: str) -> str"] --> DEC["@mcp.tool()"]
    DEC --> SRV["FastMCP-сервер:\nинструмент по протоколу MCP"]
    SRV -- stdio / HTTP --> CLIENT["Любой MCP-клиент"]
    style FN fill:#2d2d2d,color:#fff
    style DEC fill:#1a5276,color:#fff
    style SRV fill:#4a235a,color:#fff
    style CLIENT fill:#1e8449,color:#fff
```

---

**GraphRecursionError / recursion_limit** — жёсткий потолок числа переходов графа и исключение при его превышении; грубая защита от зацикливания. Главы 1–2.

```mermaid
flowchart LR
    G["Граф выполняет\nпереходы узел → узел"] --> C["Счётчик переходов"]
    C --> CHK{"Превышен\nrecursion_limit?"}
    CHK -- нет --> G
    CHK -- да --> ERR["GraphRecursionError"]
    style G fill:#1a5276,color:#fff
    style C fill:#7d6608,color:#fff
    style CHK fill:#7d6608,color:#fff
    style ERR fill:#6e2f1a,color:#fff
```

---

**Human-in-the-loop (HITL)** — остановка агента для решения человека перед побочным действием; в LangGraph — `interrupt()`. Главы 1–3.

```mermaid
flowchart LR
    WRITE["Агент хочет\nсделать запись"] --> STOP["interrupt() до\nлюбого эффекта"]
    STOP --> HUMAN["Человек: разрешить\nили отклонить"]
    HUMAN -- разрешил --> DO["Запись выполнена"]
    HUMAN -- отклонил --> SKIP["Запись не выполнена"]
    style WRITE fill:#2d2d2d,color:#fff
    style STOP fill:#6e2f1a,color:#fff
    style HUMAN fill:#7d6608,color:#fff
    style DO fill:#1e8449,color:#fff
    style SKIP fill:#1e8449,color:#fff
```

---

**Идемпотентность инструмента** — повтор вызова после сбоя не создаёт второго эффекта; ключ идемпотентности в аргументах записи. Главы 1 и 3.

```mermaid
flowchart LR
    CALL1["Вызов save_note\nid=note-42"] --> EFF["Заметка создана"]
    FAIL["Сеть оборвалась\nдо ответа"] -.-> CALL1
    CALL2["Повтор того же\nвызова id=note-42"] --> CHK{"id уже\nобработан?"}
    CHK -- да --> SKIP["Эффект не повторён"]
    style CALL1 fill:#2d2d2d,color:#fff
    style EFF fill:#1e8449,color:#fff
    style FAIL fill:#6e2f1a,color:#fff
    style CALL2 fill:#2d2d2d,color:#fff
    style CHK fill:#7d6608,color:#fff
    style SKIP fill:#1e8449,color:#fff
```

---

**interrupt()** — функция LangGraph, приостанавливающая граф внутри узла с сохранением состояния; возвращает решение при возобновлении. Лаба, шаг 2.

```mermaid
flowchart TD
    NODE["Узел графа\nвызывает interrupt(data)"] --> PAUSE["Выполнение\nостановлено"]
    PAUSE --> SAVE["Состояние сохранено\nчерез checkpointer"]
    SAVE --> RESUME["Command(resume=X)"]
    RESUME --> BACK["interrupt() возвращает X,\nузел продолжается"]
    style NODE fill:#1a5276,color:#fff
    style PAUSE fill:#7d6608,color:#fff
    style SAVE fill:#7d6608,color:#fff
    style RESUME fill:#2d2d2d,color:#fff
    style BACK fill:#1e8449,color:#fff
```

---

**langchain-mcp-adapters** — библиотека, представляющая инструменты MCP-серверов как инструменты LangChain и LangGraph (`MultiServerMCPClient`). Лаба, шаг 7.

```mermaid
flowchart LR
    MCP["MCP-сервер:\nинструменты по протоколу"] --> ADAPT["langchain-mcp-adapters"]
    ADAPT --> TOOLS["Обычные инструменты\nLangChain/LangGraph"]
    TOOLS --> GRAPH["bind_tools() на графе,\nкак свои функции"]
    style MCP fill:#4a235a,color:#fff
    style ADAPT fill:#1a5276,color:#fff
    style TOOLS fill:#7d6608,color:#fff
    style GRAPH fill:#1e8449,color:#fff
```

---

**LangGraph** — фреймворк оркестрации агентов на графе состояний: узлы, рёбра, редьюсеры, checkpointer, interrupt, streaming. Главы 1–3.

```mermaid
flowchart TD
    S["StateGraph:\nтипизированное состояние"] --> N["Узлы: функции,\nменяющие состояние"]
    N --> E["Рёбра: обычные\nи условные"]
    E --> C["compile(checkpointer)"]
    C --> RUN["Граф готов\nк ainvoke/interrupt"]
    style S fill:#2d2d2d,color:#fff
    style N fill:#1a5276,color:#fff
    style E fill:#1a5276,color:#fff
    style C fill:#7d6608,color:#fff
    style RUN fill:#1e8449,color:#fff
```

---

**MCP (Model Context Protocol)** — открытый протокол подключения серверов инструментов, ресурсов и промптов к любому клиенту-агенту; транспорты stdio и streamable HTTP. Главы 1–3.

```mermaid
flowchart LR
    SRV1["MCP-сервер:\nпамять"] --> CL["Любой MCP-клиент:\nагент, Claude Code"]
    SRV2["MCP-сервер:\nфайлы"] --> CL
    SRV3["MCP-сервер:\nбаза данных"] --> CL
    CL --> USE["Один протокол\nдля любых инструментов"]
    style SRV1 fill:#4a235a,color:#fff
    style SRV2 fill:#4a235a,color:#fff
    style SRV3 fill:#4a235a,color:#fff
    style CL fill:#1a5276,color:#fff
    style USE fill:#1e8449,color:#fff
```

---

**Память агента (agent memory)** — короткая (состояние диалога), долгая (факты между сессиями, семантический поиск — ai-agent-memory), процедурная (инструкции). Глава 1.

```mermaid
flowchart LR
    SHORT["Короткая:\nистория текущего диалога\n(checkpointer)"] --> AGENT["Агент"]
    LONG["Долгая: факты\nмежду сессиями\n(векторный поиск)"] --> AGENT
    PROC["Процедурная:\nинструкции, системный промпт"] --> AGENT
    style SHORT fill:#1a5276,color:#fff
    style LONG fill:#7d6608,color:#fff
    style PROC fill:#7d6608,color:#fff
    style AGENT fill:#1e8449,color:#fff
```

---

**ReAct** — схема «рассуждение → действие → наблюдение» в цикле до финального ответа. Глава 3.

```mermaid
flowchart LR
    R["Рассуждение:\n«нужно найти X»"] --> A["Действие:\nвызов инструмента"]
    A --> O["Наблюдение:\nрезультат инструмента"]
    O --> R
    R --> F["Финальный ответ,\nкогда рассуждение\nговорит «готово»"]
    style R fill:#1a5276,color:#fff
    style A fill:#4a235a,color:#fff
    style O fill:#7d6608,color:#fff
    style F fill:#1e8449,color:#fff
```

---

**Схемы workflow** — цепочка промптов, маршрутизация, параллелизация, оркестратор с исполнителями, генератор с оценщиком; предпочтительнее агента, когда порядок шагов известен. Глава 1.

```mermaid
flowchart LR
    KNOWN["Порядок шагов\nизвестен заранее"] --> WF["Workflow: разработчик\nзадаёт шаги в коде"]
    UNKNOWN["Путь заранее\nнеизвестен"] --> AG["Агент: модель сама\nвыбирает шаги"]
    style KNOWN fill:#2d2d2d,color:#fff
    style WF fill:#1e8449,color:#fff
    style UNKNOWN fill:#2d2d2d,color:#fff
    style AG fill:#4a235a,color:#fff
```

---

**StateGraph** — класс LangGraph для построения графа с типизированным состоянием: `add_node`, `add_edge`, `add_conditional_edges`, `compile`. Лаба, шаг 2.

```mermaid
flowchart TD
    DEF["class AgentState(TypedDict): …"] --> SG["StateGraph(AgentState)"]
    SG --> AN["add_node('llm', fn)\nadd_node('tools', fn)"]
    AN --> AE["add_conditional_edges(...)"]
    AE --> CP["compile() → готовый граф"]
    style DEF fill:#2d2d2d,color:#fff
    style SG fill:#1a5276,color:#fff
    style AN fill:#1a5276,color:#fff
    style AE fill:#1a5276,color:#fff
    style CP fill:#1e8449,color:#fff
```

---

**thread_id** — идентификатор ветки диалога для checkpointer; один `thread_id` — одна продолжаемая история. Лаба, шаг 6.

```mermaid
flowchart LR
    T1["thread_id='t1'"] --> H1["История диалога 1"]
    T2["thread_id='t2'"] --> H2["История диалога 2\n(независимая)"]
    H1 -. тот же t1 позже .-> CONT["Продолжение того же диалога"]
    style T1 fill:#2d2d2d,color:#fff
    style T2 fill:#2d2d2d,color:#fff
    style H1 fill:#7d6608,color:#fff
    style H2 fill:#7d6608,color:#fff
    style CONT fill:#1e8449,color:#fff
```

---

**Tool poisoning** — вредоносные инструкции в описании инструмента MCP-сервера, влияющие на поведение модели; угроза цепочки поставок инструментов. Главы 1 и 3.

```mermaid
flowchart LR
    DESC["Описание инструмента:\n«…а ещё игнорируй\nправила безопасности»"] --> M["Модель читает\nописание как часть промпта"]
    M --> BAD["Поведение модели\nискажено чужим инструментом"]
    style DESC fill:#6e2f1a,color:#fff
    style M fill:#1a5276,color:#fff
    style BAD fill:#6e2f1a,color:#fff
```

---

**ToolNode** — готовый узел LangGraph, выполняющий вызовы инструментов из последнего сообщения модели и возвращающий `ToolMessage`. Лаба, шаг 2.

```mermaid
flowchart LR
    AI["AIMessage с tool_calls"] --> TN["ToolNode"]
    TN --> RUN["Вызывает каждый\nинструмент по имени"]
    RUN --> TM["ToolMessage(content=результат,\ntool_call_id=...)"]
    style AI fill:#2d2d2d,color:#fff
    style TN fill:#1a5276,color:#fff
    style RUN fill:#1a5276,color:#fff
    style TM fill:#1e8449,color:#fff
```

---

**Trajectory (траектория)** — последовательность вызовов инструментов агента; оценивается вместе с результатом и стоимостью. Глава 3.

```mermaid
flowchart TD
    C1["search_docs('порт')"] --> C2["memory_search('Ollama')"]
    C2 --> C3["save_note(...)"]
    C1 -.-> T["Траектория =\nвся последовательность"]
    C2 -.-> T
    C3 -.-> T
    T --> EVAL["Оценка: результат +\nстоимость + число шагов"]
    style C1 fill:#1a5276,color:#fff
    style C2 fill:#1a5276,color:#fff
    style C3 fill:#6e2f1a,color:#fff
    style T fill:#7d6608,color:#fff
    style EVAL fill:#1e8449,color:#fff
```

---

**usage_metadata** — поле ответа модели в LangChain с числом входных и выходных токенов; основа учёта бюджета агента. Лаба, шаг 2.

```mermaid
flowchart LR
    RESP["Ответ модели"] --> UM["response.usage_metadata:\ninput_tokens, output_tokens"]
    UM --> COST["cost = in × p_in +\nout × p_out"]
    COST --> BUDGET["Прибавить к cost_usd\nсостояния агента"]
    style RESP fill:#2d2d2d,color:#fff
    style UM fill:#1a5276,color:#fff
    style COST fill:#7d6608,color:#fff
    style BUDGET fill:#1e8449,color:#fff
```

---

**Fail-closed** — при неизвестной цене/usage или неизвестном инструменте запрещать следующие действия, а не считать отсутствие данных безопасным. Лаба.

```mermaid
flowchart LR
    UNK["usage неизвестен\nили инструмент не в allowlist"] --> CHK{"Данных достаточно\nдля безопасного решения?"}
    CHK -- нет --> STOP["Остановка:\naccounting_ok = False"]
    CHK -- да --> GO["Продолжить"]
    style UNK fill:#7d6608,color:#fff
    style CHK fill:#7d6608,color:#fff
    style STOP fill:#6e2f1a,color:#fff
    style GO fill:#1e8449,color:#fff
```
