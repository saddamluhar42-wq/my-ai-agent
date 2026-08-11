"""
Video Provider Bootstrap.

Initializes the central video-generation system
and provides safe startup/status helpers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from providers.video.manager import (
    VideoGenerationManager,
    get_video_manager,
)


# ============================================================
# GLOBAL STATE
# ============================================================

_initialized = False
_manager: Optional[
    VideoGenerationManager
] = None


# ============================================================
# INITIALIZE
# ============================================================

def initialize_video_system() -> (
    VideoGenerationManager
):
    """
    Initialize the central video provider manager.

    Initialization is performed only once.
    """

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

def get_initialized_video_manager() -> (
    VideoGenerationManager
):
    """
    Return the initialized video manager.
    """

    if not _initialized:
        return initialize_video_system()

    if _manager is None:
        return initialize_video_system()

    return _manager


# ============================================================
# PROVIDER STATUS
# ============================================================

def get_video_system_status() -> (
    Dict[str, Any]
):
    """
    Return safe status information for
    all registered video providers.

    API keys are never returned.
    """

    manager = (
        get_initialized_video_manager()
    )

    return manager.test_configuration()


# ============================================================
# AVAILABLE PROVIDERS
# ============================================================

def get_ready_video_providers() -> list[str]:
    """
    Return providers that are currently
    configured and ready.
    """

    manager = (
        get_initialized_video_manager()
    )

    return [
        entry.name
        for entry
        in manager.get_available_providers()
    ]


# ============================================================
# SYSTEM READY CHECK
# ============================================================

def is_video_system_ready() -> bool:
    """
    Return True when at least one video
    provider is configured and available.
    """

    return bool(
        get_ready_video_providers()
    )


# ============================================================
# STARTUP REPORT
# ============================================================

def get_video_startup_report() -> str:
    """
    Create a human-readable startup report.
    """

    status = (
        get_video_system_status()
    )

    providers = status.get(
        "providers",
        {},
    )

    ready = status.get(
        "available_providers",
        [],
    )

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

        enabled = bool(
            data.get(
                "enabled",
                False,
            )
        )

        configured = bool(
            data.get(
                "configured",
                False,
            )
        )

        available = bool(
            data.get(
                "available",
                False,
            )
        )

        if available:
            state = "READY"
        elif not enabled:
            state = "DISABLED"
        elif not configured:
            state = "NOT CONFIGURED"
        else:
            state = "UNAVAILABLE"

        lines.append(
            f"- {name}: {state}"
        )

    return "\n".join(lines)


# ============================================================
# BOOTSTRAP
# ============================================================

def bootstrap_video_providers() -> (
    VideoGenerationManager
):
    """
    Main bootstrap entry point.

    Call this once when the AI Agent starts.
    """

    manager = (
        initialize_video_system()
    )

    return manager


# ============================================================
# AUTO INITIALIZATION
# ============================================================

bootstrap_video_providers()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "initialize_video_system",
    "get_initialized_video_manager",
    "get_video_system_status",
    "get_ready_video_providers",
    "is_video_system_ready",
    "get_video_startup_report",
    "bootstrap_video_providers",
]
