import base64
from io import BytesIO

import requests

from config import (
    NVIDIA_API_KEY,
    NVIDIA_API_KEY_2,
    NVIDIA_API_KEY_3,
    NVIDIA_IMAGE_MODEL,
    NVIDIA_URL,
)


class NVIDIAError(Exception):
    """Raised when NVIDIA image generation fails."""


def get_available_tokens():
    tokens = []

    if NVIDIA_API_KEY:
        tokens.append(
            (
                "NVIDIA_API_KEY",
                NVIDIA_API_KEY,
            )
        )

    if NVIDIA_API_KEY_2:
        tokens.append(
            (
                "NVIDIA_API_KEY_2",
                NVIDIA_API_KEY_2,
            )
        )

    if NVIDIA_API_KEY_3:
        tokens.append(
            (
                "NVIDIA_API_KEY_3",
                NVIDIA_API_KEY_3,
            )
        )

    return tokens


def is_configured():
    return bool(get_available_tokens())


def generate_image(
    prompt,
    model=None,
):
    if not prompt or not prompt.strip():
        raise NVIDIAError(
            "Image prompt cannot be empty."
        )

    tokens = get_available_tokens()

    if not tokens:
        raise NVIDIAError(
            "No NVIDIA API key is configured."
        )

    selected_model = (
        model or NVIDIA_IMAGE_MODEL
    )

    errors = []

    payload = {
        "model": selected_model,
        "prompt": prompt.strip(),
        "n": 1,
        "response_format": "b64_json",
    }

    for token_name, token in tokens:

        try:
            response = requests.post(
                NVIDIA_URL,
                headers={
                    "Authorization": (
                        f"Bearer {token}"
                    ),
                    "Accept": (
                        "application/json"
                    ),
                    "Content-Type": (
                        "application/json"
                    ),
                },
                json=payload,
                timeout=90,
            )

            if response.status_code >= 400:
                errors.append(
                    f"{token_name}: "
                    f"HTTP {response.status_code} "
                    f"- {response.text[:500]}"
                )
                continue

            data = response.json()

            images = data.get(
                "data",
                [],
            )

            if not images:
                errors.append(
                    f"{token_name}: "
                    "NVIDIA returned no image."
                )
                continue

            image_data = images[0].get(
                "b64_json"
            )

            if not image_data:
                errors.append(
                    f"{token_name}: "
                    "NVIDIA returned no "
                    "base64 image data."
                )
                continue

            image_bytes = base64.b64decode(
                image_data
            )

            from PIL import Image

            image = Image.open(
                BytesIO(image_bytes)
            )

            return image

        except Exception as error:
            errors.append(
                f"{token_name}: {error}"
            )

    raise NVIDIAError(
        "All NVIDIA API keys failed.\n"
        + "\n".join(errors)
    )


def generate_image_bytes(
    prompt,
    model=None,
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
        "provider": "NVIDIA",
        "model": NVIDIA_IMAGE_MODEL,
        "configured": is_configured(),
        "token_count": len(
            get_available_tokens()
        ),
    }
