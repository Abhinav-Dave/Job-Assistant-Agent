"""HTTP responses with PRD-shaped JSON bodies (not FastAPI `detail` wrapper)."""


class JsonHttpError(Exception):
    """Raised to return `content` as the response body with `status_code`."""

    def __init__(self, status_code: int, content: dict) -> None:
        self.status_code = status_code
        self.content = content
