# ~/proj/ai-labs/day2-rag-eval/index.py
import argparse
import json
from pathlib import Path

from common import FIXTURES, dataset_hash, snapshot_path, tenant_map
from parse import parse

SUPPORTED = {".md", ".txt", ".pdf", ".docx", ".html", ".htm"}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=FIXTURES / "corpus")
    ap.add_argument("--collection", default="chunks_openai")
    ap.add_argument("--embedder", default="openrouter", choices=["openrouter", "local"])
    ap.add_argument("--model", default="openai/text-embedding-3-small")
    ap.add_argument("--chunk-size", type=int, default=500)
    ap.add_argument("--chunk-overlap", type=int, default=50)
    ap.add_argument("--title-prefix", action="store_true")
    a = ap.parse_args()
    dest = snapshot_path(a.collection)
    if dest.exists():
        raise SystemExit("снимок уже существует: выбери новое --collection, перезаписи нет")
    if not a.corpus.is_dir():
        raise SystemExit("каталог корпуса не существует")
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=a.chunk_size, chunk_overlap=a.chunk_overlap)
    rows = []
    for path in sorted(a.corpus.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        filename = path.relative_to(a.corpus).as_posix()
        for i, chunk in enumerate(splitter.split_text(parse(path))):
            rows.append({"id": f"{filename}:{i}", "text": chunk, "filename": filename, "chunk_index": i})
    if not rows:
        raise SystemExit("не извлечено ни одного чанка")
    tenants = tenant_map(r["filename"] for r in rows)
    for row in rows:
        row["tenant_id"] = tenants[row["filename"]]
    from embed import Embedder
    to_embed = [f"{r['filename']}\n{r['text']}" if a.title_prefix else r["text"] for r in rows]
    vectors = Embedder(a.embedder, a.model).embed_documents(to_embed)
    if len(vectors) != len(rows):
        raise RuntimeError("число векторов не совпадает с числом чанков")
    config = {"collection": a.collection, "embedder": a.embedder, "model": a.model,
              "dimension": len(vectors[0]), "chunk_size": a.chunk_size,
              "chunk_overlap": a.chunk_overlap, "title_prefix": a.title_prefix,
              "dataset_hash": dataset_hash(rows), "documents": len(tenants)}
    dest.mkdir(parents=True, exist_ok=False)
    import chromadb
    client = chromadb.PersistentClient(path=str(dest / "chroma"))
    col = client.create_collection(a.collection, metadata={"hnsw:space": "cosine"})
    for s in range(0, len(rows), 500):
        batch = rows[s:s + 500]
        col.add(ids=[r["id"] for r in batch], documents=[r["text"] for r in batch],
                embeddings=vectors[s:s + 500],
                metadatas=[{k: v for k, v in r.items() if k not in {"id", "text"}} for r in batch])
    (dest / "chunks.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (dest / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"снимок {a.collection}: документов {len(tenants)}, чанков {col.count()}, dim={config['dimension']}")

if __name__ == "__main__":
    main()
