from io import BytesIO

from huggingface_hub import InferenceClient

from config import (
    HF_TOKEN,
    HF_TOKEN_2,
    HF_TOKEN_3,
)


class HuggingFaceError(Exception):
    """Raised when Hugging Face image generation fails."""


MODEL = "black-forest-labs/FLUX.1-schnell"


def get_available_tokens():
    tokens = []

    if HF_TOKEN:
        tokens.append(
            (
                "HF_TOKEN",
                HF_TOKEN,
            )
        )

    if HF_TOKEN_2:
        tokens.append(
            (
                "HF_TOKEN_2",
                HF_TOKEN_2,
            )
        )

    if HF_TOKEN_3:
        tokens.append(
            (
                "HF_TOKEN_3",
                HF_TOKEN_3,
            )
        )

    return tokens


def is_configured():
    return bool(
        get_available_tokens()
    )


def generate_image(
    prompt,
    model=MODEL,
):
    if not prompt or not prompt.strip():
        raise HuggingFaceError(
            "Image prompt cannot be empty."
        )

    tokens = get_available_tokens()

    if not tokens:
        raise HuggingFaceError(
            "No Hugging Face API token is configured."
        )

    errors = []

    for token_name, token in tokens:

        try:
            client = InferenceClient(
                api_key=token,
                provider="auto",
            )

            image = client.text_to_image(
                prompt=prompt.strip(),
                model=model,
            )

            if image is None:
                errors.append(
                    f"{token_name}: "
                    "Hugging Face returned no image."
                )
                continue

            return image

        except Exception as error:
            errors.append(
                f"{token_name}: {error}"
            )

    raise HuggingFaceError(
        "All Hugging Face API keys failed.\n"
        + "\n".join(errors)
    )


def generate_image_bytes(
    prompt,
    model=MODEL,
):
    image = generate_image(
        prompt=prompt,
        model=model,
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def get_provider_info():
    tokens = get_available_tokens()

    return {
        "provider": "Hugging Face",
        "model": MODEL,
        "configured": bool(tokens),
        "token_count": len(tokens),
    }
