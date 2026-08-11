"""
Video Provider Bootstrap.

Initializes the central video-generation system
and normalizes legacy Render environment variable names
before provider modules are loaded.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _set_alias(target: str, *sources: str) -> None:
    """Copy the first configured source variable to target if needed."""
    if os.getenv(target, "").strip():
        return

    for source in sources:
        value = os.getenv(source, "").strip()
        if value:
            os.environ[target] = value
            return


def normalize_video_environment() -> None:
    """Normalize alternate Render variable names used by older configs."""
    for index in (1, 2, 3):
        _set_alias(
            f"RUNWAY_API_KEY_{index}",
            f"RUNWAY_API_KEY{index}",
        )
        _set_alias(
            f"LUMA_API_KEY_{index}",
            f"LUMA_API_KEY{index}",
        )

    _set_alias(
        "REPLICATE_API_TOKEN",
        "REPLICATE_API_KEY",
        "REPLICATE_API_TOKEN_1",
    )
    _set_alias(
        "REPLICATE_API_TOKEN_2",
        "REPLICATE_API_KEY_2",
    )

    _set_alias(
        "GOOGLE_VIDEO_API_KEY",
        "GEMINI_API_KEY",
    )


# Normalize BEFORE importing the manager. The manager imports
# provider modules during initialization, so this ordering matters.
normalize_video_environment()

from providers.video.manager import (  # noqa: E402
    VideoGenerationManager,
    get_video_manager,
)


# ============================================================
# GLOBAL STATE
# ============================================================

_initialized = False
_manager: Optional[VideoGenerationManager] = None


# ============================================================
# INITIALIZE
# ============================================================

def initialize_video_system() -> VideoGenerationManager:
    """Initialize the central video provider manager once."""
    global _initialized
    global _manager

    if _initialized and _manager is not None:
        return _manager

    _manager = get_video_manager()
    _initialized = True
    return _manager


# ============================================================
# GET MANAGER
# ============================================================

def get_initialized_video_manager() -> VideoGenerationManager:
    """Return the initialized video manager."""
    if not _initialized:
        return initialize_video_system()

    if _manager is None:
        return initialize_video_system()

    return _manager


# ============================================================
# PROVIDER STATUS
# ============================================================

def get_video_system_status() -> Dict[str, Any]:
    """Return safe status information; API keys are never returned."""
    manager = get_initialized_video_manager()
    return manager.test_configuration()


# ============================================================
# AVAILABLE PROVIDERS
# ============================================================

def get_ready_video_providers() -> list[str]:
    """Return providers that are configured and ready."""
    manager = get_initialized_video_manager()
    return [
        entry.name
        for entry in manager.get_available_providers()
    ]


# ============================================================
# SYSTEM READY CHECK
# ============================================================

def is_video_system_ready() -> bool:
    """Return True when at least one video provider is available."""
    return bool(get_ready_video_providers())


# ============================================================
# STARTUP REPORT
# ============================================================

def get_video_startup_report() -> str:
    """Create a human-readable startup report."""
    status = get_video_system_status()
    providers = status.get("providers", {})
    ready = status.get("available_providers", [])

    lines = [
        "VIDEO SYSTEM",
        "============",
        "",
        f"Ready: {'YES' if ready else 'NO'}",
        f"Available providers: {len(ready)}",
        "",
        "PROVIDERS:",
    ]

    for name, data in providers.items():
        enabled = bool(data.get("enabled", False))
        configured = bool(data.get("configured", False))
        available = bool(data.get("available", False))

        if available:
            state = "READY"
        elif not enabled:
            state = "DISABLED"
        elif not configured:
            state = "NOT CONFIGURED"
        else:
            state = "UNAVAILABLE"

        lines.append(f"- {name}: {state}")

    return "\n".join(lines)


# ============================================================
# BOOTSTRAP
# ============================================================

def bootstrap_video_providers() -> VideoGenerationManager:
    """Main bootstrap entry point."""
    return initialize_video_system()


# ============================================================
# AUTO INITIALIZATION
# ============================================================

bootstrap_video_providers()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "normalize_video_environment",
    "initialize_video_system",
    "get_initialized_video_manager",
    "get_video_system_status",
    "get_ready_video_providers",
    "is_video_system_ready",
    "get_video_startup_report",
    "bootstrap_video_providers",
]
