# ~/proj/ai-labs/day5-evals/safe_completion.py
from langfuse import get_client, observe


@observe(as_type="generation", name="provider.chat", capture_input=False, capture_output=False)
async def complete(client, base_url: str, api_key: str, model: str, messages: list[dict], max_tokens: int = 400) -> dict:
    response = await client.post(base_url.rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "max_tokens": max_tokens, "temperature": 0, "messages": messages}, timeout=60)
    # Текст upstream error может содержать запрос: не включаем его в exception/status_message.
    if response.status_code >= 400:
        raise RuntimeError(f"Provider HTTP {response.status_code}")
    data = response.json()
    usage = data.get("usage", {})
    details = {k: usage[source] for k, source in (("input", "prompt_tokens"), ("output", "completion_tokens"))
               if isinstance(usage.get(source), int) and usage[source] >= 0}
    get_client().update_current_generation(model=model, usage_details=details)
    return data
