"""Scraping helpers for job descriptions and application forms."""

from __future__ import annotations

import json
import re
from typing import Iterable
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from schemas.autofill import FormField

_REQUEST_TIMEOUT_SECONDS = 20.0
_MAX_JD_CHARS = 4000
_MIN_JD_CHARS = 100
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


def _strip_html_to_text(html_fragment: str) -> str:
    if not html_fragment or "<" not in html_fragment:
        return _clean_text(html_fragment)
    try:
        frag = BeautifulSoup(html_fragment, "html.parser")
        return _clean_text(frag.get_text(separator=" ", strip=True))
    except Exception:
        return _clean_text(re.sub(r"<[^>]+>", " ", html_fragment))


def _extract_json_ld_job_description(soup: BeautifulSoup) -> str:
    """Pull JobPosting (or similar) description from JSON-LD before scripts are removed."""
    chunks: list[str] = []
    for script in soup.find_all("script", attrs={"type": lambda t: t and "ld+json" in t.lower()}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            raw_type = item.get("@type")
            if isinstance(raw_type, list):
                type_names = {t for t in raw_type if isinstance(t, str)}
            elif isinstance(raw_type, str):
                type_names = {raw_type}
            else:
                type_names = set()
            looks_like_job = (
                "JobPosting" in type_names
                or "WebPage" in type_names
                or (bool(item.get("title")) and bool(item.get("hiringOrganization")))
            )
            if not looks_like_job:
                continue
            desc = item.get("description")
            if isinstance(desc, str) and len(desc.strip()) > 40:
                chunks.append(_strip_html_to_text(desc))
            elif isinstance(desc, dict):
                val = desc.get("text") or desc.get("@value")
                if isinstance(val, str) and len(val.strip()) > 40:
                    chunks.append(_strip_html_to_text(val))
    return _clean_text(" ".join(chunks))


def _extract_ats_description_nodes(soup: BeautifulSoup) -> str:
    """Workday, Greenhouse, and similar often expose a dedicated description node."""
    automation_attrs = (
        "jobPostingDescription",
        "job-description",
        "jobDescriptionText",
        "job-details",
    )
    chunks: list[str] = []
    for attr_val in automation_attrs:
        for node in soup.find_all(attrs={"data-automation": attr_val}):
            t = _clean_text(node.get_text(separator=" ", strip=True))
            if len(t) >= 80:
                chunks.append(t)
        for node in soup.select(f"[data-qa='{attr_val}']"):
            t = _clean_text(node.get_text(separator=" ", strip=True))
            if len(t) >= 80:
                chunks.append(t)
    for sel in ("div.job-description", "div#job-description", "section.job-description"):
        node = soup.select_one(sel)
        if node:
            t = _clean_text(node.get_text(separator=" ", strip=True))
            if len(t) >= 80:
                chunks.append(t)
    if not chunks:
        return ""
    return max(chunks, key=len)


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
        from_ld = _extract_json_ld_job_description(soup)
        from_ats = _extract_ats_description_nodes(soup)

        for tag_name in ("script", "style", "noscript", "nav", "footer"):
            for node in soup.find_all(tag_name):
                node.decompose()

        root = soup.find("main") or soup.find("article") or soup.find("body") or soup
        body = _clean_text(root.get_text(separator=" ", strip=True))

        candidates = [c for c in (from_ld, from_ats, body) if c and len(c.strip()) >= 40]
        if not candidates:
            return ""
        best = max(candidates, key=len)
        return best[:_MAX_JD_CHARS]
    except Exception:
        return ""


def best_effort_jd_text(jd_url: str | None, jd_text: str | None) -> str:
    """Prefer scraping ``jd_url`` when it yields enough text; else use pasted ``jd_text``.

    Use this for ATS pages (e.g. Workday) that often need a pasted fallback.
    """
    u = (jd_url or "").strip()
    t = (jd_text or "").strip()
    if u:
        scraped = scrape_job_description(u)
        if len(scraped.strip()) >= _MIN_JD_CHARS:
            return scraped[:_MAX_JD_CHARS]
    if len(t) >= _MIN_JD_CHARS:
        return t[:_MAX_JD_CHARS]
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
