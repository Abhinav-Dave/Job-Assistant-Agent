import pytest

from services import llm


def test_load_prompt_reads_known_prompt() -> None:
    prompt = llm.load_prompt("resume_score_v1.txt")
    assert isinstance(prompt, str)
    assert len(prompt) > 20


def test_load_prompt_rejects_path_traversal() -> None:
    with pytest.raises(llm.PromptLoadError):
        llm.load_prompt("../.env")


def test_parse_json_from_response_direct_json() -> None:
    raw = '{"status":"ok","score":74}'
    assert llm.parse_json_from_response(raw) == {"status": "ok", "score": 74}


def test_parse_json_from_response_code_fenced() -> None:
    raw = """```json
{"status":"ok","grade":"A"}
```"""
    assert llm.parse_json_from_response(raw) == {"status": "ok", "grade": "A"}


def test_parse_json_from_response_with_preamble() -> None:
    raw = 'Here is the result you requested: {"status":"ok","count":2} Thanks.'
    assert llm.parse_json_from_response(raw) == {"status": "ok", "count": 2}


def test_parse_json_from_response_raises_on_garbage() -> None:
    with pytest.raises(llm.JSONParseError):
        llm.parse_json_from_response("not json at all")


def test_call_gemini_raises_if_not_configured(monkeypatch) -> None:
    class _Settings:
        google_gemini_api_key = ""
        gemini_model = "gemini-2.5-flash"

    monkeypatch.setattr("services.llm.get_settings", lambda: _Settings())
    with pytest.raises(llm.LLMError) as exc:
        llm.call_gemini("hello", max_tokens=10)
    assert exc.value.code == "llm_not_configured"


def test_call_gemini_returns_text_from_mocked_client(monkeypatch) -> None:
    class _FakeResponse:
        text = '{"status":"ok"}'

    class _FakeModel:
        def generate_content(self, *_args, **_kwargs):
            return _FakeResponse()

    class _FakeLegacyGenAI:
        class GenerationConfig:
            def __init__(self, **_kwargs) -> None:
                pass

    def _fake_build_gemini_clients(api_key: str, model_name: str):
        assert api_key == "unit-test-key"
        assert model_name
        # Legacy branch shape: model, model_name, legacy_module (with GenerationConfig)
        return "google.generativeai", _FakeModel(), model_name, _FakeLegacyGenAI

    class _Settings:
        google_gemini_api_key = "unit-test-key"
        gemini_model = "gemini-2.5-flash"
        gemini_model_fallback = ""

    monkeypatch.setattr("services.llm.get_settings", lambda: _Settings())
    monkeypatch.setattr("services.llm._build_gemini_clients", _fake_build_gemini_clients)

    assert llm.call_gemini("return json", max_tokens=32) == '{"status":"ok"}'


def test_call_gemini_retries_on_overload_when_fallback_set(monkeypatch) -> None:
    calls: list[str] = []

    def _fake_once(*, api_key: str, model_name: str, **_kwargs) -> str:
        calls.append(model_name)
        if model_name == "gemini-2.5-flash":
            raise llm.LLMError("llm_unavailable", "503 UNAVAILABLE")
        return '{"retry":"ok"}'

    class _Settings:
        google_gemini_api_key = "unit-test-key"
        gemini_model = "gemini-2.5-flash"
        gemini_model_fallback = "gemini-2.5-flash-lite"

    monkeypatch.setattr("services.llm.get_settings", lambda: _Settings())
    monkeypatch.setattr("services.llm._call_gemini_once", _fake_once)

    assert llm.call_gemini("x", max_tokens=10) == '{"retry":"ok"}'
    assert calls == ["gemini-2.5-flash", "gemini-2.5-flash-lite"]


def test_call_gemini_retries_after_deprecated_gemini20_404(monkeypatch) -> None:
    """Legacy gemini-2.0-flash in env: chain auto-appends gemini-2.5-flash-lite; 404 no-longer-available is retryable."""
    calls: list[str] = []

    def _fake_once(*, model_name: str, **_kwargs) -> str:
        calls.append(model_name)
        if model_name == "gemini-2.5-flash":
            raise llm.LLMError("llm_unavailable", "503 UNAVAILABLE")
        if model_name == "gemini-2.0-flash":
            raise llm.LLMError(
                "llm_unavailable",
                "404 NOT_FOUND. This model is no longer available to new users.",
            )
        return '{"ok":true}'

    class _Settings:
        google_gemini_api_key = "unit-test-key"
        gemini_model = "gemini-2.5-flash"
        gemini_model_fallback = "gemini-2.0-flash"

    monkeypatch.setattr("services.llm.get_settings", lambda: _Settings())
    monkeypatch.setattr("services.llm._call_gemini_once", _fake_once)

    assert llm.call_gemini("x", max_tokens=10) == '{"ok":true}'
    assert calls == ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]


def test_call_gemini_does_not_retry_on_non_overload(monkeypatch) -> None:
    calls: list[str] = []

    def _fake_once(*, model_name: str, **_kwargs) -> str:
        calls.append(model_name)
        raise llm.LLMError("llm_unavailable", "PERMISSION_DENIED")

    class _Settings:
        google_gemini_api_key = "unit-test-key"
        gemini_model = "gemini-2.5-flash"
        gemini_model_fallback = "gemini-2.5-flash-lite"

    monkeypatch.setattr("services.llm.get_settings", lambda: _Settings())
    monkeypatch.setattr("services.llm._call_gemini_once", _fake_once)

    with pytest.raises(llm.LLMError):
        llm.call_gemini("x", max_tokens=10)
    assert calls == ["gemini-2.5-flash"]

