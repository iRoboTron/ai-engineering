# ~/proj/ai-labs/day2-rag-eval/index.py
"""Строит один снимок индекса: режет документы на чанки, считает векторы, кладёт в Chroma и в chunks.jsonl.
Настройки — константы ниже, не аргументы командной строки: поменял значение, сохранил файл, нажал Run —
получил новый снимок под новым именем. Старые снимки не трогает и не перезаписывает."""
import json

import labkit                          # noqa: F401  подключает .env и пути labkit.FIXTURES/labkit.ROOT
from common import FIXTURES, dataset_hash, snapshot_path, tenant_map
from parse import parse

# --- НАСТРОЙКИ: поменяй и запусти снова, чтобы получить другой снимок для сравнения ---
CORPUS = FIXTURES / "corpus"           # папка с документами; по умолчанию — учебные fixture курса
COLLECTION = "chunks_openai"           # имя снимка: у каждого эксперимента своё, старое не стирается
EMBEDDER = "openrouter"                # "openrouter" — платный API, "local" — бесплатная модель на CPU
MODEL = "openai/text-embedding-3-small"    # модель эмбеддингов; для EMBEDDER="local" — например BAAI/bge-m3
CHUNK_SIZE = 500                       # символов в одном чанке
CHUNK_OVERLAP = 50                     # перекрытие между соседними чанками, чтобы не резать мысль пополам
TITLE_PREFIX = False                   # True — дописывать имя файла перед текстом каждого чанка (шаг 7)

SUPPORTED = {".md", ".txt", ".pdf", ".docx", ".html", ".htm"}


def main() -> None:
    dest = snapshot_path(COLLECTION)
    if dest.exists():
        raise SystemExit(f"снимок {COLLECTION} уже существует: смени COLLECTION вверху файла, перезаписи нет")
    if not CORPUS.is_dir():
        raise SystemExit("каталог корпуса не существует")
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    rows = []
    for path in sorted(CORPUS.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        filename = path.relative_to(CORPUS).as_posix()
        for i, chunk in enumerate(splitter.split_text(parse(path))):
            rows.append({"id": f"{filename}:{i}", "text": chunk, "filename": filename, "chunk_index": i})
    if not rows:
        raise SystemExit("не извлечено ни одного чанка")
    tenants = tenant_map(r["filename"] for r in rows)          # делит документы на двух учебных арендаторов (день 3)
    for row in rows:
        row["tenant_id"] = tenants[row["filename"]]
    from embed import Embedder
    to_embed = [f"{r['filename']}\n{r['text']}" if TITLE_PREFIX else r["text"] for r in rows]
    vectors = Embedder(EMBEDDER, MODEL).embed_documents(to_embed)
    if len(vectors) != len(rows):
        raise RuntimeError("число векторов не совпадает с числом чанков")
    config = {"collection": COLLECTION, "embedder": EMBEDDER, "model": MODEL,
              "dimension": len(vectors[0]), "chunk_size": CHUNK_SIZE,
              "chunk_overlap": CHUNK_OVERLAP, "title_prefix": TITLE_PREFIX,
              "dataset_hash": dataset_hash(rows), "documents": len(tenants)}
    dest.mkdir(parents=True, exist_ok=False)
    import chromadb
    client = chromadb.PersistentClient(path=str(dest / "chroma"))     # локальная векторная база, файлы на диске
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    for s in range(0, len(rows), 500):                         # пачками, чтобы не упереться в лимит одного add()
        batch = rows[s:s + 500]
        col.add(ids=[r["id"] for r in batch], documents=[r["text"] for r in batch],
                embeddings=vectors[s:s + 500],
                metadatas=[{k: v for k, v in r.items() if k not in {"id", "text"}} for r in batch])
    (dest / "chunks.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (dest / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"снимок {COLLECTION}: документов {len(tenants)}, чанков {col.count()}, dim={config['dimension']}")


if __name__ == "__main__":
    main()
