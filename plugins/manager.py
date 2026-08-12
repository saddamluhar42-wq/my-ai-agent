"""Secure external plugin registry.

Plugins are remote HTTPS services described by a small JSON manifest. The
manager never downloads or executes arbitrary plugin source code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_MANIFEST_BYTES = 64 * 1024
ALLOWED_SCHEMES = {"https"}


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    description: str
    endpoint: str
    capabilities: tuple[str, ...]


def validate_https_url(value: str) -> str:
    parsed = urlparse(str(value).strip())
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError("Plugin endpoint must use HTTPS.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in plugin URLs are not allowed.")
    return value.strip()


def fetch_manifest(manifest_url: str, timeout: float = 5.0) -> PluginManifest:
    url = validate_https_url(manifest_url)
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "My-AI-Agent-Plugin-Manager/1.0"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("Plugin manifest is too large.")
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid plugin manifest.")
    name = str(data.get("name", "")).strip()
    version = str(data.get("version", "")).strip()
    description = str(data.get("description", "")).strip()
    endpoint = validate_https_url(str(data.get("endpoint", "")).strip())
    capabilities = data.get("capabilities", [])
    if not name or not version or not endpoint or not isinstance(capabilities, list):
        raise ValueError("Manifest requires name, version, endpoint and capabilities.")
    clean_caps = tuple(str(item).strip()[:80] for item in capabilities if str(item).strip())
    return PluginManifest(name, version, description[:500], endpoint, clean_caps)


def plugin_payload(manifest: PluginManifest) -> dict:
    return {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "endpoint": manifest.endpoint,
        "capabilities": list(manifest.capabilities),
    }
