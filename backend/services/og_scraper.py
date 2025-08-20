from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup


@dataclass(slots=True)
class ScrapedMetadata:
    title: str = ""
    description: str = ""


def _sanitize_text(value: Optional[str], *, max_len: int = 4000) -> str:
    if not value:
        return ""
    # Collapse whitespace and strip
    text = re.sub(r"\s+", " ", value).strip()
    # Remove excessive control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    if len(text) > max_len:
        text = text[:max_len]
    return text


def _choose(*candidates: Optional[str]) -> str:
    for c in candidates:
        c2 = _sanitize_text(c)
        if c2:
            return c2
    return ""


async def fetch_og_metadata(url: str) -> ScrapedMetadata:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        resp = await client.get(url, headers=headers, follow_redirects=True)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    def meta(prop: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return str(tag["content"])  # type: ignore
        tag = soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            return str(tag["content"])  # type: ignore
        return None

    # Candidates
    og_title = meta("og:title")
    og_desc = meta("og:description")
    name_desc = meta("description")
    title_tag = None
    if soup.title and soup.title.string:
        title_tag = soup.title.string

    title = _choose(og_title, title_tag)
    description = _choose(og_desc, name_desc)

    return ScrapedMetadata(title=title, description=description)


__all__ = ["ScrapedMetadata", "fetch_og_metadata"]


