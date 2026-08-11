"""
Runway video generation provider.

Supports:
- Text-to-video generation
- Multiple API keys
- Automatic key fallback
- Task polling
- Video download
- Environment-variable based configuration

Environment variables:
    RUNWAY_API_KEY_1
    RUNWAY_API_KEY_2
    RUNWAY_API_KEY_3

Optional:
    RUNWAY_MODEL
    RUNWAY_VIDEO_RATIO
    RUNWAY_VIDEO_DURATION
    VIDEO_OUTPUT_DIR
    REQUEST_TIMEOUT
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURATION
# ============================================================

RUNWAY_API_URL = (
    "https://api.dev.runwayml.com"
)

RUNWAY_API_VERSION = (
    "2024-11-06"
)

DEFAULT_MODEL = os.getenv(
    "RUNWAY_MODEL",
    "gen4.5",
)

DEFAULT_RATIO = os.getenv(
    "RUNWAY_VIDEO_RATIO",
    "1280:720",
)

DEFAULT_DURATION = int(
    os.getenv(
        "RUNWAY_VIDEO_DURATION",
        "5",
    )
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


# ============================================================
# EXCEPTION
# ============================================================


class RunwayVideoError(Exception):
    """Raised when a Runway video operation fails."""


# ============================================================
# PROVIDER
# ============================================================


class RunwayVideoProvider:
    """
    Runway text-to-video provider.

    Multiple API keys are supported.

    Key order:
        RUNWAY_API_KEY_1
        RUNWAY_API_KEY_2
        RUNWAY_API_KEY_3

    The provider automatically tries the next key when
    the current key fails.
    """

    name = "runway"

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
    # API KEY MANAGEMENT
    # ========================================================

    @staticmethod
    def _load_api_keys() -> List[str]:
        """
        Load Runway API keys from environment variables.
        """

        keys = []

        for name in (
            "RUNWAY_API_KEY_1",
            "RUNWAY_API_KEY_2",
            "RUNWAY_API_KEY_3",
        ):

            value = os.getenv(
                name,
                "",
            ).strip()

            if value:
                keys.append(value)

        # Backward compatibility.
        legacy_key = os.getenv(
            "RUNWAY_API_KEY",
            "",
        ).strip()

        if legacy_key and legacy_key not in keys:
            keys.append(legacy_key)

        # Runway official SDK convention.
        sdk_key = os.getenv(
            "RUNWAYML_API_SECRET",
            "",
        ).strip()

        if sdk_key and sdk_key not in keys:
            keys.append(sdk_key)

        return keys

    def refresh_api_keys(self) -> None:
        """Reload API keys from environment variables."""

        self.api_keys = self._load_api_keys()

    def is_configured(self) -> bool:
        """Return True when at least one API key exists."""

        self.refresh_api_keys()

        return bool(
            self.api_keys
        )

    def get_key_count(self) -> int:
        """Return number of configured Runway keys."""

        self.refresh_api_keys()

        return len(
            self.api_keys
        )

    # ========================================================
    # HTTP HELPERS
    # ========================================================

    def _headers(
        self,
        api_key: str,
    ) -> Dict[str, str]:

        return {
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
            "X-Runway-Version": (
                RUNWAY_API_VERSION
            ),
        }

    def _request_json(
        self,
        method: str,
        url: str,
        api_key: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        body = None

        if payload is not None:
            import json

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

                import json

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
                raw_error = (
                    error.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )
            except Exception:
                raw_error = str(
                    error
                )

            raise RunwayVideoError(
                f"Runway HTTP {error.code}: "
                f"{raw_error}"
            ) from error

        except URLError as error:

            raise RunwayVideoError(
                f"Runway connection failed: "
                f"{error}"
            ) from error

        except Exception as error:

            raise RunwayVideoError(
                f"Runway request failed: "
                f"{error}"
            ) from error

    # ========================================================
    # CREATE TASK
    # ========================================================

    def _create_task(
        self,
        api_key: str,
        prompt: str,
        model: str,
        ratio: str,
        duration: int,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:

        payload: Dict[str, Any] = {
            "model": model,
            "promptText": prompt,
            "ratio": ratio,
            "duration": duration,
        }

        if negative_prompt:
            payload[
                "negativePrompt"
            ] = negative_prompt

        if seed is not None:
            payload[
                "seed"
            ] = int(seed)

        return self._request_json(
            method="POST",
            url=(
                f"{RUNWAY_API_URL}"
                "/v1/text_to_video"
            ),
            api_key=api_key,
            payload=payload,
        )

    # ========================================================
    # TASK STATUS
    # ========================================================

    def _get_task(
        self,
        api_key: str,
        task_id: str,
    ) -> Dict[str, Any]:

        return self._request_json(
            method="GET",
            url=(
                f"{RUNWAY_API_URL}"
                f"/v1/tasks/{task_id}"
            ),
            api_key=api_key,
        )

    # ========================================================
    # POLLING
    # ========================================================

    def _wait_for_task(
        self,
        api_key: str,
        task_id: str,
    ) -> Dict[str, Any]:

        started_at = time.monotonic()

        while True:

            elapsed = (
                time.monotonic()
                - started_at
            )

            if elapsed > self.timeout:
                raise RunwayVideoError(
                    "Runway video generation "
                    "timed out."
                )

            task = self._get_task(
                api_key=api_key,
                task_id=task_id,
            )

            status = str(
                task.get(
                    "status",
                    "",
                )
            ).upper()

            if status in {
                "SUCCEEDED",
                "SUCCESS",
                "COMPLETED",
            }:
                return task

            if status in {
                "FAILED",
                "FAILURE",
                "CANCELLED",
                "CANCELED",
            }:

                failure_reason = (
                    task.get(
                        "failure",
                        task.get(
                            "error",
                            "Unknown Runway error.",
                        ),
                    )
                )

                raise RunwayVideoError(
                    f"Runway task failed: "
                    f"{failure_reason}"
                )

            time.sleep(
                self.poll_interval
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

            raise RunwayVideoError(
                f"Video download failed "
                f"with HTTP {error.code}."
            ) from error

        except URLError as error:

            raise RunwayVideoError(
                f"Video download connection "
                f"failed: {error}"
            ) from error

        except Exception as error:

            raise RunwayVideoError(
                f"Failed to save Runway "
                f"video: {error}"
            ) from error

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

        filename = (
            f"runway_"
            f"{int(time.time())}.mp4"
        )

        return (
            self.output_dir
            / filename
        )

    # ========================================================
    # EXTRACT OUTPUT URL
    # ========================================================

    @staticmethod
    def _extract_output_url(
        task: Dict[str, Any],
    ) -> Optional[str]:

        output = task.get(
            "output"
        )

        if isinstance(
            output,
            list,
        ):

            for item in output:

                if isinstance(
                    item,
                    str,
                ) and item.startswith(
                    "http"
                ):
                    return item

        if isinstance(
            output,
            str,
        ) and output.startswith(
            "http"
        ):
            return output

        return None

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
        ratio: Optional[str] = None,
        duration: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        prompt = str(
            prompt or ""
        ).strip()

        if not prompt:
            raise RunwayVideoError(
                "Video generation prompt "
                "is required."
            )

        self.refresh_api_keys()

        if not self.api_keys:
            raise RunwayVideoError(
                "No Runway API keys are "
                "configured."
            )

        selected_model = (
            model
            or self.model
        )

        selected_ratio = (
            ratio
            or DEFAULT_RATIO
        )

        selected_duration = (
            duration
            if duration is not None
            else DEFAULT_DURATION
        )

        selected_duration = int(
            selected_duration
        )

        if not (
            2
            <= selected_duration
            <= 10
        ):
            raise RunwayVideoError(
                "Runway duration must "
                "be between 2 and 10 seconds."
            )

        final_path = (
            self._resolve_output_path(
                output_path
            )
        )

        errors = []

        # ====================================================
        # KEY FALLBACK
        # ====================================================

        for index, api_key in enumerate(
            self.api_keys,
            start=1,
        ):

            try:

                task = self._create_task(
                    api_key=api_key,
                    prompt=prompt,
                    model=selected_model,
                    ratio=selected_ratio,
                    duration=selected_duration,
                    negative_prompt=negative_prompt,
                    seed=seed,
                )

                task_id = str(
                    task.get(
                        "id",
                        ""
                    )
                ).strip()

                if not task_id:
                    raise RunwayVideoError(
                        "Runway did not return "
                        "a task ID."
                    )

                completed_task = (
                    self._wait_for_task(
                        api_key=api_key,
                        task_id=task_id,
                    )
                )

                video_url = (
                    self._extract_output_url(
                        completed_task
                    )
                )

                if not video_url:
                    raise RunwayVideoError(
                        "Runway completed the "
                        "task but returned no "
                        "video URL."
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
                    "task_id": task_id,
                    "key_index": index,
                    "metadata": {
                        "prompt": prompt,
                        "ratio": selected_ratio,
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

                # Try next configured key.
                continue

        # ====================================================
        # ALL KEYS FAILED
        # ====================================================

        raise RunwayVideoError(
            "All configured Runway API keys "
            "failed. "
            f"Attempts: {errors}"
        )


# ============================================================
# GLOBAL PROVIDER
# ============================================================


runway_video_provider = (
    RunwayVideoProvider()
)


# ============================================================
# PUBLIC HELPERS
# ============================================================


def is_runway_video_configured() -> bool:
    """Check whether Runway has at least one API key."""

    return (
        runway_video_provider
        .is_configured()
    )


def get_runway_key_count() -> int:
    """Return configured Runway key count."""

    return (
        runway_video_provider
        .get_key_count()
    )


def generate_runway_video(
    prompt: str,
    *,
    output_path: Optional[
        str | Path
    ] = None,
    model: Optional[str] = None,
    ratio: Optional[str] = None,
    duration: Optional[int] = None,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Generate a video using Runway.
    """

    return (
        runway_video_provider.generate(
            prompt=prompt,
            output_path=output_path,
            model=model,
            ratio=ratio,
            duration=duration,
            negative_prompt=negative_prompt,
            seed=seed,
            **kwargs,
        )
    )
