import httpx

from tools.scraper import scrape_form_fields, scrape_job_description


class _MockResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "https://example.com"),
                response=httpx.Response(self.status_code),
            )


def test_scrape_job_description_extracts_clean_text_and_limits(monkeypatch) -> None:
    long_text = "Data Scientist role. " * 400
    html = f"""
    <html>
      <body>
        <nav>ignore nav content</nav>
        <main>
          <h1>Role</h1>
          <p>{long_text}</p>
        </main>
        <footer>ignore footer content</footer>
        <script>console.log("ignore")</script>
      </body>
    </html>
    """

    def _mock_get(*args, **kwargs):  # noqa: ANN002, ANN003
        return _MockResponse(html)

    monkeypatch.setattr("tools.scraper.httpx.get", _mock_get)
    result = scrape_job_description("https://example.com/jobs/1")

    assert result
    assert "ignore nav content" not in result
    assert "ignore footer content" not in result
    assert "Data Scientist role." in result
    assert len(result) <= 4000


def test_scrape_job_description_handles_http_failure(monkeypatch) -> None:
    def _mock_get(*args, **kwargs):  # noqa: ANN002, ANN003
        raise httpx.RequestError("network down", request=httpx.Request("GET", "https://bad-url"))

    monkeypatch.setattr("tools.scraper.httpx.get", _mock_get)
    assert scrape_job_description("https://bad-url") == ""


def test_scrape_form_fields_normalizes_controls(monkeypatch) -> None:
    html = """
    <html>
      <body>
        <form>
          <label for="first_name">First Name</label>
          <input id="first_name" name="first_name" type="text" placeholder="First" />

          <label>Email <input name="email" type="email" /></label>

          <textarea id="cover_letter" placeholder="Tell us about yourself"></textarea>

          <select name="country"><option>USA</option></select>

          <input type="hidden" name="csrf" value="token" />
          <input placeholder="Portfolio URL" />
        </form>
      </body>
    </html>
    """

    def _mock_get(*args, **kwargs):  # noqa: ANN002, ANN003
        return _MockResponse(html)

    monkeypatch.setattr("tools.scraper.httpx.get", _mock_get)
    fields = scrape_form_fields("https://example.com/apply")

    assert len(fields) == 5
    assert fields[0].field_id == "first_name"
    assert fields[0].label == "First Name"
    assert fields[0].field_type == "text"

    assert fields[1].name == "email"
    assert fields[1].label == "Email"
    assert fields[1].field_type == "email"

    assert fields[2].field_type == "textarea"
    assert fields[3].field_type == "select"

    assert fields[4].field_id.startswith("generated_")
    assert fields[4].label == "Portfolio URL"
    assert fields[4].placeholder == "Portfolio URL"


def test_scrape_form_fields_returns_empty_on_failure(monkeypatch) -> None:
    def _mock_get(*args, **kwargs):  # noqa: ANN002, ANN003
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("tools.scraper.httpx.get", _mock_get)
    assert scrape_form_fields("https://timeout.example") == []
