"""Source acquisition adapters for Ultra Legend knowledge ingestion."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import re

import httpx
from pypdf import PdfReader

from knowledge.multimodal import MultimodalAnalysisError, analyze_media


@dataclass(slots=True)
class SourcePayload:
    content: str
    source: str
    title: str = ""
    source_type: str = "document"
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceConnectorError(RuntimeError):
    pass


def _html_text(html: str) -> str:
    html = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</(p|div|article|section|li|h[1-6])>", "\n", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html, flags=re.I)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


class WebURLConnector:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def fetch(self, url: str) -> SourcePayload:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise SourceConnectorError(f"Invalid URL: {url}")
        headers = {"User-Agent": "UltraLegendAI/1.0"}
        with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
        text = _html_text(response.text)
        if not text:
            raise SourceConnectorError(f"No readable text at {url}")
        match = re.search(r"<title[^>]*>(.*?)</title>", response.text, flags=re.I | re.S)
        title = _html_text(match.group(1)) if match else parsed.netloc
        return SourcePayload(text, str(response.url), title, "web", {"content_type": response.headers.get("content-type", "")})


class PDFConnector:
    def fetch(self, path: str | Path) -> SourcePayload:
        p = Path(path).expanduser().resolve()
        if not p.is_file() or p.suffix.lower() != ".pdf":
            raise SourceConnectorError(f"PDF not found: {p}")
        reader = PdfReader(str(p))
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {number}]\n{text}")
        content = "\n\n".join(pages).strip()
        if not content:
            raise SourceConnectorError(f"No extractable text in {p.name}")
        return SourcePayload(content, str(p), p.name, "pdf", {"page_count": len(reader.pages)})


class GitHubConnector:
    API = "https://api.github.com"

    def __init__(self, token: str | None = None, timeout: float = 30.0) -> None:
        self.token = token
        self.timeout = timeout

    def fetch(self, url: str) -> SourcePayload:
        parsed = urlparse(url)
        if parsed.netloc not in {"github.com", "www.github.com"}:
            raise SourceConnectorError(f"Not a GitHub URL: {url}")
        parts = [x for x in parsed.path.split("/") if x]
        if len(parts) < 2:
            raise SourceConnectorError(f"Invalid GitHub URL: {url}")
        owner, repo = parts[0], parts[1].removesuffix(".git")
        path = "/".join(parts[4:]) if len(parts) >= 5 and parts[2] in {"blob", "tree"} else ""
        api = f"{self.API}/repos/{owner}/{repo}/contents/{path}"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "UltraLegendAI/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(api)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("download_url"):
                raw = client.get(data["download_url"])
                raw.raise_for_status()
                return SourcePayload(raw.text, url, data.get("name", repo), "github", {"repository": f"{owner}/{repo}", "path": path})
            if isinstance(data, dict) and path == "":
                readme = client.get(f"{self.API}/repos/{owner}/{repo}/readme")
                if readme.is_success:
                    rd = readme.json()
                    raw = client.get(rd["download_url"])
                    raw.raise_for_status()
                    return SourcePayload(raw.text, url, f"{repo} README", "github", {"repository": f"{owner}/{repo}"})
        raise SourceConnectorError("GitHub target is not a supported text file or repository README")


class MediaConnector:
    """Analyze image/video assets before they enter the knowledge pipeline."""
    IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic"}
    VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

    def fetch(self, path: str | Path, analysis: str | None = None) -> SourcePayload:
        p = Path(path).expanduser().resolve()
        if not p.is_file():
            raise SourceConnectorError(f"Media not found: {p}")
        suffix = p.suffix.lower()
        if suffix in self.IMAGE:
            kind = "image"
        elif suffix in self.VIDEO:
            kind = "video"
        else:
            raise SourceConnectorError(f"Unsupported media type: {suffix}")

        if analysis:
            content = analysis
            metadata = {"path": str(p), "extension": suffix, "analysis_pending": False, "analysis_source": "external"}
        else:
            try:
                result = analyze_media(p)
                content = result["analysis"]
                metadata = {
                    "path": str(p),
                    "extension": suffix,
                    "analysis_pending": False,
                    "analysis_source": "gemini_multimodal",
                    "analysis_model": result.get("model", ""),
                }
            except MultimodalAnalysisError as exc:
                raise SourceConnectorError(f"Multimodal analysis failed for {p.name}: {exc}") from exc

        return SourcePayload(content, str(p), p.name, kind, metadata)


class AutomaticSourceConnector:
    """Route URLs, PDFs, GitHub repositories/files, photos and videos automatically."""
    def __init__(self, github_token: str | None = None) -> None:
        self.web = WebURLConnector()
        self.pdf = PDFConnector()
        self.github = GitHubConnector(github_token)
        self.media = MediaConnector()

    def fetch(self, source: str | Path, *, media_analysis: str | None = None) -> SourcePayload:
        value = str(source)
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            if parsed.netloc.lower() in {"github.com", "www.github.com"}:
                return self.github.fetch(value)
            return self.web.fetch(value)
        p = Path(value).expanduser()
        if p.suffix.lower() == ".pdf":
            return self.pdf.fetch(p)
        if p.suffix.lower() in self.media.IMAGE or p.suffix.lower() in self.media.VIDEO:
            return self.media.fetch(p, media_analysis)
        raise SourceConnectorError(f"Unsupported automatic source: {source}")
