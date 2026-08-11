"""
Kling AI Video Provider.

Supports:
- Text to Video
- Image to Video
- Kling V3
- Multiple API keys
- Automatic key fallback
- Automatic task polling
- 16:9 / 9:16 / 1:1
- 3-15 second duration
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


# ============================================================
# CONSTANTS
# ============================================================

PROVIDER_NAME = "kling"

API_BASE_URL = "https://api-singapore.klingai.com"

TEXT_TO_VIDEO_URL = (
    f"{API_BASE_URL}/v1/videos/text2video"
)

IMAGE_TO_VIDEO_URL = (
    f"{API_BASE_URL}/v1/videos/image2video"
)


# ============================================================
# ENVIRONMENT HELPERS
# ============================================================

def _env(name: str, default: str = "") -> str:
    return os.getenv(
        name,
        default,
    ).strip()


def _load_api_keys() -> list[str]:
    """
    Load Kling keys from all supported Render names.

    Supported:
    KLING_API_KEY
    KLING_API_KEY_1
    KLING_API_KEY_2
    KLING_API_KEY_3
    """

    names = (
        "KLING_API_KEY",
        "KLING_API_KEY_1",
        "KLING_API_KEY_2",
        "KLING_API_KEY_3",
    )

    keys: list[str] = []

    for name in names:

        value = _env(name)

        if value and value not in keys:
            keys.append(value)

    return keys


# ============================================================
# PROVIDER
# ============================================================

class KlingVideoProvider:
    """
    Production Kling AI video provider.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_key_2: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[float] = None,
    ) -> None:

        keys = _load_api_keys()

        manual_keys = [
            api_key,
            api_key_2,
        ]

        for key in manual_keys:

            if key and str(key).strip():

                clean_key = str(
                    key
                ).strip()

                if clean_key not in keys:
                    keys.insert(
                        0,
                        clean_key,
                    )

        self.api_keys = keys

        self.model = (
            model
            or _env(
                "KLING_VIDEO_MODEL",
                "kling-v3",
            )
            or "kling-v3"
        )

        if self.model == "kling":
            self.model = "kling-v3"

        self.timeout = max(
            30,
            int(
                timeout
                or _env(
                    "VIDEO_REQUEST_TIMEOUT",
                    "300",
                )
            ),
        )

        self.poll_interval = max(
            1.0,
            float(
                poll_interval
                or _env(
                    "VIDEO_POLL_INTERVAL",
                    "3",
                )
            ),
        )

        self.default_duration = int(
            _env(
                "VIDEO_DEFAULT_DURATION",
                "5",
            )
        )

        self.default_aspect_ratio = _env(
            "VIDEO_DEFAULT_ASPECT_RATIO",
            "16:9",
        )

        self.session = requests.Session()

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def is_configured(self) -> bool:
        """
        Return True when at least one API key exists.
        """

        return bool(
            self.api_keys
        )

    # ========================================================
    # INFO
    # ========================================================

    def get_provider_info(
        self,
    ) -> Dict[str, Any]:

        return {
            "provider": PROVIDER_NAME,
            "model": self.model,
            "configured": self.is_configured(),
            "api_key_count": len(
                self.api_keys
            ),
            "api_base_url": API_BASE_URL,
            "supports_text_to_video": True,
            "supports_image_to_video": True,
            "supports_multi_shot": True,
        }

    # ========================================================
    # HEADERS
    # ========================================================

    @staticmethod
    def _headers(
        api_key: str,
    ) -> Dict[str, str]:

        return {
            "Authorization": (
                f"Bearer {api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
            "Accept": (
                "application/json"
            ),
        }

    # ========================================================
    # HTTP
    # ========================================================

    def _request(
        self,
        method: str,
        url: str,
        api_key: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        response = self.session.request(
            method=method,
            url=url,
            headers=self._headers(
                api_key
            ),
            timeout=60,
            **kwargs,
        )

        try:
            data = response.json()

        except Exception:
            data = {
                "code": response.status_code,
                "message": response.text,
            }

        if response.status_code >= 400:

            raise RuntimeError(
                "Kling HTTP "
                f"{response.status_code}: "
                f"{data}"
            )

        if not isinstance(
            data,
            dict,
        ):

            raise RuntimeError(
                "Kling returned an invalid response."
            )

        code = data.get(
            "code",
            0,
        )

        if str(code) not in {
            "0",
            "None",
        }:

            raise RuntimeError(
                "Kling API error: "
                f"{data.get('message', data)}"
            )

        return data

    # ========================================================
    # PAYLOAD
    # ========================================================

    def _build_payload(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        mode: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        sound: Optional[str] = None,
        image: Optional[str] = None,
        image_tail: Optional[str] = None,
        multi_shot: bool = False,
        multi_prompt: Optional[list] = None,
        shot_type: Optional[str] = None,
    ) -> Dict[str, Any]:

        selected_model = (
            model
            or self.model
        )

        if selected_model == "kling":
            selected_model = "kling-v3"

        selected_duration = int(
            duration
            or self.default_duration
            or 5
        )

        selected_duration = max(
            3,
            min(
                selected_duration,
                15,
            ),
        )

        selected_ratio = (
            aspect_ratio
            or self.default_aspect_ratio
            or "16:9"
        )

        if selected_ratio not in {
            "16:9",
            "9:16",
            "1:1",
        }:

            selected_ratio = "16:9"

        selected_mode = (
            mode
            or "pro"
        )

        if selected_mode not in {
            "std",
            "pro",
            "4k",
        }:

            selected_mode = "pro"

        payload: Dict[str, Any] = {
            "model_name": selected_model,
            "prompt": prompt,
            "duration": str(
                selected_duration
            ),
            "mode": selected_mode,
            "aspect_ratio": selected_ratio,
        }

        if negative_prompt:
            payload[
                "negative_prompt"
            ] = str(
                negative_prompt
            )

        if sound in {
            "on",
            "off",
        }:

            payload[
                "sound"
            ] = sound

        if image:
            payload[
                "image"
            ] = image

        if image_tail:
            payload[
                "image_tail"
            ] = image_tail

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

            if multi_prompt:
                payload[
                    "multi_prompt"
                ] = multi_prompt

        return payload

    # ========================================================
    # CREATE TASK
    # ========================================================

    def _create_task(
        self,
        payload: Dict[str, Any],
        *,
        image_mode: bool = False,
    ) -> Dict[str, Any]:

        url = (
            IMAGE_TO_VIDEO_URL
            if image_mode
            else TEXT_TO_VIDEO_URL
        )

        last_error: Optional[
            Exception
        ] = None

        for api_key in self.api_keys:

            try:

                return self._request(
                    "POST",
                    url,
                    api_key,
                    json=payload,
                )

            except Exception as error:

                last_error = error

                continue

        raise RuntimeError(
            "All configured Kling API keys failed. "
            f"Last error: {last_error}"
        )

    # ========================================================
    # TASK STATUS
    # ========================================================

    def _get_task(
        self,
        task_id: str,
    ) -> Dict[str, Any]:

        last_error: Optional[
            Exception
        ] = None

        for api_key in self.api_keys:

            try:

                return self._request(
                    "GET",
                    (
                        f"{TEXT_TO_VIDEO_URL}"
                        f"/{task_id}"
                    ),
                    api_key,
                )

            except Exception as error:

                last_error = error

        raise RuntimeError(
            "Failed to query Kling task. "
            f"Last error: {last_error}"
        )

    # ========================================================
    # POLLING
    # ========================================================

    def _wait_for_result(
        self,
        task_id: str,
    ) -> Dict[str, Any]:

        started = time.monotonic()

        while True:

            elapsed = (
                time.monotonic()
                - started
            )

            if elapsed >= self.timeout:

                raise TimeoutError(
                    "Kling video generation "
                    "timed out."
                )

            response = self._get_task(
                task_id
            )

            data = response.get(
                "data",
                {},
            )

            if not isinstance(
                data,
                dict,
            ):

                raise RuntimeError(
                    "Kling returned invalid task data."
                )

            status = str(
                data.get(
                    "task_status",
                    "",
                )
            ).lower()

            if status == "succeed":
                return response

            if status == "failed":

                message = data.get(
                    "task_status_msg",
                    "Kling task failed.",
                )

                raise RuntimeError(
                    str(message)
                )

            time.sleep(
                self.poll_interval
            )

    # ========================================================
    # VIDEO URL
    # ========================================================

    @staticmethod
    def _extract_video_url(
        response: Dict[str, Any],
    ) -> str:

        data = response.get(
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
            or ""
        )

    # ========================================================
    # GENERATE
    # ========================================================

    def generate_video(
        self,
        request: Any = None,
        *,
        prompt: Optional[str] = None,
        output_path: Optional[
            str | Path
        ] = None,
        model: Optional[str] = None,
        duration: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        mode: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        sound: Optional[str] = None,
        image: Optional[str] = None,
        image_tail: Optional[str] = None,
        multi_shot: bool = False,
        multi_prompt: Optional[list] = None,
        shot_type: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a Kling video.

        Accepts both:
        generate_video(prompt="...")
        and
        generate_video(request={...})
        """

        if request is not None:

            if isinstance(
                request,
                str,
            ):

                prompt = request

            elif isinstance(
                request,
                dict,
            ):

                prompt = (
                    request.get(
                        "prompt"
                    )
                    or prompt
                )

                model = (
                    request.get(
                        "model"
                    )
                    or request.get(
                        "model_name"
                    )
                    or model
                )

                duration = (
                    request.get(
                        "duration"
                    )
                    or duration
                )

                aspect_ratio = (
                    request.get(
                        "aspect_ratio"
                    )
                    or aspect_ratio
                )

                mode = (
                    request.get(
                        "mode"
                    )
                    or mode
                )

                negative_prompt = (
                    request.get(
                        "negative_prompt"
                    )
                    or negative_prompt
                )

                sound = (
                    request.get(
                        "sound"
                    )
                    or sound
                )

                image = (
                    request.get(
                        "image"
                    )
                    or request.get(
                        "image_input"
                    )
                    or image
                )

                image_tail = (
                    request.get(
                        "image_tail"
                    )
                    or image_tail
                )

                multi_shot = bool(
                    request.get(
                        "multi_shot",
                        multi_shot,
                    )
                )

                multi_prompt = (
                    request.get(
                        "multi_prompt"
                    )
                    or multi_prompt
                )

                shot_type = (
                    request.get(
                        "shot_type"
                    )
                    or shot_type
                )

        prompt = str(
            prompt or ""
        ).strip()

        image = (
            str(image).strip()
            if image
            else None
        )

        if not prompt and not image:

            return {
                "success": False,
                "provider": PROVIDER_NAME,
                "model": self.model,
                "error": (
                    "Kling requires a prompt "
                    "or image."
                ),
            }

        if not self.is_configured():

            return {
                "success": False,
                "provider": PROVIDER_NAME,
                "model": self.model,
                "error": (
                    "Kling API key is not configured. "
                    "Use KLING_API_KEY or "
                    "KLING_API_KEY_1."
                ),
            }

        try:

            payload = self._build_payload(
                prompt,
                model=model,
                duration=duration,
                aspect_ratio=aspect_ratio,
                mode=mode,
                negative_prompt=negative_prompt,
                sound=sound,
                image=image,
                image_tail=image_tail,
                multi_shot=multi_shot,
                multi_prompt=multi_prompt,
                shot_type=shot_type,
            )

            create_response = (
                self._create_task(
                    payload,
                    image_mode=bool(image),
                )
            )

            data = create_response.get(
                "data",
                {},
            )

            task_id = str(
                data.get(
                    "task_id",
                    "",
                )
            )

            if not task_id:

                raise RuntimeError(
                    "Kling did not return a task ID."
                )

            final_response = (
                self._wait_for_result(
                    task_id
                )
            )

            video_url = (
                self._extract_video_url(
                    final_response
                )
            )

            if not video_url:

                raise RuntimeError(
                    "Kling completed the task "
                    "but returned no video URL."
                )

            result = {
                "success": True,
                "provider": PROVIDER_NAME,
                "model": self.model,
                "video_url": video_url,
                "task_id": task_id,
                "job_id": task_id,
                "status": "succeed",
                "output_path": (
                    str(output_path)
                    if output_path
                    else None
                ),
                "metadata": {
                    "task_id": task_id,
                    "model": payload.get(
                        "model_name"
                    ),
                    "duration": payload.get(
                        "duration"
                    ),
                    "aspect_ratio": payload.get(
                        "aspect_ratio"
                    ),
                    "mode": payload.get(
                        "mode"
                    ),
                    "sound": payload.get(
                        "sound"
                    ),
                },
            }

            return result

        except Exception as error:

            return {
                "success": False,
                "provider": PROVIDER_NAME,
                "model": self.model,
                "video_url": "",
                "task_id": "",
                "status": "failed",
                "error": str(error),
            }


# ============================================================
# GLOBAL PROVIDER
# ============================================================

kling = KlingVideoProvider()


# ============================================================
# PUBLIC HELPERS
# ============================================================

def is_configured() -> bool:
    return kling.is_configured()


def get_provider_info() -> Dict[str, Any]:
    return kling.get_provider_info()


def generate_video(
    prompt: str = "",
    *,
    request: Any = None,
    **kwargs: Any,
) -> Dict[str, Any]:

    if request is not None:

        return kling.generate_video(
            request=request,
            **kwargs,
        )

    return kling.generate_video(
        prompt=prompt,
        **kwargs,
    )


__all__ = [
    "KlingVideoProvider",
    "kling",
    "is_configured",
    "get_provider_info",
    "generate_video",
]
