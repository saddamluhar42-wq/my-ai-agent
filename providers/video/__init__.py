"""
Video generation provider package.

This package contains provider integrations
for AI video generation.
"""

from providers.video.manager import (
    VideoGenerationManager,
    VideoGenerationResult,
    video_manager,
)

__all__ = [
    "VideoGenerationManager",
    "VideoGenerationResult",
    "video_manager",
]
