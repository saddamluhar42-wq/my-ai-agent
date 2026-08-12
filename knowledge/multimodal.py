"""Multimodal analysis for Ultra Legend knowledge ingestion.

Turns local images and videos into searchable textual knowledge using a
configured Gemini multimodal model. The original media file is never stored in
the knowledge table; only the model's analysis and provenance metadata enter
RAG.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from config import GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_MODEL, GEMINI_MODEL_2

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None


class MultimodalAnalysisError(RuntimeError):
    pass


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def _clients() -> list[tuple[str, str]]:
    return [
        (key, model)
        for key, model in (
            (GEMINI_API_KEY, GEMINI_MODEL),
            (GEMINI_API_KEY_2, GEMINI_MODEL_2),
        )
        if key
    ]


def _prompt(kind: str) -> str:
    if kind == "image":
        return """Analyze this image for a universal AI knowledge base. Return a factual, detailed, searchable description. Cover: visible people and non-sensitive attributes; objects; setting/location cues; actions/poses; clothing and visual design; food/products if present; readable text/OCR; colors/materials; relationships between objects; important visual details; and likely context. Clearly separate what is directly visible from uncertain inference. Do not identify real people. Do not invent facts."""
    return """Analyze this video for a universal AI knowledge base. Produce a detailed chronological summary of the meaningful visual events. Include: scenes and transitions; people and visible actions; objects; setting; food/products; readable text/OCR when visible; important visual details; approximate sequence/timing; and audio/speech/environmental cues when the model can reliably perceive them. Clearly separate direct observations from uncertain inference. Do not identify real people. Do not invent facts. Focus on information useful for later semantic retrieval."""


def analyze_media(path: str | Path) -> dict[str, Any]:
    """Analyze an image/video with Gemini and return text plus provenance."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise MultimodalAnalysisError(f"Media not found: {p}")

    suffix = p.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        kind = "image"
    elif suffix in VIDEO_EXTENSIONS:
        kind = "video"
    else:
        raise MultimodalAnalysisError(f"Unsupported media type: {suffix}")

    if genai is None:
        raise MultimodalAnalysisError("google-genai package is not installed")

    errors: list[str] = []
    for key, model in _clients():
        try:
            client = genai.Client(api_key=key)
            uploaded = client.files.upload(file=str(p))
            response = client.models.generate_content(
                model=model,
                contents=[uploaded, _prompt(kind)],
            )
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                raise MultimodalAnalysisError("Multimodal model returned no analysis")
            return {
                "analysis": text,
                "kind": kind,
                "model": model,
                "path": str(p),
                "analysis_pending": False,
            }
        except Exception as exc:  # try the next configured key
            errors.append(f"{model}: {exc}")

    raise MultimodalAnalysisError("; ".join(errors) or "No Gemini multimodal key configured")


def multimodal_available() -> bool:
    return bool(genai is not None and _clients())
