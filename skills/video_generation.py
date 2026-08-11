from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VideoGenerationRequest:
    prompt: str
    duration: int = 5
    aspect_ratio: str = "16:9"
    style: str = "cinematic"
    image_input: Optional[Any] = None
    negative_prompt: str = ""
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class VideoGenerationResult:
    success: bool
    video_url: str = ""
    provider: str = ""
    job_id: str = ""
    status: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


class VideoGenerationEngine:
    """
    Provider-independent AI video generation engine.

    Supports:
        - Text-to-video
        - Image-to-video
        - Cinematic video prompts
        - Duration
        - Aspect ratio
        - Style
        - Negative prompts

    Actual AI video providers can be connected later.
    """

    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self.default_provider = ""

    def register_provider(
        self,
        name: str,
        provider,
    ):
        name = str(
            name or ""
        ).strip()

        if not name:
            raise ValueError(
                "Provider name is required."
            )

        if provider is None:
            raise ValueError(
                "Provider is required."
            )

        self._providers[name] = provider

        if not self.default_provider:
            self.default_provider = name

    def remove_provider(
        self,
        name: str,
    ) -> bool:

        name = str(
            name or ""
        ).strip()

        if name not in self._providers:
            return False

        del self._providers[name]

        if self.default_provider == name:
            self.default_provider = (
                next(
                    iter(self._providers),
                    "",
                )
            )

        return True

    def get_provider(
        self,
        name: Optional[str] = None,
    ):

        provider_name = (
            str(name).strip()
            if name
            else self.default_provider
        )

        if not provider_name:
            return None

        return self._providers.get(
            provider_name
        )

    def get_providers(
        self,
    ) -> List[str]:

        return sorted(
            self._providers.keys()
        )

    def set_default_provider(
        self,
        name: str,
    ) -> bool:

        name = str(
            name or ""
        ).strip()

        if name not in self._providers:
            return False

        self.default_provider = name

        return True

    def validate_request(
        self,
        request: VideoGenerationRequest,
    ) -> None:

        prompt = str(
            request.prompt or ""
        ).strip()

        if not prompt:
            raise ValueError(
                "Video prompt is required."
            )

        duration = int(
            request.duration
        )

        if duration < 1:
            raise ValueError(
                "Video duration must be at least 1 second."
            )

        if duration > 300:
            raise ValueError(
                "Video duration cannot exceed 300 seconds."
            )

        allowed_ratios = {
            "16:9",
            "9:16",
            "1:1",
            "4:5",
            "4:3",
            "3:4",
        }

        if request.aspect_ratio not in allowed_ratios:
            raise ValueError(
                "Unsupported aspect ratio: "
                f"{request.aspect_ratio}"
            )

    def _call_provider(
        self,
        provider,
        request: VideoGenerationRequest,
    ) -> VideoGenerationResult:

        if hasattr(
            provider,
            "generate_video",
        ):
            result = provider.generate_video(
                request=request
            )

        elif callable(provider):
            result = provider(
                request=request
            )

        else:
            raise TypeError(
                "Video provider must expose "
                "'generate_video()' or be callable."
            )

        if isinstance(
            result,
            VideoGenerationResult,
        ):
            return result

        if isinstance(
            result,
            dict,
        ):
            return VideoGenerationResult(
                success=bool(
                    result.get(
                        "success",
                        False,
                    )
                ),
                video_url=str(
                    result.get(
                        "video_url",
                        "",
                    )
                    or ""
                ),
                provider=str(
                    result.get(
                        "provider",
                        "",
                    )
                    or ""
                ),
                job_id=str(
                    result.get(
                        "job_id",
                        "",
                    )
                    or ""
                ),
                status=str(
                    result.get(
                        "status",
                        "",
                    )
                    or ""
                ),
                error=str(
                    result.get(
                        "error",
                        "",
                    )
                    or ""
                ),
                metadata=result.get(
                    "metadata",
                    {},
                )
                or {},
            )

        raise TypeError(
            "Video provider returned an "
            "unsupported result."
        )

    def generate(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        style: str = "cinematic",
        image_input: Optional[Any] = None,
        negative_prompt: str = "",
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VideoGenerationResult:

        request = VideoGenerationRequest(
            prompt=str(
                prompt or ""
            ).strip(),
            duration=int(duration),
            aspect_ratio=str(
                aspect_ratio or "16:9"
            ).strip(),
            style=str(
                style or "cinematic"
            ).strip(),
            image_input=image_input,
            negative_prompt=str(
                negative_prompt or ""
            ).strip(),
            metadata=metadata or {},
        )

        self.validate_request(
            request
        )

        provider_name = (
            str(provider).strip()
            if provider
            else self.default_provider
        )

        selected_provider = (
            self._providers.get(
                provider_name
            )
            if provider_name
            else None
        )

        if selected_provider is None:
            return VideoGenerationResult(
                success=False,
                provider=provider_name,
                status="provider_unavailable",
                error=(
                    "No AI video provider is "
                    "currently configured."
                ),
                metadata={
                    "prompt": request.prompt,
                    "duration": request.duration,
                    "aspect_ratio": (
                        request.aspect_ratio
                    ),
                    "style": request.style,
                },
            )

        try:
            result = self._call_provider(
                selected_provider,
                request,
            )

            if not result.provider:
                result.provider = provider_name

            return result

        except Exception as error:
            return VideoGenerationResult(
                success=False,
                provider=provider_name,
                status="failed",
                error=str(error),
                metadata={
                    "prompt": request.prompt,
                    "duration": request.duration,
                    "aspect_ratio": (
                        request.aspect_ratio
                    ),
                    "style": request.style,
                },
            )


video_engine = VideoGenerationEngine()


def register_video_provider(
    name: str,
    provider,
):
    video_engine.register_provider(
        name=name,
        provider=provider,
    )


def remove_video_provider(
    name: str,
) -> bool:

    return video_engine.remove_provider(
        name
    )


def get_video_providers() -> List[str]:

    return video_engine.get_providers()


def set_default_video_provider(
    name: str,
) -> bool:

    return video_engine.set_default_provider(
        name
    )


def generate_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    style: str = "cinematic",
    image_input: Optional[Any] = None,
    negative_prompt: str = "",
    provider: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> VideoGenerationResult:

    return video_engine.generate(
        prompt=prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
        style=style,
        image_input=image_input,
        negative_prompt=negative_prompt,
        provider=provider,
        metadata=metadata,
    )
