"""Scraping helpers for job descriptions and application forms."""

from __future__ import annotations

from typing import Iterable
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from schemas.autofill import FormField

_REQUEST_TIMEOUT_SECONDS = 10.0
_MAX_JD_CHARS = 4000
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 JobAssistantBot/1.0"
)


def _get_html(url: str) -> str:
    if not url or not url.strip():
        return ""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    try:
        response = httpx.get(
            parsed.geturl(),
            timeout=_REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text or ""
    except (httpx.HTTPError, ValueError):
        return ""


def _clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def scrape_job_description(url: str) -> str:
    """Fetch and extract visible job description text from a URL.

    Returns a cleaned text block up to 4000 characters.
    Returns an empty string if fetch/parsing fails or text is unavailable.
    """

    html = _get_html(url)
    if not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag_name in ("script", "style", "noscript", "nav", "footer"):
            for node in soup.find_all(tag_name):
                node.decompose()

        root = soup.find("main") or soup.find("article") or soup.find("body") or soup
        text = _clean_text(root.get_text(separator=" ", strip=True))
        return text[:_MAX_JD_CHARS]
    except Exception:
        return ""


def _extract_label(control, soup: BeautifulSoup) -> str | None:
    control_id = (control.get("id") or "").strip()
    if control_id:
        linked_label = soup.find("label", attrs={"for": control_id})
        if linked_label:
            label_text = _clean_text(linked_label.get_text(" ", strip=True))
            if label_text:
                return label_text

    parent_label = control.find_parent("label")
    if parent_label:
        label_text = _clean_text(parent_label.get_text(" ", strip=True))
        if label_text:
            return label_text

    aria_label = _clean_text(control.get("aria-label", ""))
    if aria_label:
        return aria_label

    return None


def _iter_form_controls(soup: BeautifulSoup) -> Iterable:
    for control in soup.select("input, textarea, select"):
        input_type = (control.get("type") or "").lower()
        if control.name == "input" and input_type in {"hidden", "submit", "button", "image", "reset"}:
            continue
        yield control


def scrape_form_fields(url: str) -> list[FormField]:
    """Extract normalized form fields from a page.

    Returns an empty list when no parseable fields are available or request fails.
    """

    html = _get_html(url)
    if not html:
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
        fields: list[FormField] = []

        for index, control in enumerate(_iter_form_controls(soup), start=1):
            field_id = _clean_text(control.get("id", ""))
            name = _clean_text(control.get("name", "")) or None
            placeholder = _clean_text(control.get("placeholder", "")) or None
            label = _extract_label(control, soup) or placeholder or name or field_id or None

            if not field_id:
                # Stable fallback id for controls missing both id/name.
                fallback_suffix = name or f"field_{index}"
                field_id = f"generated_{fallback_suffix}"

            if control.name == "textarea":
                field_type = "textarea"
            elif control.name == "select":
                field_type = "select"
            else:
                field_type = _clean_text(control.get("type", "")) or "text"

            fields.append(
                FormField(
                    field_id=field_id,
                    name=name,
                    label=label,
                    field_type=field_type,
                    placeholder=placeholder,
                )
            )

        return fields
    except Exception:
        return []
