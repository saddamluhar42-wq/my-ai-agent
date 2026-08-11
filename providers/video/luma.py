"""
Luma Dream Machine video generation provider.

Supports:
- Text-to-video
- Multiple API keys
- Automatic key fallback
- Generation polling
- Video download
- 16:9 / 9:16 and other supported aspect ratios
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LUMA_API_URL = (
    "https://api.lumalabs.ai"
    "/dream-machine/v1"
)

DEFAULT_MODEL = os.getenv(
    "LUMA_VIDEO_MODEL",
    "ray-2",
)

DEFAULT_ASPECT_RATIO = os.getenv(
    "LUMA_VIDEO_ASPECT_RATIO",
    "16:9",
)

DEFAULT_RESOLUTION = os.getenv(
    "LUMA_VIDEO_RESOLUTION",
    "720p",
)

DEFAULT_DURATION = os.getenv(
    "LUMA_VIDEO_DURATION",
    "5s",
)

DEFAULT_OUTPUT_DIR = Path(
    os.getenv(
        "VIDEO_OUTPUT_DIR",
        "generated_videos",
    )
)

DEFAULT_TIMEOUT = int(
    os.getenv(
        "REQUEST_TIMEOUT",
        "90",
    )
)

DEFAULT_POLL_INTERVAL = 5


class LumaVideoError(Exception):
    """Raised when a Luma video operation fails."""


class LumaVideoProvider:
    """
    Luma Dream Machine provider.

    Supported environment variables:

        LUMA_API_KEY_1
        LUMA_API_KEY_2
        LUMA_API_KEY_3

    Legacy fallback:

        LUMA_API_KEY
    """

    name = "luma"

    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        model: Optional[str] = None,
        output_dir: Optional[str | Path] = None,
        timeout: Optional[int] = None,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:

        self.api_keys = (
            api_keys
            if api_keys is not None
            else self._load_api_keys()
        )

        self.model = (
            model
            or DEFAULT_MODEL
        )

        self.output_dir = Path(
            output_dir
            or DEFAULT_OUTPUT_DIR
        )

        self.timeout = (
            timeout
            if timeout is not None
            else DEFAULT_TIMEOUT
        )

        self.poll_interval = max(
            1,
            int(poll_interval),
        )

    # ========================================================
    # API KEYS
    # ========================================================

    @staticmethod
    def _load_api_keys() -> List[str]:
        keys: List[str] = []

        for name in (
            "LUMA_API_KEY_1",
            "LUMA_API_KEY_2",
            "LUMA_API_KEY_3",
        ):
            value = os.getenv(
                name,
                "",
            ).strip()

            if value:
                keys.append(value)

        legacy_key = os.getenv(
            "LUMA_API_KEY",
            "",
        ).strip()

        if (
            legacy_key
            and legacy_key not in keys
        ):
            keys.append(legacy_key)

        return keys

    def refresh_api_keys(self) -> None:
        self.api_keys = (
            self._load_api_keys()
        )

    def is_configured(self) -> bool:
        self.refresh_api_keys()
        return bool(self.api_keys)

    def get_key_count(self) -> int:
        self.refresh_api_keys()
        return len(self.api_keys)

    # ========================================================
    # HTTP
    # ========================================================

    def _headers(
        self,
        api_key: str,
    ) -> Dict[str, str]:

        return {
            "Accept": (
                "application/json"
            ),
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
        }

    def _request_json(
        self,
        method: str,
        url: str,
        api_key: str,
        payload: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:

        body = None

        if payload is not None:
            body = json.dumps(
                payload
            ).encode("utf-8")

        request = Request(
            url=url,
            data=body,
            headers=self._headers(
                api_key
            ),
            method=method,
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                raw = response.read()

                if not raw:
                    return {}

                return json.loads(
                    raw.decode(
                        "utf-8"
                    )
                )

        except HTTPError as error:

            try:
                details = (
                    error.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )
            except Exception:
                details = str(error)

            raise LumaVideoError(
                f"Luma HTTP {error.code}: "
                f"{details}"
            ) from error

        except URLError as error:

            raise LumaVideoError(
                f"Luma connection failed: "
                f"{error}"
            ) from error

        except Exception as error:

            raise LumaVideoError(
                f"Luma request failed: "
                f"{error}"
            ) from error

    # ========================================================
    # CREATE GENERATION
    # ========================================================

    def _create_generation(
        self,
        api_key: str,
        prompt: str,
        model: str,
        aspect_ratio: str,
        resolution: Optional[str],
        duration: Optional[str],
        loop: bool,
        concepts: Optional[
            List[Dict[str, Any]]
        ],
    ) -> Dict[str, Any]:

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "loop": loop,
        }

        if resolution:
            payload[
                "resolution"
            ] = resolution

        if duration:
            payload[
                "duration"
            ] = duration

        if concepts:
            payload[
                "concepts"
            ] = concepts

        return self._request_json(
            method="POST",
            url=(
                f"{LUMA_API_URL}"
                "/generations/video"
            ),
            api_key=api_key,
            payload=payload,
        )

    # ========================================================
    # GET GENERATION
    # ========================================================

    def _get_generation(
        self,
        api_key: str,
        generation_id: str,
    ) -> Dict[str, Any]:

        return self._request_json(
            method="GET",
            url=(
                f"{LUMA_API_URL}"
                f"/generations/"
                f"{generation_id}"
            ),
            api_key=api_key,
        )

    # ========================================================
    # POLLING
    # ========================================================

    def _wait_for_generation(
        self,
        api_key: str,
        generation_id: str,
    ) -> Dict[str, Any]:

        started_at = time.monotonic()

        while True:

            elapsed = (
                time.monotonic()
                - started_at
            )

            if elapsed > self.timeout:
                raise LumaVideoError(
                    "Luma video generation "
                    "timed out."
                )

            generation = (
                self._get_generation(
                    api_key=api_key,
                    generation_id=(
                        generation_id
                    ),
                )
            )

            state = str(
                generation.get(
                    "state",
                    "",
                )
            ).lower()

            if state == "completed":
                return generation

            if state == "failed":
                reason = generation.get(
                    "failure_reason"
                )

                raise LumaVideoError(
                    "Luma generation failed: "
                    f"{reason or 'Unknown error.'}"
                )

            time.sleep(
                self.poll_interval
            )

    # ========================================================
    # OUTPUT URL
    # ========================================================

    @staticmethod
    def _extract_video_url(
        generation: Dict[str, Any],
    ) -> Optional[str]:

        assets = generation.get(
            "assets"
        )

        if not isinstance(
            assets,
            dict,
        ):
            return None

        video_url = assets.get(
            "video"
        )

        if (
            isinstance(
                video_url,
                str,
            )
            and video_url.startswith(
                "http"
            )
        ):
            return video_url

        return None

    # ========================================================
    # OUTPUT PATH
    # ========================================================

    def _resolve_output_path(
        self,
        output_path: Optional[
            str | Path
        ],
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
            / (
                f"luma_"
                f"{int(time.time())}"
                f".mp4"
            )
        )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    def _download_video(
        self,
        video_url: str,
        output_path: Path,
    ) -> None:

        request = Request(
            url=video_url,
            method="GET",
        )

        try:

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                with output_path.open(
                    "wb"
                ) as file:

                    while True:

                        chunk = (
                            response.read(
                                1024 * 1024
                            )
                        )

                        if not chunk:
                            break

                        file.write(
                            chunk
                        )

        except HTTPError as error:

            raise LumaVideoError(
                f"Luma video download "
                f"failed: HTTP {error.code}"
            ) from error

        except URLError as error:

            raise LumaVideoError(
                f"Luma video download "
                f"connection failed: "
                f"{error}"
            ) from error

        except Exception as error:

            raise LumaVideoError(
                f"Failed to save Luma "
                f"video: {error}"
            ) from error

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(
        self,
        prompt: str,
        *,
        output_path: Optional[
            str | Path
        ] = None,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        duration: Optional[str] = None,
        loop: bool = False,
        concepts: Optional[
            List[Dict[str, Any]]
        ] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        prompt = str(
            prompt or ""
        ).strip()

        if not prompt:
            raise LumaVideoError(
                "Video generation prompt "
                "is required."
            )

        if len(prompt) < 3:
            raise LumaVideoError(
                "Luma prompt must contain "
                "at least 3 characters."
            )

        if len(prompt) > 5000:
            raise LumaVideoError(
                "Luma prompt must not exceed "
                "5000 characters."
            )

        self.refresh_api_keys()

        if not self.api_keys:
            raise LumaVideoError(
                "No Luma API keys are "
                "configured."
            )

        selected_model = (
            model
            or self.model
        )

        selected_ratio = (
            aspect_ratio
            or DEFAULT_ASPECT_RATIO
        )

        selected_resolution = (
            resolution
            if resolution is not None
            else DEFAULT_RESOLUTION
        )

        selected_duration = (
            duration
            if duration is not None
            else DEFAULT_DURATION
        )

        final_path = (
            self._resolve_output_path(
                output_path
            )
        )

        errors = []

        # ====================================================
        # AUTOMATIC KEY FALLBACK
        # ====================================================

        for index, api_key in enumerate(
            self.api_keys,
            start=1,
        ):

            try:

                generation = (
                    self._create_generation(
                        api_key=api_key,
                        prompt=prompt,
                        model=selected_model,
                        aspect_ratio=(
                            selected_ratio
                        ),
                        resolution=(
                            selected_resolution
                        ),
                        duration=(
                            selected_duration
                        ),
                        loop=loop,
                        concepts=concepts,
                    )
                )

                generation_id = str(
                    generation.get(
                        "id",
                        "",
                    )
                ).strip()

                if not generation_id:
                    raise LumaVideoError(
                        "Luma did not return "
                        "a generation ID."
                    )

                completed = (
                    self._wait_for_generation(
                        api_key=api_key,
                        generation_id=(
                            generation_id
                        ),
                    )
                )

                video_url = (
                    self._extract_video_url(
                        completed
                    )
                )

                if not video_url:
                    raise LumaVideoError(
                        "Luma completed the "
                        "generation but returned "
                        "no video URL."
                    )

                self._download_video(
                    video_url=video_url,
                    output_path=final_path,
                )

                return {
                    "success": True,
                    "provider": self.name,
                    "model": selected_model,
                    "output_path": str(
                        final_path
                    ),
                    "generation_id": (
                        generation_id
                    ),
                    "key_index": index,
                    "metadata": {
                        "prompt": prompt,
                        "aspect_ratio": (
                            selected_ratio
                        ),
                        "resolution": (
                            selected_resolution
                        ),
                        "duration": (
                            selected_duration
                        ),
                    },
                }

            except Exception as error:

                errors.append(
                    {
                        "key_index": index,
                        "error": str(
                            error
                        ),
                    }
                )

                continue

        raise LumaVideoError(
            "All configured Luma API keys "
            "failed. "
            f"Attempts: {errors}"
        )


# ============================================================
# GLOBAL PROVIDER
# ============================================================

luma_video_provider = (
    LumaVideoProvider()
)


# ============================================================
# PUBLIC HELPERS
# ============================================================

def is_luma_video_configured() -> bool:
    return (
        luma_video_provider
        .is_configured()
    )


def get_luma_key_count() -> int:
    return (
        luma_video_provider
        .get_key_count()
    )


def generate_luma_video(
    prompt: str,
    *,
    output_path: Optional[
        str | Path
    ] = None,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    duration: Optional[str] = None,
    loop: bool = False,
    concepts: Optional[
        List[Dict[str, Any]]
    ] = None,
    **kwargs: Any,
) -> Dict[str, Any]:

    return (
        luma_video_provider.generate(
            prompt=prompt,
            output_path=output_path,
            model=model,
            aspect_ratio=(
                aspect_ratio
            ),
            resolution=resolution,
            duration=duration,
            loop=loop,
            concepts=concepts,
            **kwargs,
        )
    )
