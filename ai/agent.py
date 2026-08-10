from ai import cerebras
from ai import gemini
from ai import groq
from ai import mistral
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

    return providers


def generate(
    prompt,
    preferred_provider=None,
    temperature=None,
    max_tokens=None,
):
    """
    Generate an AI response.

    Provider priority:
    1. Explicitly requested provider
    2. Gemini
    3. OpenRouter
    4. Groq
    5. Cerebras
    6. Mistral
    """

    providers = []

    if preferred_provider:
        provider = preferred_provider.lower().strip()

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

    errors = []

    for provider in providers:

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
                    "model": gemini.get_provider_info()[
                        "model"
                    ],
                }

            except Exception as error:
                errors.append(
                    f"Gemini: {error}"
                )

        elif provider == "OpenRouter":

            if not openrouter.is_configured():
                errors.append(
                    "OpenRouter: API key not configured."
                )
                continue

            try:
                answer = openrouter.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return {
                    "answer": answer,
                    "provider": "OpenRouter",
                    "model": openrouter.get_provider_info()[
                        "model"
                    ],
                }

            except Exception as error:
                errors.append(
                    f"OpenRouter: {error}"
                )

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
                    "model": groq.get_provider_info()[
                        "model"
                    ],
                }

            except Exception as error:
                errors.append(
                    f"Groq: {error}"
                )

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
                    "model": cerebras.get_provider_info()[
                        "model"
                    ],
                }

            except Exception as error:
                errors.append(
                    f"Cerebras: {error}"
                )

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
                    "model": mistral.get_provider_info()[
                        "model"
                    ],
                }

            except Exception as error:
                errors.append(
                    f"Mistral: {error}"
                )

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
        "Gemini": gemini.is_configured(),
        "OpenRouter": openrouter.is_configured(),
        "Groq": groq.is_configured(),
        "Cerebras": cerebras.is_configured(),
        "Mistral": mistral.is_configured(),
    }
