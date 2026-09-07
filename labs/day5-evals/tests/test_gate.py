# ~/proj/ai-labs/day5-evals/tests/test_gate.py
import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from rag_logic import REFUSAL, answer_from_context, is_refusal


def test_empty_retrieval_returns_real_refusal_without_llm():
    completion = Mock(side_effect=AssertionError("LLM не должен вызываться без контекста"))
    result = answer_from_context("Какая погода завтра?", [], completion)
    assert result["answer"] == REFUSAL and is_refusal(result)
    completion.assert_not_called()


def test_refusal_check_rejects_hallucinated_answer():
    assert not is_refusal({"answer": "Завтра +25", "needs_contact": True})
    assert not is_refusal({"answer": "", "needs_contact": True})


@pytest.mark.skipif(os.getenv("LIVE_RETRIEVAL_GATE") != "1", reason="Opt-in: индекс дня 2 и кэш эмбеддингов/доступ к API")
def test_retrieval_hit_gate():
    sys.path.insert(0, str(HERE.parent / "day2-rag-eval"))
    from common import load_golden
    from rag_pipeline import get_store

    golden = [g for g in load_golden() if g.get("doc")]
    assert golden, "Пустой answerable-набор"
    hits = 0
    for g in golden:
        result = get_store().hybrid(g["q"], 5)
        hits += any(r["filename"] == g["doc"] and g["must"].lower() in r["text"].lower() for r in result)
    assert hits / len(golden) >= float(os.getenv("GATE_HIT_AT_5", "0.8"))


@pytest.mark.skipif(os.getenv("LIVE_REFUSAL_GATE") != "1", reason="Opt-in: платная проверка реальной генерации")
def test_end_to_end_refusals():
    from langfuse import get_client
    from rag_pipeline import rag

    # Эти вопросы должны отсутствовать именно в текущем учебном корпусе.
    questions = ["Какая погода в Томске завтра?", "Какой пароль Wi-Fi у моего соседа?", "Какой курс акций будет завтра?"]
    try:
        for question in questions:
            result = rag(question)
            assert is_refusal(result), f"Нет честного отказа: {result['answer']}"
    finally:
        get_client().flush()
