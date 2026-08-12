import os


APP_NAME = "My AI Agent"
APP_VERSION = "1.3.0"

RENDER_URL = os.getenv("RENDER_URL", "https://my-ai-agent-q6po.onrender.com")

# Text / chat providers
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_KEY_2 = os.getenv("OPENROUTER_API_KEY_2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
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
YOU_API_KEY = os.getenv("YOU_API_KEY")
YOU_API_KEY_2 = os.getenv("YOU_API_KEY_2")
YOU_API_KEY_3 = os.getenv("YOU_API_KEY_3")

# Image providers
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
REPLICATE_VIDEO_MODEL = os.getenv("REPLICATE_VIDEO_MODEL")

VIDEO_DEFAULT_PROVIDER = os.getenv("VIDEO_DEFAULT_PROVIDER", "auto").strip().lower()
VIDEO_DEFAULT_DURATION = int(os.getenv("VIDEO_DEFAULT_DURATION", "5"))
VIDEO_DEFAULT_ASPECT_RATIO = os.getenv("VIDEO_DEFAULT_ASPECT_RATIO", "16:9")
VIDEO_DEFAULT_STYLE = os.getenv("VIDEO_DEFAULT_STYLE", "cinematic")
VIDEO_REQUEST_TIMEOUT = int(os.getenv("VIDEO_REQUEST_TIMEOUT", "300"))
VIDEO_POLL_INTERVAL = float(os.getenv("VIDEO_POLL_INTERVAL", "3"))
VIDEO_MAX_DURATION = int(os.getenv("VIDEO_MAX_DURATION", "300"))

# Model names shown in the UI and used by providers that support model selection.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_2 = os.getenv("GEMINI_MODEL_2", "gemini-2.5-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_MODEL_2 = os.getenv("OPENROUTER_MODEL_2", "openrouter/free")
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
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_URL_2 = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_2}:generateContent"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_URL_2 = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
TAVILY_URL = "https://api.tavily.com/search"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/images/generations"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else ""

AI_TEMPERATURE = 0.7
AI_MAX_OUTPUT_TOKENS = 2048
REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "15"))
DATABASE_TIMEOUT = 10

MAX_FILE_SIZE_MB = 20
SUPPORTED_FILE_TYPES = ["txt", "md", "csv", "json", "py", "html", "xml", "yaml", "yml", "pdf", "docx"]
MAX_CONVERSATION_MESSAGES = 30
MAX_MEMORY_RESULTS = 30
MAX_FILE_CONTEXT_CHARS = 50000
TELEGRAM_POLL_TIMEOUT = 50
TELEGRAM_MESSAGE_LIMIT = 3900


def is_gemini_configured(): return bool(GEMINI_API_KEY or GEMINI_API_KEY_2)
def is_openrouter_configured(): return bool(OPENROUTER_API_KEY or OPENROUTER_API_KEY_2)
def is_groq_configured(): return bool(GROQ_API_KEY)
def is_cerebras_configured(): return bool(CEREBRAS_API_KEY)
def is_mistral_configured(): return bool(MISTRAL_API_KEY)
def is_anthropic_configured(): return bool(ANTHROPIC_API_KEY or ANTHROPIC_API_KEY_2 or ANTHROPIC_API_KEY_3)
def is_deepseek_configured(): return bool(DEEPSEEK_API_KEY or DEEPSEEK_API_KEY_2 or DEEPSEEK_API_KEY_3)
def is_kimi_configured(): return bool(KIMI_API_KEY or KIMI_API_KEY_2 or KIMI_API_KEY_3)
def is_openai_configured(): return bool(OPENAI_API_KEY or OPENAI_API_KEY_2 or OPENAI_API_KEY_3)
def is_xai_configured(): return bool(XAI_API_KEY or XAI_API_KEY_2 or XAI_API_KEY_3)
def is_you_configured(): return bool(YOU_API_KEY or YOU_API_KEY_2 or YOU_API_KEY_3)
def is_hf_configured(): return bool(HF_TOKEN or HF_TOKEN_2 or HF_TOKEN_3)
def is_nvidia_configured(): return bool(NVIDIA_IMAGE_1 or NVIDIA_IMAGE_2 or NVIDIA_IMAGE_3)

def get_nvidia_image_keys(): return [key for key in [NVIDIA_IMAGE_1, NVIDIA_IMAGE_2, NVIDIA_IMAGE_3] if key]

def is_google_video_configured(): return bool(GOOGLE_VIDEO_API_KEY or GOOGLE_VIDEO_API_KEY_2)
def is_runway_configured(): return bool(RUNWAY_API_KEY1 or RUNWAY_API_KEY2 or RUNWAY_API_KEY3)
def is_luma_configured(): return bool(LUMA_API_KEY1 or LUMA_API_KEY2 or LUMA_API_KEY3)
def is_kling_configured(): return bool(KLING_API_KEY1 or KLING_API_KEY2 or KLING_API_KEY3)
def is_replicate_configured(): return bool(REPLICATE_API_TOKEN or REPLICATE_API_TOKEN_2)

def get_runway_keys(): return [key for key in [RUNWAY_API_KEY1, RUNWAY_API_KEY2, RUNWAY_API_KEY3] if key]
def get_luma_keys(): return [key for key in [LUMA_API_KEY1, LUMA_API_KEY2, LUMA_API_KEY3] if key]
def get_kling_keys(): return [key for key in [KLING_API_KEY1, KLING_API_KEY2, KLING_API_KEY3] if key]
def get_google_video_keys(): return [key for key in [GOOGLE_VIDEO_API_KEY, GOOGLE_VIDEO_API_KEY_2] if key]
def get_replicate_tokens(): return [token for token in [REPLICATE_API_TOKEN, REPLICATE_API_TOKEN_2] if token]

def get_configured_video_providers():
    providers = []
    if is_google_video_configured(): providers.append("google")
    if is_runway_configured(): providers.append("runway")
    if is_luma_configured(): providers.append("luma")
    if is_kling_configured(): providers.append("kling")
    if is_replicate_configured(): providers.append("replicate")
    return providers

def is_tavily_configured(): return bool(TAVILY_API_KEY)
def is_database_configured(): return bool(DATABASE_URL)
def is_telegram_configured(): return bool(TELEGRAM_BOT_TOKEN)
def is_telegram_webhook_secret_configured(): return bool(TELEGRAM_WEBHOOK_SECRET)

def get_config_status():
    return {
        "gemini": is_gemini_configured(), "openrouter": is_openrouter_configured(),
        "groq": is_groq_configured(), "cerebras": is_cerebras_configured(), "mistral": is_mistral_configured(),
        "anthropic": is_anthropic_configured(), "deepseek": is_deepseek_configured(), "kimi": is_kimi_configured(),
        "openai": is_openai_configured(), "xai": is_xai_configured(), "you": is_you_configured(),
        "huggingface": is_hf_configured(), "nvidia": is_nvidia_configured(),
        "google_video": is_google_video_configured(), "runway_video": is_runway_configured(), "luma_video": is_luma_configured(), "kling_video": is_kling_configured(), "replicate_video": is_replicate_configured(),
        "video_default_provider": VIDEO_DEFAULT_PROVIDER, "configured_video_providers": get_configured_video_providers(),
        "tavily": is_tavily_configured(), "database": is_database_configured(), "telegram": is_telegram_configured(),
    }
