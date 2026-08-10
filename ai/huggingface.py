from io import BytesIO

from huggingface_hub import InferenceClient

from config import HF_TOKEN


class HuggingFaceError(Exception):
    """Raised when Hugging Face image generation fails."""


MODEL = "black-forest-labs/FLUX.1-schnell"


def is_configured():
    return bool(HF_TOKEN)


def generate_image(
    prompt,
    model=MODEL,
):
    if not HF_TOKEN:
        raise HuggingFaceError(
            "HF_TOKEN is not configured."
        )

    if not prompt or not prompt.strip():
        raise HuggingFaceError(
            "Image prompt cannot be empty."
        )

    try:
        client = InferenceClient(
            api_key=HF_TOKEN,
            provider="auto",
        )

        image = client.text_to_image(
            prompt=prompt.strip(),
            model=model,
        )

    except Exception as error:
        raise HuggingFaceError(
            f"Hugging Face image generation failed: "
            f"{error}"
        ) from error

    if image is None:
        raise HuggingFaceError(
            "Hugging Face returned no image."
        )

    return image


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
    return {
        "provider": "Hugging Face",
        "model": MODEL,
        "configured": is_configured(),
    }
