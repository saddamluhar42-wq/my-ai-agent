"""
Video generation provider package.

Contains provider integrations and the central
video generation manager.
"""

from providers.video.manager import (
    VideoGenerationManager,
    VideoGenerationResult,
    video_manager,
    generate_video,
    get_video_manager,
    get_video_provider_status,
    get_available_video_providers,
    test_video_providers,
)

from providers.video.bootstrap import (
    initialize_video_system,
    get_initialized_video_manager,
    get_video_system_status,
    get_ready_video_providers,
    is_video_system_ready,
    get_video_startup_report,
    bootstrap_video_providers,
)


__all__ = [
    # Manager
    "VideoGenerationManager",
    "VideoGenerationResult",
    "video_manager",

    # Generation
    "generate_video",

    # Manager helpers
    "get_video_manager",
    "get_video_provider_status",
    "get_available_video_providers",
    "test_video_providers",

    # Bootstrap
    "initialize_video_system",
    "get_initialized_video_manager",
    "get_video_system_status",
    "get_ready_video_providers",
    "is_video_system_ready",
    "get_video_startup_report",
    "bootstrap_video_providers",
]
