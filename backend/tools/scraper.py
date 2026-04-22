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
_JS_RENDER_TIMEOUT_MS = 12000
_MAX_JD_CHARS = 4000
_MIN_JD_CHARS = 100
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 JobAssistantBot/1.0"
)


def _get_rendered_html(url: str) -> str:
    """Fetch HTML using a real browser for JS-heavy pages.

    Returns empty string when Playwright is unavailable or rendering fails.
    """
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception:
        return ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=_USER_AGENT)
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=_JS_RENDER_TIMEOUT_MS,
            )
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except PlaywrightTimeoutError:
                # Dynamic pages may keep long-polling; continue with current DOM snapshot.
                pass
            rendered = page.content() or ""
            browser.close()
            return rendered
    except Exception:
        return ""


def _extract_form_controls_via_playwright(url: str) -> list[dict[str, str | None]]:
    """Extract controls from live browser DOM, including shadow roots."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception:
        return []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=_USER_AGENT)
            page.goto(url, wait_until="domcontentloaded", timeout=_JS_RENDER_TIMEOUT_MS)
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except PlaywrightTimeoutError:
                pass
            try:
                page.wait_for_selector("input, textarea, select", timeout=2500)
            except PlaywrightTimeoutError:
                pass
            extractor_js = """() => {
                  const output = [];
                  const skipInputTypes = new Set(["hidden", "submit", "button", "image", "reset"]);

                  const clean = (val) => {
                    if (val === undefined || val === null) return null;
                    const text = String(val).replace(/\\s+/g, " ").trim();
                    return text || null;
                  };

                  const getLabel = (el) => {
                    let label = clean(el.getAttribute("aria-label"));
                    if (label) return label;

                    const id = clean(el.id);
                    if (id) {
                      const linked = document.querySelector(`label[for="${id}"]`);
                      if (linked) {
                        label = clean(linked.textContent);
                        if (label) return label;
                      }
                    }

                    const labelledBy = clean(el.getAttribute("aria-labelledby"));
                    if (labelledBy) {
                      const text = labelledBy
                        .split(/\\s+/)
                        .map((itemId) => document.getElementById(itemId))
                        .filter(Boolean)
                        .map((node) => clean(node.textContent))
                        .filter(Boolean)
                        .join(" ");
                      if (clean(text)) return clean(text);
                    }

                    const parentLabel = el.closest("label");
                    if (parentLabel) return clean(parentLabel.textContent);
                    return null;
                  };

                  const pushControl = (el) => {
                    const tag = (el.tagName || "").toLowerCase();
                    const inputType = clean(el.getAttribute("type")) || "";
                    if (tag === "input" && skipInputTypes.has(inputType.toLowerCase())) return;

                    const fieldType = tag === "textarea" ? "textarea" : (tag === "select" ? "select" : (inputType || "text"));
                    output.push({
                      field_id: clean(el.id) || clean(el.getAttribute("name")) || null,
                      name: clean(el.getAttribute("name")),
                      label: getLabel(el),
                      field_type: fieldType,
                      placeholder: clean(el.getAttribute("placeholder")),
                    });
                  };

                  const traverse = (root) => {
                    if (!root || !root.querySelectorAll) return;
                    root.querySelectorAll("input, textarea, select").forEach(pushControl);
                    root.querySelectorAll("*").forEach((node) => {
                      if (node.shadowRoot) traverse(node.shadowRoot);
                    });
                  };

                  traverse(document);
                  return output;
                }"""
            def collect_controls() -> list[dict[str, str | None]]:
                controls_inner: list[dict[str, str | None]] = []
                frames_inner = [page.main_frame, *page.frames]
                for frame in frames_inner:
                    try:
                        data = frame.evaluate(extractor_js)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    controls_inner.append(item)
                    except Exception:
                        continue
                return controls_inner

            def click_progress_actions() -> bool:
                selectors = [
                    'a[data-automation-id="applyManually"]',
                    'button[data-automation-id="applyManually"]',
                    '[data-automation-id="applyButton"]',
                    '[data-automation-id="bottom-navigation-next-button"]',
                    'button:has-text("Apply Manually")',
                    'button:has-text("Apply manually")',
                    'button:has-text("Start Application")',
                    'button:has-text("Apply")',
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                    'a:has-text("Apply Manually")',
                    'a:has-text("Apply")',
                    '[role="button"]:has-text("Apply")',
                    '[role="button"]:has-text("Continue")',
                    '[role="button"]:has-text("Next")',
                ]

                frames_inner = [page.main_frame, *page.frames]
                for frame in frames_inner:
                    for selector in selectors:
                        try:
                            loc = frame.locator(selector).first
                            if loc.count() == 0:
                                continue
                            if not loc.is_visible(timeout=400):
                                continue
                            loc.click(timeout=1200)
                            page.wait_for_timeout(700)
                            try:
                                page.wait_for_selector("input, textarea, select", timeout=2000)
                            except Exception:
                                pass
                            return True
                        except Exception:
                            continue
                return False

            controls = collect_controls()
            # Session-aware path for multi-step ATS pages (Workday/Oracle-style):
            # try progressing application flow a few steps and re-collect.
            for _ in range(10):
                meaningful_seed = [
                    c
                    for c in controls
                    if str(c.get("label") or c.get("name") or "").strip()
                ]
                if len(controls) >= 6 and len(meaningful_seed) >= 3:
                    break
                progressed = click_progress_actions()
                if not progressed:
                    break
                controls = collect_controls()

            browser.close()
            # Deduplicate by (field_id,name,label,type) while preserving order.
            deduped: list[dict[str, str | None]] = []
            seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
            for item in controls:
                key = (
                    item.get("field_id"),
                    item.get("name"),
                    item.get("label"),
                    item.get("field_type"),
                )
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(item)
            return deduped
    except Exception:
        return []


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


def _form_field_from_parts(
    *,
    index: int,
    field_id: str | None,
    name: str | None,
    label: str | None,
    field_type: str | None,
    placeholder: str | None,
) -> FormField:
    normalized_id = _clean_text(field_id or "")
    normalized_name = _clean_text(name or "") or None
    normalized_placeholder = _clean_text(placeholder or "") or None
    normalized_label = _clean_text(label or "") or None
    normalized_type = _clean_text(field_type or "") or "text"

    if not normalized_id:
        fallback_suffix = normalized_name or f"field_{index}"
        normalized_id = f"generated_{fallback_suffix}"

    return FormField(
        field_id=normalized_id,
        name=normalized_name,
        label=normalized_label or normalized_placeholder or normalized_name or normalized_id or None,
        field_type=normalized_type,
        placeholder=normalized_placeholder,
    )


def _looks_like_low_signal_fields(fields: list[FormField]) -> bool:
    """Heuristic: fields exist but look like nav/share/UI chrome, not application fields."""
    if not fields:
        return True
    meaningful_hints = (
        "name",
        "email",
        "phone",
        "resume",
        "cover letter",
        "linkedin",
        "portfolio",
        "address",
        "city",
        "country",
        "state",
        "province",
        "experience",
    )
    junk_snippets = (
        "copy link",
        "share",
        "assistant",
        "chat",
        "search for a job",
        "oda work summary",
        "oda-work-summary",
    )
    score = 0
    for field in fields:
        text = " ".join(
            part
            for part in (field.label, field.name, field.placeholder, field.field_id)
            if part
        ).lower()
        if any(junk in text for junk in junk_snippets):
            continue
        if any(hint in text for hint in meaningful_hints):
            score += 1
    return score == 0


def scrape_form_fields_interactive(url: str) -> list[FormField]:
    """Force browser-driven extraction with progression clicks (ATS recovery mode)."""
    browser_controls = _extract_form_controls_via_playwright(url)
    fields: list[FormField] = []
    for index, item in enumerate(browser_controls, start=1):
        if not isinstance(item, dict):
            continue
        fields.append(
            _form_field_from_parts(
                index=index,
                field_id=item.get("field_id"),
                name=item.get("name"),
                label=item.get("label"),
                field_type=item.get("field_type"),
                placeholder=item.get("placeholder"),
            )
        )
    return fields


def scrape_form_fields(url: str) -> list[FormField]:
    """Extract normalized form fields from a page.

    Returns an empty list when no parseable fields are available or request fails.
    """

    html = _get_html(url)
    if not html:
        html = _get_rendered_html(url)
        if not html:
            return []

    try:
        soup = BeautifulSoup(html, "html.parser")
        fields: list[FormField] = []

        for index, control in enumerate(_iter_form_controls(soup), start=1):
            if control.name == "textarea":
                field_type = "textarea"
            elif control.name == "select":
                field_type = "select"
            else:
                field_type = control.get("type")

            fields.append(
                _form_field_from_parts(
                    index=index,
                    field_id=control.get("id"),
                    name=control.get("name"),
                    label=_extract_label(control, soup),
                    field_type=field_type,
                    placeholder=control.get("placeholder"),
                )
            )

        if fields and not _looks_like_low_signal_fields(fields):
            return fields

        # JS fallback: if static HTML had no controls, try rendered DOM once.
        rendered_html = _get_rendered_html(url)
        if not rendered_html:
            return []

        rendered_soup = BeautifulSoup(rendered_html, "html.parser")
        rendered_fields: list[FormField] = []

        for index, control in enumerate(_iter_form_controls(rendered_soup), start=1):
            if control.name == "textarea":
                field_type = "textarea"
            elif control.name == "select":
                field_type = "select"
            else:
                field_type = control.get("type")

            rendered_fields.append(
                _form_field_from_parts(
                    index=index,
                    field_id=control.get("id"),
                    name=control.get("name"),
                    label=_extract_label(control, rendered_soup),
                    field_type=field_type,
                    placeholder=control.get("placeholder"),
                )
            )

        if rendered_fields and not _looks_like_low_signal_fields(rendered_fields):
            return rendered_fields

        return scrape_form_fields_interactive(url)
    except Exception:
        return []
