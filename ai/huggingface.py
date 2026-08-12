from io import BytesIO

from huggingface_hub import InferenceClient

from config import HF_TOKEN, HF_TOKEN_2, HF_TOKEN_3


class HuggingFaceError(Exception):
    """Raised when Hugging Face image generation fails."""


MODEL = "black-forest-labs/FLUX.1-schnell"


def get_available_tokens():
    return [(name, token) for name, token in (
        ("HF_TOKEN", HF_TOKEN),
        ("HF_TOKEN_2", HF_TOKEN_2),
        ("HF_TOKEN_3", HF_TOKEN_3),
    ) if token and token.strip()]


def is_configured():
    return bool(get_available_tokens())


def _safe_error(error):
    text = str(error or "Unknown error").replace("\n", " ").strip()
    for _, token in get_available_tokens():
        if token and len(token) > 8:
            text = text.replace(token, "[REDACTED]")
    return text[:500]


def _check_token(token_name, token):
    try:
        client = InferenceClient(api_key=token, provider="auto")
        whoami = getattr(client, "whoami", None)
        if callable(whoami):
            whoami()
        return True, "Authentication accepted"
    except Exception as error:
        return False, _safe_error(error)


def diagnose():
    tokens = get_available_tokens()
    if not tokens:
        return {
            "configured": False,
            "status": "missing_token",
            "message": "No Hugging Face token is available in the running environment.",
            "tokens": [],
        }

    results = []
    for token_name, token in tokens:
        ok, detail = _check_token(token_name, token)
        results.append({"name": token_name, "ok": ok, "detail": detail})

    working = [item["name"] for item in results if item["ok"]]
    if working:
        return {
            "configured": True,
            "status": "connected",
            "message": f"Hugging Face authentication available via {working[0]}.",
            "tokens": results,
        }

    return {
        "configured": True,
        "status": "authentication_failed",
        "message": "All configured Hugging Face tokens failed authentication. Check token validity and permissions.",
        "tokens": results,
    }


def generate_image(prompt, model=MODEL):
    if not prompt or not prompt.strip():
        raise HuggingFaceError("Image prompt cannot be empty.")

    tokens = get_available_tokens()
    if not tokens:
        raise HuggingFaceError("Hugging Face token is missing from the running environment. Add HF_TOKEN, HF_TOKEN_2, or HF_TOKEN_3 to the active Render service and redeploy.")

    errors = []
    for token_name, token in tokens:
        try:
            client = InferenceClient(api_key=token, provider="auto")
            image = client.text_to_image(prompt=prompt.strip(), model=model)
            if image is not None:
                return image
            errors.append(f"{token_name}: provider returned no image")
        except Exception as error:
            errors.append(f"{token_name}: {_safe_error(error)}")

    raise HuggingFaceError(
        "All Hugging Face image-generation attempts failed. "
        + " | ".join(errors)
    )


def generate_image_bytes(prompt, model=MODEL):
    image = generate_image(prompt=prompt, model=model)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def get_provider_info():
    tokens = get_available_tokens()
    diagnosis = diagnose() if tokens else None
    return {
        "provider": "Hugging Face",
        "model": MODEL,
        "configured": bool(tokens),
        "token_count": len(tokens),
        "status": diagnosis["status"] if diagnosis else "missing_token",
    }
