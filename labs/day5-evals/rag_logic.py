# ~/proj/ai-labs/day5-evals/rag_logic.py
REFUSAL = "В документах нет ответа на этот вопрос"


def is_refusal(result: dict) -> bool:
    return result.get("needs_contact") is True and result.get("answer", "").strip().rstrip(".") == REFUSAL


def answer_from_context(question: str, chunks: list[dict], complete) -> dict:
    # Детерминированная ветка при пустом retrieval; отсутствие ответа в непустом top-k
    # всё ещё проверяется end-to-end negative-примерами, а не поиском пары слов в чанках.
    answer = complete(question, chunks) if chunks else REFUSAL
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Пустой/невалидный ответ — ERROR")
    refusal = answer.strip().rstrip(".") == REFUSAL
    return {"answer": answer, "needs_contact": refusal,
            "contexts": [c["text"] for c in chunks],
            "sources": [f"{c['filename']}#{c['chunk_index']}" for c in chunks],
            "filenames": [c["filename"] for c in chunks]}
