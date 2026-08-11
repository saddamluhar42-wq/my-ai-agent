"""
Kling AI video generation provider.

Supports:
- Text to Video
- Image to Video
- kling-v3
- Automatic task polling
- Multiple API-key fallback
- 16:9 / 9:16 / 1:1
- Kling multi-shot generation
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

import requests

from config import (
    KLING_API_KEY,
    KLING_API_KEY_2,
    KLING_VIDEO_MODEL,
    VIDEO_DEFAULT_DURATION,
    VIDEO_POLL_INTERVAL,
    VIDEO_REQUEST_TIMEOUT,
)


PROVIDER_NAME = "kling"

API_BASE_URL = (
    "https://api-singapore.klingai.com"
)

TEXT_TO_VIDEO_URL = (
    f"{API_BASE_URL}/v1/videos/text2video"
)

IMAGE_TO_VIDEO_URL = (
    f"{API_BASE_URL}/v1/videos/image2video"
)


class KlingVideoProvider:
    """
    Kling AI video provider.

    The provider returns dictionaries that are normalized
    by VideoGenerationManager into VideoGenerationResult.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_key_2: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[float] = None,
    ) -> None:

        self.api_keys = [
            key.strip()
            for key in [
                api_key or KLING_API_KEY,
                api_key_2 or KLING_API_KEY_2,
            ]
            if key and str(key).strip()
        ]

        configured_model = (
            model
            or KLING_VIDEO_MODEL
            or "kling-v3"
        )

        if configured_model == "kling":
            configured_model = "kling-v3"

        self.model = configured_model

        self.timeout = max(
            30,
            int(
                timeout
                or VIDEO_REQUEST_TIMEOUT
                or 300
            ),
        )

        self.poll_interval = max(
            1.0,
            float(
                poll_interval
                or VIDEO_POLL_INTERVAL
                or 3
            ),
        )

        self.session = requests.Session()

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def is_configured(self) -> bool:
        """Return True when at least one Kling API key exists."""

        return bool(self.api_keys)

    # ========================================================
    # PROVIDER INFORMATION
    # ========================================================

    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider metadata."""

        return {
            "provider": PROVIDER_NAME,
            "model": self.model,
            "configured": self.is_configured(),
            "api_key_count": len(self.api_keys),
            "api_base_url": API_BASE_URL,
            "supports_text_to_video": True,
            "supports_image_to_video": True,
            "supports_multi_shot": True,
        }

    # ========================================================
    # HEADERS
    # ========================================================

    def _headers(
        self,
        api_key: str,
    ) -> Dict[str, str]:

        return {
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ========================================================
    # REQUEST
    # ========================================================

    def _request(
        self,
        method: str,
        url: str,
        api_key: str,
        **kwargs: Any,
    ) -> requests.Response:

        response = self.session.request(
            method=method,
            url=url,
            headers=self._headers(api_key),
            timeout=self.timeout,
            **kwargs,
        )

        if response.status_code >= 400:

            try:
                body = response.json()

            except ValueError:
                body = response.text

            raise RuntimeError(
                "Kling API HTTP error "
                f"{response.status_code}: "
                f"{body}"
            )

        return response

    # ========================================================
    # RESPONSE VALIDATION
    # ========================================================

    @staticmethod
    def _parse_response(
        response: requests.Response,
    ) -> Dict[str, Any]:

        try:
            payload = response.json()

        except ValueError as error:
            raise RuntimeError(
                "Kling returned an invalid JSON response."
            ) from error

        if not isinstance(payload, dict):
            raise RuntimeError(
                "Kling returned an invalid response object."
            )

        code = payload.get("code")

        if code not in (
            None,
            0,
            "0",
        ):

            message = payload.get(
                "message",
                "Unknown Kling API error.",
            )

            raise RuntimeError(
                f"Kling API error {code}: {message}"
            )

        return payload

    # ========================================================
    # NORMALIZATION HELPERS
    # ========================================================

    @staticmethod
    def _get_request_value(
        request: Any,
        name: str,
        default: Any = None,
    ) -> Any:

        if request is None:
            return default

        if isinstance(request, dict):
            return request.get(
                name,
                default,
            )

        return getattr(
            request,
            name,
            default,
        )

    @staticmethod
    def _clean_optional(
        value: Any,
    ) -> Any:

        if value is None:
            return None

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return None

        return value

    @staticmethod
    def _normalize_duration(
        value: Any,
    ) -> str:

        if value is None:
            value = VIDEO_DEFAULT_DURATION

        try:
            duration = int(value)

        except (
            TypeError,
            ValueError,
        ):
            duration = int(
                VIDEO_DEFAULT_DURATION
            )

        duration = max(
            3,
            min(
                duration,
                15,
            ),
        )

        return str(duration)

    @staticmethod
    def _normalize_ratio(
        value: Any,
    ) -> str:

        ratio = str(
            value
            or "16:9"
        ).strip()

        allowed = {
            "16:9",
            "9:16",
            "1:1",
        }

        if ratio not in allowed:
            ratio = "16:9"

        return ratio

    # ========================================================
    # PAYLOAD BUILDER
    # ========================================================

    def _build_payload(
        self,
        request: Any,
        image_input: Optional[str] = None,
    ) -> Dict[str, Any]:

        prompt = str(
            self._get_request_value(
                request,
                "prompt",
                "",
            )
            or ""
        ).strip()

        negative_prompt = self._clean_optional(
            self._get_request_value(
                request,
                "negative_prompt",
                None,
            )
        )

        duration = self._normalize_duration(
            self._get_request_value(
                request,
                "duration",
                VIDEO_DEFAULT_DURATION,
            )
        )

        aspect_ratio = self._normalize_ratio(
            self._get_request_value(
                request,
                "aspect_ratio",
                "16:9",
            )
        )

        model = str(
            self._get_request_value(
                request,
                "model",
                self.model,
            )
            or self.model
        ).strip()

        if model == "kling":
            model = "kling-v3"

        mode = str(
            self._get_request_value(
                request,
                "mode",
                "std",
            )
            or "std"
        ).strip()

        if mode not in {
            "std",
            "pro",
            "4k",
        }:
            mode = "std"

        sound = str(
            self._get_request_value(
                request,
                "sound",
                "off",
            )
            or "off"
        ).strip().lower()

        if sound not in {
            "on",
            "off",
        }:
            sound = "off"

        payload: Dict[str, Any] = {
            "model_name": model,
            "prompt": prompt,
            "duration": duration,
            "mode": mode,
            "sound": sound,
            "aspect_ratio": aspect_ratio,
        }

        if negative_prompt is not None:
            payload[
                "negative_prompt"
            ] = negative_prompt

        cfg_scale = self._get_request_value(
            request,
            "cfg_scale",
            None,
        )

        if cfg_scale is not None:

            try:
                cfg_scale = float(
                    cfg_scale
                )

                cfg_scale = max(
                    0.0,
                    min(
                        cfg_scale,
                        1.0,
                    ),
                )

                payload[
                    "cfg_scale"
                ] = cfg_scale

            except (
                TypeError,
                ValueError,
            ):
                pass

        callback_url = self._clean_optional(
            self._get_request_value(
                request,
                "callback_url",
                None,
            )
        )

        if callback_url:
            payload[
                "callback_url"
            ] = callback_url

        external_task_id = (
            self._get_request_value(
                request,
                "external_task_id",
                None,
            )
        )

        if not external_task_id:
            external_task_id = (
                f"my-ai-agent-"
                f"{uuid.uuid4().hex}"
            )

        payload[
            "external_task_id"
        ] = str(
            external_task_id
        )

        multi_shot = bool(
            self._get_request_value(
                request,
                "multi_shot",
                False,
            )
        )

        multi_prompt = self._get_request_value(
            request,
            "multi_prompt",
            None,
        )

        shot_type = self._get_request_value(
            request,
            "shot_type",
            None,
        )

        if multi_shot:

            payload[
                "multi_shot"
            ] = True

            if shot_type in {
                "customize",
                "intelligence",
            }:
                payload[
                    "shot_type"
                ] = shot_type

            if isinstance(
                multi_prompt,
                list,
            ) and multi_prompt:

                payload[
                    "multi_prompt"
                ] = multi_prompt

            # Kling documentation states that when
            # multi_shot=true the normal prompt is invalid.
            payload.pop(
                "prompt",
                None,
            )

        camera_control = (
            self._get_request_value(
                request,
                "camera_control",
                None,
            )
        )

        if isinstance(
            camera_control,
            dict,
        ):
            payload[
                "camera_control"
            ] = camera_control

        if image_input:
            payload[
                "image"
            ] = image_input

        return payload

    # ========================================================
    # CREATE TASK
    # ========================================================

    def _create_task(
        self,
        payload: Dict[str, Any],
        image_input: Optional[str] = None,
    ) -> Dict[str, Any]:

        endpoint = (
            IMAGE_TO_VIDEO_URL
            if image_input
            else TEXT_TO_VIDEO_URL
        )

        errors = []

        for api_key in self.api_keys:

            try:

                response = self._request(
                    "POST",
                    endpoint,
                    api_key,
                    json=payload,
                )

                return self._parse_response(
                    response
                )

            except Exception as error:

                errors.append(
                    str(error)
                )

        raise RuntimeError(
            "Kling task creation failed. "
            + " | ".join(errors)
        )

    # ========================================================
    # TASK STATUS
    # ========================================================

    def _get_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:

        endpoint = (
            f"{TEXT_TO_VIDEO_URL}/"
            f"{task_id}"
        )

        errors = []

        for api_key in self.api_keys:

            try:

                response = self._request(
                    "GET",
                    endpoint,
                    api_key,
                )

                return self._parse_response(
                    response
                )

            except Exception as error:

                errors.append(
                    str(error)
                )

        raise RuntimeError(
            "Kling task status request failed. "
            + " | ".join(errors)
        )

    # ========================================================
    # RESULT URL
    # ========================================================

    @staticmethod
    def _extract_video_url(
        payload: Dict[str, Any],
    ) -> str:

        data = payload.get(
            "data",
            {},
        )

        if not isinstance(
            data,
            dict,
        ):
            return ""

        task_result = data.get(
            "task_result",
            {},
        )

        if not isinstance(
            task_result,
            dict,
        ):
            return ""

        videos = task_result.get(
            "videos",
            [],
        )

        if not isinstance(
            videos,
            list,
        ) or not videos:

            return ""

        first = videos[0]

        if not isinstance(
            first,
            dict,
        ):
            return ""

        return str(
            first.get(
                "url",
                "",
            )
            or first.get(
                "watermark_url",
                "",
            )
            or ""
        )

    # ========================================================
    # POLLING
    # ========================================================

    def _wait_for_result(
        self,
        task_id: str,
    ) -> Dict[str, Any]:

        started_at = time.monotonic()

        last_payload: Dict[str, Any] = {}

        while True:

            elapsed = (
                time.monotonic()
                - started_at
            )

            if elapsed >= self.timeout:

                raise TimeoutError(
                    "Kling video generation "
                    "timed out."
                )

            payload = self._get_task(
                task_id
            )

            last_payload = payload

            data = payload.get(
                "data",
                {},
            )

            if not isinstance(
                data,
                dict,
            ):
                raise RuntimeError(
                    "Kling returned invalid "
                    "task status data."
                )

            status = str(
                data.get(
                    "task_status",
                    "",
                )
                or ""
            ).lower()

            if status == "succeed":

                video_url = (
                    self._extract_video_url(
                        payload
                    )
                )

                if not video_url:

                    raise RuntimeError(
                        "Kling task succeeded "
                        "but returned no video URL."
                    )

                return payload

            if status == "failed":

                message = str(
                    data.get(
                        "task_status_msg",
                        "",
                    )
                    or payload.get(
                        "message",
                        "Kling generation failed.",
                    )
                )

                raise RuntimeError(
                    message
                )

            time.sleep(
                self.poll_interval
            )

    # ========================================================
    # PUBLIC GENERATION
    # ========================================================

    def generate_video(
        self,
        request: Any,
    ) -> Dict[str, Any]:
        """
        Generate a Kling video.

        Automatically chooses:
        - Image to Video when request.image_input exists
        - Text to Video otherwise
        """

        if not self.is_configured():

            return {
                "success": False,
                "video_url": "",
                "provider": PROVIDER_NAME,
                "job_id": "",
                "status": "not_configured",
                "error": (
                    "Kling API key is not configured."
                ),
                "metadata": {},
            }

        prompt = str(
            self._get_request_value(
                request,
                "prompt",
                "",
            )
            or ""
        ).strip()

        image_input = (
            self._get_request_value(
                request,
                "image_input",
                None,
            )
        )

        if not prompt and not image_input:

            return {
                "success": False,
                "video_url": "",
                "provider": PROVIDER_NAME,
                "job_id": "",
                "status": "invalid_request",
                "error": (
                    "Kling requires a prompt "
                    "or image input."
                ),
                "metadata": {},
            }

        image_input = (
            str(image_input).strip()
            if image_input
            else None
        )

        try:

            payload = self._build_payload(
                request=request,
                image_input=image_input,
            )

            create_response = (
                self._create_task(
                    payload=payload,
                    image_input=image_input,
                )
            )

            data = create_response.get(
                "data",
                {},
            )

            if not isinstance(
                data,
                dict,
            ):
                raise RuntimeError(
                    "Kling did not return task data."
                )

            task_id = str(
                data.get(
                    "task_id",
                    "",
                )
                or ""
            )

            if not task_id:

                raise RuntimeError(
                    "Kling did not return a task ID."
                )

            final_response = (
                self._wait_for_result(
                    task_id=task_id
                )
            )

            video_url = (
                self._extract_video_url(
                    final_response
                )
            )

            final_data = final_response.get(
                "data",
                {},
            )

            return {
                "success": True,
                "video_url": video_url,
                "provider": PROVIDER_NAME,
                "job_id": task_id,
                "status": "succeed",
                "error": "",
                "metadata": {
                    "model": self.model,
                    "task_id": task_id,
                    "mode": payload.get(
                        "mode"
                    ),
                    "duration": payload.get(
                        "duration"
                    ),
                    "aspect_ratio": payload.get(
                        "aspect_ratio"
                    ),
                    "sound": payload.get(
                        "sound"
                    ),
                    "task_status": (
                        final_data.get(
                            "task_status"
                        )
                        if isinstance(
                            final_data,
                            dict,
                        )
                        else None
                    ),
                    "raw_response": (
                        final_response
                    ),
                },
            }

        except Exception as error:

            return {
                "success": False,
                "video_url": "",
                "provider": PROVIDER_NAME,
                "job_id": "",
                "status": "failed",
                "error": str(error),
                "metadata": {
                    "model": self.model,
                },
            }


# ============================================================
# MODULE-LEVEL PROVIDER
# ============================================================

kling = KlingVideoProvider()


# ============================================================
# PUBLIC HELPERS
# ============================================================

def is_configured() -> bool:
    """Return whether Kling is configured."""

    return kling.is_configured()


def get_provider_info() -> Dict[str, Any]:
    """Return Kling provider information."""

    return kling.get_provider_info()


def generate_video(
    request: Any,
) -> Dict[str, Any]:
    """Generate a video using the shared Kling provider."""

    return kling.generate_video(
        request=request
    )


__all__ = [
    "KlingVideoProvider",
    "kling",
    "is_configured",
    "get_provider_info",
    "generate_video",
]
