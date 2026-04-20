from tools.pdf_parser import extract_text_from_pdf


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def get_text(self, *_args, **_kwargs) -> str:
        return self._text


class _FakeDocument:
    def __init__(self, page_texts: list[str]) -> None:
        self._pages = [_FakePage(text) for text in page_texts]

    def __enter__(self) -> "_FakeDocument":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False

    def __iter__(self):
        return iter(self._pages)


def test_extract_text_from_pdf_success(monkeypatch) -> None:
    def _mock_open(*_args, **_kwargs):  # noqa: ANN002, ANN003
        return _FakeDocument(["Jane Doe Resume", "Python | FastAPI | SQL"])

    monkeypatch.setattr("tools.pdf_parser.fitz.open", _mock_open)
    result = extract_text_from_pdf(b"%PDF-mock")

    assert result == "Jane Doe Resume\nPython | FastAPI | SQL"


def test_extract_text_from_pdf_scanned_pdf_returns_empty(monkeypatch) -> None:
    def _mock_open(*_args, **_kwargs):  # noqa: ANN002, ANN003
        return _FakeDocument(["", "   "])

    monkeypatch.setattr("tools.pdf_parser.fitz.open", _mock_open)
    assert extract_text_from_pdf(b"%PDF-scanned") == ""


def test_extract_text_from_pdf_handles_parser_error(monkeypatch) -> None:
    def _mock_open(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError("bad pdf")

    monkeypatch.setattr("tools.pdf_parser.fitz.open", _mock_open)
    assert extract_text_from_pdf(b"%PDF-bad") == ""


def test_extract_text_from_pdf_handles_empty_bytes() -> None:
    assert extract_text_from_pdf(b"") == ""
