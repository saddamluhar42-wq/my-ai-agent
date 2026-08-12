from __future__ import annotations

import base64
import os
import tempfile
from typing import Any, Dict, List

from config import GEMINI_API_KEY, GEMINI_MODEL, OPENAI_API_KEY, OPENAI_MODEL


def _openai_image(prompt: str, item: Dict[str, Any]) -> str:
    import json, urllib.request
    data_url = f"data:{item.get('type','image/jpeg')};base64," + base64.b64encode(item["data"]).decode()
    payload = {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url}}]}], "max_tokens": 700}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=8) as response:
        body = json.loads(response.read().decode())
    return str(body["choices"][0]["message"]["content"])


def _gemini_media(prompt: str, item: Dict[str, Any]) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    suffix = os.path.splitext(item.get("name", "upload.bin"))[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(item["data"])
        path = handle.name
    try:
        uploaded = client.files.upload(file=path)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=[uploaded, prompt])
        return str(response.text or "")
    finally:
        try: os.unlink(path)
        except OSError: pass


def analyze_uploaded_media(files: List[Dict[str, Any]], question: str) -> str:
    if not files:
        return ""
    sections = []
    prompt = f"Analyze the attached media for the user's question. Describe only what is actually visible/audible and clearly state uncertainty. User question: {question}"
    for item in files[:4]:
        mime = str(item.get("type", ""))
        try:
            if mime.startswith("video/") or str(item.get("name", "")).lower().endswith((".mp4", ".mov", ".webm", ".avi", ".mkv")):
                if not GEMINI_API_KEY:
                    sections.append(f"MEDIA {item.get('name')}: video uploaded; video understanding requires a Gemini API key.")
                    continue
                text = _gemini_media(prompt, item)
            elif mime.startswith("image/"):
                if OPENAI_API_KEY:
                    text = _openai_image(prompt, item)
                elif GEMINI_API_KEY:
                    text = _gemini_media(prompt, item)
                else:
                    text = "Image uploaded, but no vision-capable provider is configured."
            else:
                continue
            sections.append(f"MEDIA ANALYSIS — {item.get('name')}:\n{text[:6000]}")
        except Exception as exc:
            sections.append(f"MEDIA ANALYSIS — {item.get('name')}: unavailable ({str(exc)[:240]}).")
    return "\n\n".join(sections)
