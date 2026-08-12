import os

APP_NAME = "My AI Agent"
APP_VERSION = "2.2.0"
RENDER_URL = os.getenv("RENDER_URL", "https://my-ai-agent-collab.onrender.com")

# Provider keys: every provider supports up to 3 keys. Keep secrets server-side.
def _keys(*names):
    return [value for value in (os.getenv(name) for name in names) if value and value.strip()]

def _configured(*names):
    return bool(_keys(*names))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_KEY_3 = os.getenv("GEMINI_API_KEY_3")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_KEY_2 = os.getenv("OPENROUTER_API_KEY_2")
OPENROUTER_API_KEY_3 = os.getenv("OPENROUTER_API_KEY_3")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2")
GROQ_API_KEY_3 = os.getenv("GROQ_API_KEY_3")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_API_KEY_2 = os.getenv("CEREBRAS_API_KEY_2")
CEREBRAS_API_KEY_3 = os.getenv("CEREBRAS_API_KEY_3")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_KEY_2 = os.getenv("MISTRAL_API_KEY_2")
MISTRAL_API_KEY_3 = os.getenv("MISTRAL_API_KEY_3")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_KEY_2 = os.getenv("ANTHROPIC_API_KEY_2")
ANTHROPIC_API_KEY_3 = os.getenv("ANTHROPIC_API_KEY_3")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_KEY_2 = os.getenv("DEEPSEEK_API_KEY_2")
DEEPSEEK_API_KEY_3 = os.getenv("DEEPSEEK_API_KEY_3")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_KEY_2 = os.getenv("KIMI_API_KEY_2")
KIMI_API_KEY_3 = os.getenv("KIMI_API_KEY_3")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY_2 = os.getenv("OPENAI_API_KEY_2")
OPENAI_API_KEY_3 = os.getenv("OPENAI_API_KEY_3")
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_KEY_2 = os.getenv("XAI_API_KEY_2")
XAI_API_KEY_3 = os.getenv("XAI_API_KEY_3")

YDC_API_KEY = os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY")
YDC_API_KEY_2 = os.getenv("YDC_API_KEY_2") or os.getenv("YOU_API_KEY_2")
YDC_API_KEY_3 = os.getenv("YDC_API_KEY_3") or os.getenv("YOU_API_KEY_3")
YOU_API_KEY = YDC_API_KEY
YOU_API_KEY_2 = YDC_API_KEY_2
YOU_API_KEY_3 = YDC_API_KEY_3

HF_TOKEN = os.getenv("HF_TOKEN")
HF_TOKEN_2 = os.getenv("HF_TOKEN_2")
HF_TOKEN_3 = os.getenv("HF_TOKEN_3")
NVIDIA_IMAGE_1 = os.getenv("NVIDIA_IMAGE_1")
NVIDIA_IMAGE_2 = os.getenv("NVIDIA_IMAGE_2")
NVIDIA_IMAGE_3 = os.getenv("NVIDIA_IMAGE_3")
NVIDIA_API_KEY = NVIDIA_IMAGE_1
NVIDIA_API_KEY_2 = NVIDIA_IMAGE_2
NVIDIA_API_KEY_3 = NVIDIA_IMAGE_3

# Video providers
GOOGLE_VIDEO_API_KEY = os.getenv("GOOGLE_VIDEO_API_KEY")
GOOGLE_VIDEO_API_KEY_2 = os.getenv("GOOGLE_VIDEO_API_KEY_2")
GOOGLE_VIDEO_API_KEY_3 = os.getenv("GOOGLE_VIDEO_API_KEY_3")
GOOGLE_VIDEO_MODEL = os.getenv("GOOGLE_VIDEO_MODEL", "veo")
RUNWAY_API_KEY1 = os.getenv("RUNWAY_API_KEY1")
RUNWAY_API_KEY2 = os.getenv("RUNWAY_API_KEY2")
RUNWAY_API_KEY3 = os.getenv("RUNWAY_API_KEY3")
RUNWAY_VIDEO_MODEL = os.getenv("RUNWAY_VIDEO_MODEL", "gen-4")
LUMA_API_KEY1 = os.getenv("LUMA_API_KEY1")
LUMA_API_KEY2 = os.getenv("LUMA_API_KEY2")
LUMA_API_KEY3 = os.getenv("LUMA_API_KEY3")
LUMA_VIDEO_MODEL = os.getenv("LUMA_VIDEO_MODEL", "ray")
KLING_API_KEY1 = os.getenv("KLING_API_KEY1")
KLING_API_KEY2 = os.getenv("KLING_API_KEY2")
KLING_API_KEY3 = os.getenv("KLING_API_KEY3")
KLING_VIDEO_MODEL = os.getenv("KLING_VIDEO_MODEL", "kling")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_API_TOKEN_2 = os.getenv("REPLICATE_API_TOKEN_2")
REPLICATE_API_TOKEN_3 = os.getenv("REPLICATE_API_TOKEN_3")

VIDEO_DEFAULT_PROVIDER = os.getenv("VIDEO_DEFAULT_PROVIDER", "auto").strip().lower()
VIDEO_DEFAULT_DURATION = int(os.getenv("VIDEO_DEFAULT_DURATION", "5"))
VIDEO_DEFAULT_ASPECT_RATIO = os.getenv("VIDEO_DEFAULT_ASPECT_RATIO", "16:9")
VIDEO_DEFAULT_STYLE = os.getenv("VIDEO_DEFAULT_STYLE", "cinematic")
VIDEO_REQUEST_TIMEOUT = int(os.getenv("VIDEO_REQUEST_TIMEOUT", "300"))
VIDEO_POLL_INTERVAL = float(os.getenv("VIDEO_POLL_INTERVAL", "3"))
VIDEO_MAX_DURATION = int(os.getenv("VIDEO_MAX_DURATION", "300"))

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_2 = os.getenv("GEMINI_MODEL_2", "gemini-2.5-flash")
GEMINI_MODEL_3 = os.getenv("GEMINI_MODEL_3", "gemini-2.5-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_MODEL_2 = os.getenv("OPENROUTER_MODEL_2", "openrouter/free")
OPENROUTER_MODEL_3 = os.getenv("OPENROUTER_MODEL_3", "openrouter/free")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "llama-3.1-8b")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-3-mini")
YOU_MODEL = os.getenv("YOU_MODEL", "default")
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
NVIDIA_IMAGE_MODEL = os.getenv("NVIDIA_IMAGE_MODEL", "flux.1-dev")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_API_KEY_2 = os.getenv("TAVILY_API_KEY_2")
TAVILY_API_KEY_3 = os.getenv("TAVILY_API_KEY_3")
TAVILY_URL = "https://api.tavily.com/search"
YOU_SEARCH_URL = "https://ydc-index.io/v1/search"
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_URL_2 = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_2}:generateContent"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_URL_2 = OPENROUTER_URL
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/images/generations"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else ""

AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "1536"))
REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "8"))
DATABASE_TIMEOUT = 8
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
SUPPORTED_FILE_TYPES = ["txt", "md", "csv", "json", "py", "html", "xml", "yaml", "yml", "pdf", "docx", "jpg", "jpeg", "png", "webp", "gif", "mp4", "mov", "webm", "avi", "mkv"]
MAX_CONVERSATION_MESSAGES = 30
MAX_MEMORY_RESULTS = 20
MAX_FILE_CONTEXT_CHARS = 30000
TELEGRAM_POLL_TIMEOUT = 50
TELEGRAM_MESSAGE_LIMIT = 3900

# Stable configuration checks used by UI and routing.
def is_gemini_configured(): return _configured("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3")
def is_openrouter_configured(): return _configured("OPENROUTER_API_KEY", "OPENROUTER_API_KEY_2", "OPENROUTER_API_KEY_3")
def is_groq_configured(): return _configured("GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3")
def is_cerebras_configured(): return _configured("CEREBRAS_API_KEY", "CEREBRAS_API_KEY_2", "CEREBRAS_API_KEY_3")
def is_mistral_configured(): return _configured("MISTRAL_API_KEY", "MISTRAL_API_KEY_2", "MISTRAL_API_KEY_3")
def is_anthropic_configured(): return _configured("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_2", "ANTHROPIC_API_KEY_3")
def is_deepseek_configured(): return _configured("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY_2", "DEEPSEEK_API_KEY_3")
def is_kimi_configured(): return _configured("KIMI_API_KEY", "KIMI_API_KEY_2", "KIMI_API_KEY_3")
def is_openai_configured(): return _configured("OPENAI_API_KEY", "OPENAI_API_KEY_2", "OPENAI_API_KEY_3")
def is_xai_configured(): return _configured("XAI_API_KEY", "XAI_API_KEY_2", "XAI_API_KEY_3")
def is_you_configured(): return _configured("YDC_API_KEY", "YDC_API_KEY_2", "YDC_API_KEY_3", "YOU_API_KEY", "YOU_API_KEY_2", "YOU_API_KEY_3")
def is_hf_configured(): return _configured("HF_TOKEN", "HF_TOKEN_2", "HF_TOKEN_3")
def is_nvidia_configured(): return _configured("NVIDIA_IMAGE_1", "NVIDIA_IMAGE_2", "NVIDIA_IMAGE_3")
def is_tavily_configured(): return _configured("TAVILY_API_KEY", "TAVILY_API_KEY_2", "TAVILY_API_KEY_3")
def is_database_configured(): return bool(DATABASE_URL)
def is_telegram_configured(): return bool(TELEGRAM_BOT_TOKEN)
def is_telegram_webhook_secret_configured(): return bool(TELEGRAM_WEBHOOK_SECRET)

def get_provider_key_status(provider):
    groups = {
        "gemini": ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"),
        "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_API_KEY_2", "OPENROUTER_API_KEY_3"),
        "groq": ("GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"),
        "cerebras": ("CEREBRAS_API_KEY", "CEREBRAS_API_KEY_2", "CEREBRAS_API_KEY_3"),
        "mistral": ("MISTRAL_API_KEY", "MISTRAL_API_KEY_2", "MISTRAL_API_KEY_3"),
        "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_2", "ANTHROPIC_API_KEY_3"),
        "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY_2", "DEEPSEEK_API_KEY_3"),
        "kimi": ("KIMI_API_KEY", "KIMI_API_KEY_2", "KIMI_API_KEY_3"),
        "openai": ("OPENAI_API_KEY", "OPENAI_API_KEY_2", "OPENAI_API_KEY_3"),
        "xai": ("XAI_API_KEY", "XAI_API_KEY_2", "XAI_API_KEY_3"),
        "you": ("YDC_API_KEY", "YDC_API_KEY_2", "YDC_API_KEY_3"),
        "huggingface": ("HF_TOKEN", "HF_TOKEN_2", "HF_TOKEN_3"),
        "nvidia": ("NVIDIA_IMAGE_1", "NVIDIA_IMAGE_2", "NVIDIA_IMAGE_3"),
    }
    names = groups.get(provider, ())
    return [{"slot": i + 1, "configured": bool(os.getenv(name, "").strip())} for i, name in enumerate(names)]

def get_configured_video_providers():
    providers=[]
    if _configured("GOOGLE_VIDEO_API_KEY", "GOOGLE_VIDEO_API_KEY_2", "GOOGLE_VIDEO_API_KEY_3"): providers.append("google")
    if _configured("RUNWAY_API_KEY1", "RUNWAY_API_KEY2", "RUNWAY_API_KEY3"): providers.append("runway")
    if _configured("LUMA_API_KEY1", "LUMA_API_KEY2", "LUMA_API_KEY3"): providers.append("luma")
    if _configured("KLING_API_KEY1", "KLING_API_KEY2", "KLING_API_KEY3"): providers.append("kling")
    if _configured("REPLICATE_API_TOKEN", "REPLICATE_API_TOKEN_2", "REPLICATE_API_TOKEN_3"): providers.append("replicate")
    return providers

def get_config_status():
    return {
        "gemini": is_gemini_configured(), "openrouter": is_openrouter_configured(), "groq": is_groq_configured(),
        "cerebras": is_cerebras_configured(), "mistral": is_mistral_configured(), "anthropic": is_anthropic_configured(),
        "deepseek": is_deepseek_configured(), "kimi": is_kimi_configured(), "openai": is_openai_configured(),
        "xai": is_xai_configured(), "you": is_you_configured(), "huggingface": is_hf_configured(),
        "nvidia": is_nvidia_configured(), "google_video": _configured("GOOGLE_VIDEO_API_KEY", "GOOGLE_VIDEO_API_KEY_2", "GOOGLE_VIDEO_API_KEY_3"),
        "runway_video": _configured("RUNWAY_API_KEY1", "RUNWAY_API_KEY2", "RUNWAY_API_KEY3"),
        "luma_video": _configured("LUMA_API_KEY1", "LUMA_API_KEY2", "LUMA_API_KEY3"),
        "kling_video": _configured("KLING_API_KEY1", "KLING_API_KEY2", "KLING_API_KEY3"),
        "replicate_video": _configured("REPLICATE_API_TOKEN", "REPLICATE_API_TOKEN_2", "REPLICATE_API_TOKEN_3"),
        "tavily": is_tavily_configured(), "database": is_database_configured(), "telegram": is_telegram_configured(),
        "video_default_provider": VIDEO_DEFAULT_PROVIDER, "configured_video_providers": get_configured_video_providers()
    }
