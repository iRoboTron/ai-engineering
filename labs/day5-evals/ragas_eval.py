# ~/proj/ai-labs/day5-evals/ragas_eval.py
"""Считает три готовые метрики RAGAS по сохранённому прогону experiment.py и пишет их в Langfuse."""
import json
from pathlib import Path

import labkit
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langfuse import get_client
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, LLMContextPrecisionWithoutReference, LLMContextRecall, ResponseRelevancy

# --- НАСТРОЙКИ: сначала .local/run-dense-v1.json, потом .local/run-hybrid-v1.json ---
RUN_FILE = ".local/run-hybrid-v1.json"     # какой прогон experiment.py оценивать

BASE_URL = labkit.env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
JUDGE = labkit.env("JUDGE_MODEL", required=True)
KEY = labkit.env("OPENROUTER_API_KEY", required=True)
langfuse = get_client()

path = Path(__file__).resolve().parent / RUN_FILE
rows = json.loads(path.read_text(encoding="utf-8"))
if not rows:
    raise ValueError("Пустой прогон")
judge = LangchainLLMWrapper(ChatOpenAI(model=JUDGE, base_url=BASE_URL, api_key=KEY, temperature=0, timeout=120))
emb = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="openai/text-embedding-3-small", base_url=BASE_URL, api_key=KEY, check_embedding_ctx_length=False))

rows = [r for r in rows if not r.get("unanswerable")]
if not rows:
    raise ValueError("Нет answerable-примеров для RAGAS; отказы оцениваются отдельно")
samples = [{"user_input": r["question"], "response": r["answer"], "retrieved_contexts": r["contexts"], **({"reference": r["reference"]} if r.get("reference") else {})} for r in rows if not r.get("unanswerable")]
with_ref = [s for s in samples if "reference" in s]

result = evaluate(EvaluationDataset.from_list(samples), metrics=[Faithfulness(), ResponseRelevancy(), LLMContextPrecisionWithoutReference()], llm=judge, embeddings=emb)
df = result.to_pandas()
if with_ref:
    df_ref = evaluate(EvaluationDataset.from_list(with_ref), metrics=[LLMContextRecall()], llm=judge).to_pandas()
    df = df.merge(df_ref[["user_input", "context_recall"]], on="user_input", how="left")

skip = {"user_input", "response", "retrieved_contexts", "reference"}
metric_cols = [c for c in df.columns if c not in skip]
print(df[metric_cols].describe().loc[["mean", "min"]].round(3).to_markdown())

for r, (_, s) in zip(rows, df.iterrows()):
    for name in metric_cols:
        value = s[name]
        if value == value:  # не NaN
            langfuse.create_score(trace_id=r["trace_id"], name=name, value=float(value))
langfuse.flush()
print(f"оценки записаны в {len(rows)} трейсов")
