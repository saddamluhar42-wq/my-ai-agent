"""
Replicate video generation provider.

Supports:
- Replicate API token authentication
- Official model predictions
- Custom model/version predictions
- Async prediction polling
- Video URL/file download
- Configurable model and input parameters
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# CONFIGURATION
# ============================================================

REPLICATE_API_URL = (
    "https://api.replicate.com/v1"
)

DEFAULT_MODEL = os.getenv(
    "REPLICATE_VIDEO_MODEL",
    "minimax/video-01",
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

DEFAULT_POLL_INTERVAL = 3


# ============================================================
# EXCEPTION
# ============================================================


class ReplicateVideoError(Exception):
    """Raised when Replicate video generation fails."""


# ============================================================
# PROVIDER
# ============================================================


class ReplicateVideoProvider:
    """
    Replicate video generation provider.

    Required environment variable:

        REPLICATE_API_TOKEN

    Optional:

        REPLICATE_VIDEO_MODEL
        VIDEO_OUTPUT_DIR
        REQUEST_TIMEOUT
    """

    name = "replicate"

    def __init__(
        self,
        token: Optional[str] = None,
        model: Optional[str] = None,
        output_dir: Optional[str | Path] = None,
        timeout: Optional[int] = None,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:

        self.token = (
            token
            or os.getenv(
                "REPLICATE_API_TOKEN",
                "",
            )
        ).strip()

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
    # CONFIGURATION
    # ========================================================

    def refresh_token(self) -> None:
        """
        Reload token from environment.
        """

        environment_token = os.getenv(
            "REPLICATE_API_TOKEN",
            "",
        ).strip()

        if environment_token:
            self.token = environment_token

    def is_configured(self) -> bool:
        """
        Check whether Replicate is configured.
        """

        self.refresh_token()

        return bool(
            self.token
        )

    # ========================================================
    # HEADERS
    # ========================================================

    def _headers(
        self,
    ) -> Dict[str, str]:

        if not self.token:
            raise ReplicateVideoError(
                "REPLICATE_API_TOKEN is not configured."
            )

        return {
            "Authorization": (
                f"Bearer {self.token}"
            ),
            "Content-Type": (
                "application/json"
            ),
        }

    # ========================================================
    # HTTP REQUEST
    # ========================================================

    def _request_json(
        self,
        method: str,
        url: str,
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
            headers=self._headers(),
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

            raise ReplicateVideoError(
                f"Replicate HTTP {error.code}: "
                f"{details}"
            ) from error

        except URLError as error:

            raise ReplicateVideoError(
                "Replicate connection failed: "
                f"{error}"
            ) from error

        except Exception as error:

            raise ReplicateVideoError(
                "Replicate request failed: "
                f"{error}"
            ) from error

    # ========================================================
    # CREATE PREDICTION
    # ========================================================

    def _create_prediction(
        self,
        model: str,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:

        model = str(
            model or ""
        ).strip()

        if not model:
            raise ReplicateVideoError(
                "Replicate model is required."
            )

        parts = model.split(
            "/"
        )

        if len(parts) != 2:
            raise ReplicateVideoError(
                "Replicate model must use "
                "owner/model format, for example "
                "'minimax/video-01'."
            )

        owner, model_name = parts

        url = (
            f"{REPLICATE_API_URL}"
            f"/models/"
            f"{owner}/"
            f"{model_name}/predictions"
        )

        payload = {
            "input": inputs
        }

        return self._request_json(
            method="POST",
            url=url,
            payload=payload,
        )

    # ========================================================
    # GET PREDICTION
    # ========================================================

    def _get_prediction(
        self,
        prediction_id: str,
    ) -> Dict[str, Any]:

        return self._request_json(
            method="GET",
            url=(
                f"{REPLICATE_API_URL}"
                f"/predictions/"
                f"{prediction_id}"
            ),
        )

    # ========================================================
    # POLLING
    # ========================================================

    def _wait_for_prediction(
        self,
        prediction_id: str,
    ) -> Dict[str, Any]:

        started_at = time.monotonic()

        terminal_success = {
            "succeeded",
        }

        terminal_failure = {
            "failed",
            "canceled",
            "cancelled",
        }

        while True:

            elapsed = (
                time.monotonic()
                - started_at
            )

            if elapsed > self.timeout:

                raise ReplicateVideoError(
                    "Replicate video generation "
                    "timed out."
                )

            prediction = (
                self._get_prediction(
                    prediction_id
                )
            )

            status = str(
                prediction.get(
                    "status",
                    "",
                )
            ).lower()

            if status in terminal_success:
                return prediction

            if status in terminal_failure:

                error = prediction.get(
                    "error"
                )

                raise ReplicateVideoError(
                    "Replicate prediction failed: "
                    f"{error or status}"
                )

            time.sleep(
                self.poll_interval
            )

    # ========================================================
    # OUTPUT URL
    # ========================================================

    @staticmethod
    def _extract_output_url(
        output: Any,
    ) -> Optional[str]:

        if isinstance(
            output,
            str,
        ):

            if output.startswith(
                "http"
            ):
                return output

            return None

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
                    item,
                    dict,
                ):

                    for key in (
                        "url",
                        "video",
                    ):

                        value = item.get(
                            key
                        )

                        if (
                            isinstance(
                                value,
                                str,
                            )
                            and value.startswith(
                                "http"
                            )
                        ):
                            return value

        if isinstance(
            output,
            dict,
        ):

            for key in (
                "url",
                "video",
                "video_url",
            ):

                value = output.get(
                    key
                )

                if (
                    isinstance(
                        value,
                        str,
                    )
                    and value.startswith(
                        "http"
                    )
                ):
                    return value

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
                f"replicate_"
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

            raise ReplicateVideoError(
                "Replicate video download "
                f"failed: HTTP {error.code}"
            ) from error

        except URLError as error:

            raise ReplicateVideoError(
                "Replicate video download "
                f"connection failed: {error}"
            ) from error

        except Exception as error:

            raise ReplicateVideoError(
                "Failed to save Replicate "
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
        input_params: Optional[
            Dict[str, Any]
        ] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        prompt = str(
            prompt or ""
        ).strip()

        if not prompt:
            raise ReplicateVideoError(
                "Video generation prompt "
                "is required."
            )

        self.refresh_token()

        if not self.token:
            raise ReplicateVideoError(
                "REPLICATE_API_TOKEN is not configured."
            )

        selected_model = (
            model
            or self.model
        )

        inputs: Dict[str, Any] = {
            "prompt": prompt,
        }

        if input_params:
            inputs.update(
                input_params
            )

        # Allow additional model-specific
        # parameters without hard-coding them.
        reserved = {
            "output_path",
            "model",
            "input_params",
        }

        for key, value in kwargs.items():

            if key not in reserved:
                inputs[key] = value

        prediction = (
            self._create_prediction(
                model=selected_model,
                inputs=inputs,
            )
        )

        prediction_id = str(
            prediction.get(
                "id",
                "",
            )
        ).strip()

        if not prediction_id:
            raise ReplicateVideoError(
                "Replicate did not return "
                "a prediction ID."
            )

        completed = (
            self._wait_for_prediction(
                prediction_id
            )
        )

        video_url = (
            self._extract_output_url(
                completed.get(
                    "output"
                )
            )
        )

        if not video_url:
            raise ReplicateVideoError(
                "Replicate prediction completed "
                "but returned no downloadable "
                "video URL."
            )

        final_path = (
            self._resolve_output_path(
                output_path
            )
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
            "prediction_id": (
                prediction_id
            ),
            "metadata": {
                "prompt": prompt,
            },
        }


# ============================================================
# GLOBAL PROVIDER
# ============================================================

replicate_video_provider = (
    ReplicateVideoProvider()
)


# ============================================================
# PUBLIC HELPERS
# ============================================================

def is_replicate_video_configured() -> bool:
    return (
        replicate_video_provider
        .is_configured()
    )


def generate_replicate_video(
    prompt: str,
    *,
    output_path: Optional[
        str | Path
    ] = None,
    model: Optional[str] = None,
    input_params: Optional[
        Dict[str, Any]
    ] = None,
    **kwargs: Any,
) -> Dict[str, Any]:

    return (
        replicate_video_provider.generate(
            prompt=prompt,
            output_path=output_path,
            model=model,
            input_params=input_params,
            **kwargs,
        )
    )
