"""
Central AI video generation manager.

Responsibilities:
- Register available video providers.
- Detect provider configuration.
- Select a preferred provider.
- Automatically fallback when a provider fails.
- Keep provider-specific implementation outside the manager.
- Return a common result structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ============================================================
# RESULT
# ============================================================


@dataclass
class VideoGenerationResult:
    """Standard result returned by the video manager."""

    success: bool

    provider: str = ""

    model: str = ""

    output_path: Optional[str] = None

    video_url: Optional[str] = None

    task_id: Optional[str] = None

    error: Optional[str] = None

    attempts: List[Dict[str, Any]] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a normal dictionary."""

        return {
            "success": self.success,
            "provider": self.provider,
            "model": self.model,
            "output_path": self.output_path,
            "video_url": self.video_url,
            "task_id": self.task_id,
            "error": self.error,
            "attempts": self.attempts,
            "metadata": self.metadata,
        }


# ============================================================
# PROVIDER ENTRY
# ============================================================


@dataclass
class VideoProviderEntry:
    """Internal provider registration record."""

    name: str

    provider: Any

    enabled: bool = True

    priority: int = 50

    generator: Optional[
        Callable[..., Dict[str, Any]]
    ] = None

    configured_checker: Optional[
        Callable[[], bool]
    ] = None


# ============================================================
# MANAGER
# ============================================================


class VideoGenerationManager:
    """Central manager for AI video generation."""

    def __init__(self) -> None:

        self._providers: Dict[
            str,
            VideoProviderEntry,
        ] = {}

        self._register_builtin_providers()

    # ========================================================
    # PROVIDER REGISTRATION
    # ========================================================

    def register_provider(
        self,
        name: str,
        provider: Any,
        *,
        generator: Optional[
            Callable[..., Dict[str, Any]]
        ] = None,
        configured_checker: Optional[
            Callable[[], bool]
        ] = None,
        priority: int = 50,
        enabled: bool = True,
    ) -> None:

        provider_name = str(
            name or ""
        ).strip().lower()

        if not provider_name:
            raise ValueError(
                "Video provider name is required."
            )

        if provider is None:
            raise ValueError(
                "Video provider instance is required."
            )

        if generator is None:

            for method_name in (
                "generate_video",
                "generate",
            ):

                possible_generator = getattr(
                    provider,
                    method_name,
                    None,
                )

                if callable(
                    possible_generator
                ):
                    generator = (
                        possible_generator
                    )
                    break

        if configured_checker is None:

            possible_checker = getattr(
                provider,
                "is_configured",
                None,
            )

            if callable(
                possible_checker
            ):
                configured_checker = (
                    possible_checker
                )

        self._providers[
            provider_name
        ] = VideoProviderEntry(
            name=provider_name,
            provider=provider,
            enabled=bool(enabled),
            priority=int(priority),
            generator=generator,
            configured_checker=(
                configured_checker
            ),
        )

    # ========================================================
    # BUILT-IN PROVIDERS
    # ========================================================

    def _register_builtin_providers(
        self,
    ) -> None:

        # ----------------------------------------------------
        # GOOGLE
        # ----------------------------------------------------

        try:

            from providers.video.google import (
                generate_google_video,
                google_video_provider,
                is_google_video_configured,
            )

            self.register_provider(
                name="google",
                provider=(
                    google_video_provider
                ),
                generator=(
                    generate_google_video
                ),
                configured_checker=(
                    is_google_video_configured
                ),
                priority=100,
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # RUNWAY
        # ----------------------------------------------------

        try:

            from providers.video.runway import (
                generate_runway_video,
                is_runway_video_configured,
                runway_video_provider,
            )

            self.register_provider(
                name="runway",
                provider=(
                    runway_video_provider
                ),
                generator=(
                    generate_runway_video
                ),
                configured_checker=(
                    is_runway_video_configured
                ),
                priority=90,
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # LUMA
        # ----------------------------------------------------

        try:

            from providers.video.luma import (
                generate_luma_video,
                is_luma_video_configured,
                luma_video_provider,
            )

            self.register_provider(
                name="luma",
                provider=(
                    luma_video_provider
                ),
                generator=(
                    generate_luma_video
                ),
                configured_checker=(
                    is_luma_video_configured
                ),
                priority=80,
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # KLING
        # ----------------------------------------------------

        try:

            from providers.video.kling import (
                generate_video,
                kling,
                is_configured,
            )

            self.register_provider(
                name="kling",
                provider=kling,
                generator=generate_video,
                configured_checker=is_configured,
                priority=70,
            )

        except Exception:
            pass

        # ----------------------------------------------------
        # REPLICATE
        # ----------------------------------------------------

        try:

            from providers.video.replicate import (
                generate_replicate_video,
                is_replicate_video_configured,
                replicate_video_provider,
            )

            self.register_provider(
                name="replicate",
                provider=(
                    replicate_video_provider
                ),
                generator=(
                    generate_replicate_video
                ),
                configured_checker=(
                    is_replicate_video_configured
                ),
                priority=60,
            )

        except Exception:
            pass

    # ========================================================
    # PROVIDER ACCESS
    # ========================================================

    def get_provider(
        self,
        name: str,
    ) -> Optional[VideoProviderEntry]:

        provider_name = str(
            name or ""
        ).strip().lower()

        return self._providers.get(
            provider_name
        )

    def get_all_providers(
        self,
    ) -> List[VideoProviderEntry]:

        return list(
            self._providers.values()
        )

    def get_provider_names(
        self,
    ) -> List[str]:

        return sorted(
            self._providers.keys()
        )

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable_provider(
        self,
        name: str,
    ) -> bool:

        entry = self.get_provider(
            name
        )

        if entry is None:
            return False

        entry.enabled = True

        return True

    def disable_provider(
        self,
        name: str,
    ) -> bool:

        entry = self.get_provider(
            name
        )

        if entry is None:
            return False

        entry.enabled = False

        return True

    # ========================================================
    # CONFIGURATION CHECK
    # ========================================================

    def is_provider_configured(
        self,
        name: str,
    ) -> bool:

        entry = self.get_provider(
            name
        )

        if entry is None:
            return False

        if not entry.enabled:
            return False

        if entry.configured_checker is None:
            return False

        try:

            return bool(
                entry.configured_checker()
            )

        except Exception:
            return False

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(
        self,
    ) -> Dict[str, Dict[str, Any]]:

        status = {}

        for entry in (
            self._providers.values()
        ):

            configured = (
                self.is_provider_configured(
                    entry.name
                )
            )

            status[
                entry.name
            ] = {
                "enabled": entry.enabled,
                "configured": configured,
                "available": (
                    entry.enabled
                    and configured
                    and entry.generator
                    is not None
                ),
                "priority": entry.priority,
            }

        return status

    # ========================================================
    # AVAILABLE PROVIDERS
    # ========================================================

    def get_available_providers(
        self,
    ) -> List[VideoProviderEntry]:

        available = []

        for entry in (
            self._providers.values()
        ):

            if not entry.enabled:
                continue

            if entry.generator is None:
                continue

            if not self.is_provider_configured(
                entry.name
            ):
                continue

            available.append(
                entry
            )

        available.sort(
            key=lambda item: (
                item.priority,
                item.name,
            ),
            reverse=True,
        )

        return available

    # ========================================================
    # PROVIDER ORDER
    # ========================================================

    def _build_provider_order(
        self,
        preferred_provider: Optional[str],
    ) -> List[VideoProviderEntry]:

        available = (
            self.get_available_providers()
        )

        if not preferred_provider:
            return available

        preferred_name = str(
            preferred_provider
        ).strip().lower()

        preferred = []

        remaining = []

        for entry in available:

            if entry.name == preferred_name:
                preferred.append(
                    entry
                )
            else:
                remaining.append(
                    entry
                )

        return (
            preferred
            + remaining
        )

    # ========================================================
    # GENERATOR CALL
    # ========================================================

    @staticmethod
    def _call_generator(
        generator: Callable[..., Dict[str, Any]],
        prompt: str,
        generation_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call providers using their common interface.

        Kling accepts a request object, while legacy
        providers may accept prompt + kwargs.
        """

        try:

            return generator(
                prompt,
                **generation_kwargs,
            )

        except TypeError as first_error:

            request = dict(
                generation_kwargs
            )

            request[
                "prompt"
            ] = prompt

            try:

                return generator(
                    request
                )

            except TypeError:
                raise first_error

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        output_path: Optional[str] = None,
        model: Optional[str] = None,
        fallback: bool = True,
        **kwargs: Any,
    ) -> VideoGenerationResult:

        prompt = str(
            prompt or ""
        ).strip()

        if not prompt:

            return VideoGenerationResult(
                success=False,
                error=(
                    "Video generation prompt "
                    "is required."
                ),
            )

        provider_order = (
            self._build_provider_order(
                preferred_provider=provider
            )
        )

        if provider and not provider_order:

            return VideoGenerationResult(
                success=False,
                error=(
                    f"Provider '{provider}' "
                    "is not configured, "
                    "enabled, or available."
                ),
            )

        if not provider_order:

            return VideoGenerationResult(
                success=False,
                error=(
                    "No configured video "
                    "generation provider is available."
                ),
            )

        attempts = []

        if not fallback:
            provider_order = (
                provider_order[:1]
            )

        for entry in provider_order:

            generator = (
                entry.generator
            )

            if generator is None:

                attempts.append(
                    {
                        "provider": entry.name,
                        "success": False,
                        "error": (
                            "Generator is not available."
                        ),
                    }
                )

                continue

            try:

                generation_kwargs = dict(
                    kwargs
                )

                if output_path is not None:

                    generation_kwargs[
                        "output_path"
                    ] = output_path

                if model is not None:

                    generation_kwargs[
                        "model"
                    ] = model

                result = self._call_generator(
                    generator,
                    prompt,
                    generation_kwargs,
                )

                if not isinstance(
                    result,
                    dict,
                ):
                    raise RuntimeError(
                        "Provider returned "
                        "an invalid result."
                    )

                success = bool(
                    result.get(
                        "success",
                        True,
                    )
                )

                if not success:

                    provider_error = str(
                        result.get(
                            "error",
                            "Provider failed.",
                        )
                    )

                    raise RuntimeError(
                        provider_error
                    )

                attempts.append(
                    {
                        "provider": entry.name,
                        "success": True,
                    }
                )

                metadata = result.get(
                    "metadata",
                    {},
                )

                if not isinstance(
                    metadata,
                    dict,
                ):
                    metadata = {}

                return VideoGenerationResult(
                    success=True,
                    provider=str(
                        result.get(
                            "provider",
                            entry.name,
                        )
                    ),
                    model=str(
                        result.get(
                            "model",
                            model or "",
                        )
                    ),
                    output_path=(
                        result.get(
                            "output_path"
                        )
                    ),
                    video_url=(
                        result.get(
                            "video_url"
                        )
                    ),
                    task_id=(
                        result.get(
                            "task_id"
                        )
                        or result.get(
                            "generation_id"
                        )
                        or result.get(
                            "prediction_id"
                        )
                    ),
                    attempts=attempts,
                    metadata=metadata,
                )

            except Exception as error:

                attempts.append(
                    {
                        "provider": entry.name,
                        "success": False,
                        "error": str(
                            error
                        ),
                    }
                )

                if not fallback:
                    break

        last_error = (
            attempts[-1].get(
                "error"
            )
            if attempts
            else "Unknown error."
        )

        return VideoGenerationResult(
            success=False,
            error=(
                "All available video "
                "providers failed. "
                f"Last error: {last_error}"
            ),
            attempts=attempts,
        )

    # ========================================================
    # SIMPLE GENERATE
    # ========================================================

    def generate_video(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        result = self.generate(
            prompt,
            **kwargs,
        )

        return result.to_dict()

    # ========================================================
    # TEST
    # ========================================================

    def test_configuration(
        self,
    ) -> Dict[str, Any]:

        status = self.get_status()

        available = [
            name
            for name, data
            in status.items()
            if data.get(
                "available",
                False,
            )
        ]

        return {
            "providers": status,
            "available_providers": available,
            "available_count": len(
                available
            ),
        }


# ============================================================
# GLOBAL MANAGER
# ============================================================


video_manager = (
    VideoGenerationManager()
)


# ============================================================
# PUBLIC HELPERS
# ============================================================


def get_video_manager() -> (
    VideoGenerationManager
):

    return video_manager


def get_video_provider_status() -> (
    Dict[str, Dict[str, Any]]
):

    return (
        video_manager.get_status()
    )


def get_available_video_providers() -> (
    List[str]
):

    return [
        entry.name
        for entry
        in video_manager.get_available_providers()
    ]


def generate_video(
    prompt: str,
    *,
    provider: Optional[str] = None,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    fallback: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:

    return video_manager.generate_video(
        prompt=prompt,
        provider=provider,
        output_path=output_path,
        model=model,
        fallback=fallback,
        **kwargs,
    )


def test_video_providers() -> (
    Dict[str, Any]
):

    return (
        video_manager
        .test_configuration()
    )


__all__ = [
    "VideoGenerationResult",
    "VideoProviderEntry",
    "VideoGenerationManager",
    "video_manager",
    "get_video_manager",
    "get_video_provider_status",
    "get_available_video_providers",
    "generate_video",
    "test_video_providers",
]
