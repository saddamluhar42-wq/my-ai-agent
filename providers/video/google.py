"""
Google Veo video generation provider.

Uses the Gemini API / Google GenAI SDK
for text-to-video generation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from config import GEMINI_API_KEY


DEFAULT_MODEL = os.getenv(
    "GOOGLE_VIDEO_MODEL",
    "veo-3.1-generate-preview",
)

DEFAULT_OUTPUT_DIR = Path(
    os.getenv(
        "VIDEO_OUTPUT_DIR",
        "generated_videos",
    )
)


class GoogleVideoError(Exception):
    """Raised when Google video generation fails."""


class GoogleVideoProvider:
    """
    Google Veo video-generation provider.

    The provider does not store API keys in source code.
    The key is read from GEMINI_API_KEY.
    """

    name = "google"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        output_dir: Optional[str | Path] = None,
    ) -> None:

        self.api_key = (
            api_key
            or GEMINI_API_KEY
            or os.getenv("GEMINI_API_KEY")
        )

        self.model = (
            model
            or DEFAULT_MODEL
        )

        self.output_dir = Path(
            output_dir
            or DEFAULT_OUTPUT_DIR
        )

    def is_configured(self) -> bool:
        """Return True when a Google API key is available."""

        return bool(
            self.api_key
            and self.api_key.strip()
        )

    def _create_client(self):
        """Create a Google GenAI client."""

        if not self.is_configured():
            raise GoogleVideoError(
                "GEMINI_API_KEY is not configured."
            )

        try:
            from google import genai
        except ImportError as error:
            raise GoogleVideoError(
                "Google GenAI SDK is not installed. "
                "Install the 'google-genai' package."
            ) from error

        try:
            return genai.Client(
                api_key=self.api_key
            )
        except Exception as error:
            raise GoogleVideoError(
                f"Failed to create Google GenAI client: {error}"
            ) from error

    def generate(
        self,
        prompt: str,
        *,
        output_path: Optional[str | Path] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a video from a text prompt.

        Returns a dictionary containing:
        - success
        - provider
        - model
        - output_path
        - metadata
        """

        prompt = str(
            prompt or ""
        ).strip()

        if not prompt:
            raise GoogleVideoError(
                "Video generation prompt is required."
            )

        client = self._create_client()

        selected_model = (
            model
            or self.model
        )

        try:
            operation = client.models.generate_videos(
                model=selected_model,
                prompt=prompt,
            )
        except Exception as error:
            raise GoogleVideoError(
                f"Google Veo generation request failed: {error}"
            ) from error

        try:
            while not operation.done:
                operation = client.operations.get(
                    operation
                )
        except Exception as error:
            raise GoogleVideoError(
                f"Google Veo operation polling failed: {error}"
            ) from error

        if getattr(
            operation,
            "error",
            None,
        ):
            raise GoogleVideoError(
                str(operation.error)
            )

        response = getattr(
            operation,
            "response",
            None,
        )

        if response is None:
            raise GoogleVideoError(
                "Google Veo returned no response."
            )

        generated_videos = getattr(
            response,
            "generated_videos",
            None,
        )

        if not generated_videos:
            raise GoogleVideoError(
                "Google Veo returned no generated video."
            )

        generated_video = generated_videos[0]

        video_file = getattr(
            generated_video,
            "video",
            None,
        )

        if video_file is None:
            raise GoogleVideoError(
                "Google Veo response does not contain "
                "a downloadable video."
            )

        final_path = self._resolve_output_path(
            output_path
        )

        try:
            final_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            client.files.download(
                file=video_file
            )

            video_file.save(
                str(final_path)
            )

        except Exception as error:
            raise GoogleVideoError(
                f"Failed to save generated video: {error}"
            ) from error

        return {
            "success": True,
            "provider": self.name,
            "model": selected_model,
            "output_path": str(
                final_path
            ),
            "metadata": {
                "prompt": prompt,
            },
        }

    def _resolve_output_path(
        self,
        output_path: Optional[str | Path],
    ) -> Path:

        if output_path:
            path = Path(
                output_path
            )

            if not path.suffix:
                path = path.with_suffix(
                    ".mp4"
                )

            return path

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return (
            self.output_dir
            / "google_veo_video.mp4"
        )


google_video_provider = GoogleVideoProvider()


def is_google_video_configured() -> bool:
    """Check whether Google video generation is configured."""

    return google_video_provider.is_configured()


def generate_google_video(
    prompt: str,
    *,
    output_path: Optional[str | Path] = None,
    model: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Generate a video using Google Veo."""

    return google_video_provider.generate(
        prompt=prompt,
        output_path=output_path,
        model=model,
        **kwargs,
    )
