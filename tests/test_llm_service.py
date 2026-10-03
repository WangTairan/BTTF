from src.services.llm import _build_chat_body, supports_batch_api


def test_gpt6_sol_uses_batch_with_reasoning_disabled():
    provider, model_id, body = _build_chat_body(
        "gpt6-sol",
        [{"role": "user", "content": "score this code"}],
    )

    assert provider == "openai"
    assert model_id == "gpt-6-sol"
    assert supports_batch_api("gpt6-sol")
    assert body["reasoning_effort"] == "none"


def test_gpt61_sol_uses_low_reasoning_without_temperature():
    provider, model_id, body = _build_chat_body(
        "gpt61-sol",
        [{"role": "user", "content": "score this code"}],
    )

    assert provider == "openai"
    assert model_id == "gpt-6.1-sol"
    assert supports_batch_api("gpt61-sol")
    assert body["reasoning_effort"] == "low"
    assert body["max_completion_tokens"] == 2048
    assert "temperature" not in body
