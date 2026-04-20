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

    class _FakeGenAI:
        class GenerationConfig:
            def __init__(self, **_kwargs) -> None:
                pass

    def _fake_build_gemini_model(api_key: str, model_name: str):
        assert api_key == "unit-test-key"
        assert model_name
        return _FakeGenAI(), _FakeModel()

    class _Settings:
        google_gemini_api_key = "unit-test-key"
        gemini_model = "gemini-2.5-flash"

    monkeypatch.setattr("services.llm.get_settings", lambda: _Settings())
    monkeypatch.setattr("services.llm._build_gemini_model", _fake_build_gemini_model)

    assert llm.call_gemini("return json", max_tokens=32) == '{"status":"ok"}'

