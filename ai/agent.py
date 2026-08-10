from ai import anthropic
from ai import cerebras
from ai import gemini
from ai import groq
from ai import huggingface
from ai import mistral
from ai import nvidia
from ai import openrouter


class AgentError(Exception):
    """Raised when the AI agent cannot generate a response."""


def get_available_providers():
    providers = []

    if gemini.is_configured():
        providers.append("Gemini")

    if openrouter.is_configured():
        providers.append("OpenRouter")

    if groq.is_configured():
        providers.append("Groq")

    if cerebras.is_configured():
        providers.append("Cerebras")

    if mistral.is_configured():
        providers.append("Mistral")

    if anthropic.is_configured():
        providers.append("Anthropic")

    return providers


def is_image_generation_available():
    return (
        nvidia.is_configured()
        or huggingface.is_configured()
    )


def generate_image(
    prompt,
):
    """
    Generate an image using the configured image
    providers.

    Provider priority:

    1. NVIDIA
    2. Hugging Face

    Each provider has its own API-key fallback system.

    IMPORTANT:
    This function must only be called after the user
    explicitly confirms image generation.
    """

    if not prompt or not prompt.strip():
        raise AgentError(
            "Image prompt cannot be empty."
        )

    if not is_image_generation_available():
        raise AgentError(
            "No image-generation provider is configured."
        )

    errors = []

    # ========================================================
    # NVIDIA
    # ========================================================

    if nvidia.is_configured():

        try:
            image_bytes = (
                nvidia.generate_image_bytes(
                    prompt=prompt.strip(),
                )
            )

            if not image_bytes:
                raise AgentError(
                    "NVIDIA returned an empty image."
                )

            provider_info = (
                nvidia.get_provider_info()
            )

            return {
                "image": image_bytes,
                "provider": provider_info[
                    "provider"
                ],
                "model": provider_info[
                    "model"
                ],
                "type": "image",
            }

        except Exception as error:
            errors.append(
                f"NVIDIA: {error}"
            )

    else:
        errors.append(
            "NVIDIA: API keys not configured."
        )

    # ========================================================
    # HUGGING FACE
    # ========================================================

    if huggingface.is_configured():

        try:
            image_bytes = (
                huggingface.generate_image_bytes(
                    prompt=prompt.strip(),
                )
            )

            if not image_bytes:
                raise AgentError(
                    "Hugging Face returned an empty image."
                )

            provider_info = (
                huggingface.get_provider_info()
            )

            return {
                "image": image_bytes,
                "provider": provider_info[
                    "provider"
                ],
                "model": provider_info[
                    "model"
                ],
                "type": "image",
            }

        except Exception as error:
            errors.append(
                f"Hugging Face: {error}"
            )

    else:
        errors.append(
            "Hugging Face: API keys not configured."
        )

    # ========================================================
    # ALL IMAGE PROVIDERS FAILED
    # ========================================================

    raise AgentError(
        "All image providers failed.\n"
        + "\n".join(errors)
    )


def generate(
    prompt,
    preferred_provider=None,
    temperature=None,
    max_tokens=None,
):
    """
    Generate an AI text response.

    Provider priority:

    1. Explicitly requested provider
    2. Gemini
    3. OpenRouter
    4. Groq
    5. Cerebras
    6. Mistral
    7. Anthropic

    Image generation is NOT triggered here.
    Image generation requires an explicit confirmation
    followed by generate_image().
    """

    providers = []

    if preferred_provider:
        provider = (
            preferred_provider
            .lower()
            .strip()
        )

        if provider == "gemini":
            providers.append("Gemini")

        elif provider == "openrouter":
            providers.append("OpenRouter")

        elif provider == "groq":
            providers.append("Groq")

        elif provider == "cerebras":
            providers.append("Cerebras")

        elif provider == "mistral":
            providers.append("Mistral")

        elif provider in (
            "anthropic",
            "claude",
        ):
            providers.append("Anthropic")

    if "Gemini" not in providers:
        providers.append("Gemini")

    if "OpenRouter" not in providers:
        providers.append("OpenRouter")

    if "Groq" not in providers:
        providers.append("Groq")

    if "Cerebras" not in providers:
        providers.append("Cerebras")

    if "Mistral" not in providers:
        providers.append("Mistral")

    if "Anthropic" not in providers:
        providers.append("Anthropic")

    errors = []

    for provider in providers:

        # ====================================================
        # GEMINI
        # ====================================================

        if provider == "Gemini":

            if not gemini.is_configured():
                errors.append(
                    "Gemini: API key not configured."
                )
                continue

            try:
                answer = gemini.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )

                return {
                    "answer": answer,
                    "provider": "Gemini",
                    "model": (
                        gemini.get_provider_info()[
                            "model"
                        ]
                    ),
                    "type": "text",
                }

            except Exception as error:
                errors.append(
                    f"Gemini: {error}"
                )

        # ====================================================
        # OPENROUTER
        # ====================================================

        elif provider == "OpenRouter":

            if not openrouter.is_configured():
                errors.append(
                    "OpenRouter: API key not configured."
                )
                continue

            try:
                result = openrouter.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return {
                    "answer": result["answer"],
                    "provider": result["provider"],
                    "model": result["model"],
                    "type": "text",
                }

            except Exception as error:
                errors.append(
                    f"OpenRouter: {error}"
                )

        # ====================================================
        # GROQ
        # ====================================================

        elif provider == "Groq":

            if not groq.is_configured():
                errors.append(
                    "Groq: API key not configured."
                )
                continue

            try:
                answer = groq.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return {
                    "answer": answer,
                    "provider": "Groq",
                    "model": (
                        groq.get_provider_info()[
                            "model"
                        ]
                    ),
                    "type": "text",
                }

            except Exception as error:
                errors.append(
                    f"Groq: {error}"
                )

        # ====================================================
        # CEREBRAS
        # ====================================================

        elif provider == "Cerebras":

            if not cerebras.is_configured():
                errors.append(
                    "Cerebras: API key not configured."
                )
                continue

            try:
                answer = cerebras.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return {
                    "answer": answer,
                    "provider": "Cerebras",
                    "model": (
                        cerebras.get_provider_info()[
                            "model"
                        ]
                    ),
                    "type": "text",
                }

            except Exception as error:
                errors.append(
                    f"Cerebras: {error}"
                )

        # ====================================================
        # MISTRAL
        # ====================================================

        elif provider == "Mistral":

            if not mistral.is_configured():
                errors.append(
                    "Mistral: API key not configured."
                )
                continue

            try:
                answer = mistral.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return {
                    "answer": answer,
                    "provider": "Mistral",
                    "model": (
                        mistral.get_provider_info()[
                            "model"
                        ]
                    ),
                    "type": "text",
                }

            except Exception as error:
                errors.append(
                    f"Mistral: {error}"
                )

        # ====================================================
        # ANTHROPIC
        # ====================================================

        elif provider == "Anthropic":

            if not anthropic.is_configured():
                errors.append(
                    "Anthropic: API key not configured."
                )
                continue

            try:
                result = anthropic.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return {
                    "answer": result["answer"],
                    "provider": result["provider"],
                    "model": result["model"],
                    "type": "text",
                }

            except Exception as error:
                errors.append(
                    f"Anthropic: {error}"
                )

    # ========================================================
    # ALL TEXT PROVIDERS FAILED
    # ========================================================

    if not errors:
        raise AgentError(
            "No AI provider is configured."
        )

    raise AgentError(
        "All AI providers failed.\n"
        + "\n".join(errors)
    )


def generate_text(
    prompt,
    preferred_provider=None,
):
    result = generate(
        prompt=prompt,
        preferred_provider=preferred_provider,
    )

    return result["answer"]


def provider_status():
    return {
        "Gemini": (
            gemini.is_configured()
        ),
        "OpenRouter": (
            openrouter.is_configured()
        ),
        "Groq": (
            groq.is_configured()
        ),
        "Cerebras": (
            cerebras.is_configured()
        ),
        "Mistral": (
            mistral.is_configured()
        ),
        "Anthropic": (
            anthropic.is_configured()
        ),
        "NVIDIA Image": (
            nvidia.is_configured()
        ),
        "Hugging Face Image": (
            huggingface.is_configured()
        ),
    }
