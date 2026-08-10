import os


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = "My AI Agent"
APP_VERSION = "1.0.0"

RENDER_URL = os.getenv(
    "RENDER_URL",
    "https://my-ai-agent-8no8.onrender.com",
)


# ============================================================
# AI PROVIDERS
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_API_KEY_2 = os.getenv(
    "GEMINI_API_KEY_2"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

CEREBRAS_API_KEY = os.getenv(
    "CEREBRAS_API_KEY"
)

MISTRAL_API_KEY = os.getenv(
    "MISTRAL_API_KEY"
)


# ============================================================
# AI MODELS
# ============================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

GEMINI_MODEL_2 = os.getenv(
    "GEMINI_MODEL_2",
    "gemini-2.5-flash",
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free",
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.1-8b-instant",
)

CEREBRAS_MODEL = os.getenv(
    "CEREBRAS_MODEL",
    "llama-3.1-8b",
)

MISTRAL_MODEL = os.getenv(
    "MISTRAL_MODEL",
    "mistral-small-latest",
)


# ============================================================
# WEB SEARCH
# ============================================================

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)


# ============================================================
# API URLS
# ============================================================

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

GEMINI_URL_2 = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/"
    f"{GEMINI_MODEL_2}:generateContent"
)

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

GROQ_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)

CEREBRAS_URL = (
    "https://api.cerebras.ai/v1/chat/completions"
)

MISTRAL_URL = (
    "https://api.mistral.ai/v1/chat/completions"
)

TAVILY_URL = (
    "https://api.tavily.com/search"
)

TELEGRAM_URL = (
    f"https://api.telegram.org/bot"
    f"{TELEGRAM_BOT_TOKEN}"
    if TELEGRAM_BOT_TOKEN
    else ""
)


# ============================================================
# AI SETTINGS
# ============================================================

AI_TEMPERATURE = 0.7
AI_MAX_OUTPUT_TOKENS = 4096

REQUEST_TIMEOUT = 90
DATABASE_TIMEOUT = 10


# ============================================================
# FILE UPLOAD SETTINGS
# ============================================================

MAX_FILE_SIZE_MB = 20

SUPPORTED_FILE_TYPES = [
    "txt",
    "md",
    "csv",
    "json",
    "py",
    "html",
    "xml",
    "yaml",
    "yml",
    "pdf",
    "docx",
]


# ============================================================
# MEMORY SETTINGS
# ============================================================

MAX_CONVERSATION_MESSAGES = 30
MAX_MEMORY_RESULTS = 30
MAX_FILE_CONTEXT_CHARS = 50000


# ============================================================
# TELEGRAM SETTINGS
# ============================================================

TELEGRAM_POLL_TIMEOUT = 50
TELEGRAM_MESSAGE_LIMIT = 3900


# ============================================================
# HELPERS
# ============================================================

def is_gemini_configured():
    return bool(GEMINI_API_KEY)


def is_gemini_2_configured():
    return bool(GEMINI_API_KEY_2)


def is_openrouter_configured():
    return bool(OPENROUTER_API_KEY)


def is_groq_configured():
    return bool(GROQ_API_KEY)


def is_cerebras_configured():
    return bool(CEREBRAS_API_KEY)


def is_mistral_configured():
    return bool(MISTRAL_API_KEY)


def is_tavily_configured():
    return bool(TAVILY_API_KEY)


def is_database_configured():
    return bool(DATABASE_URL)


def is_telegram_configured():
    return bool(TELEGRAM_BOT_TOKEN)


def get_config_status():
    return {
        "gemini": is_gemini_configured(),
        "gemini_2": is_gemini_2_configured(),
        "openrouter": is_openrouter_configured(),
        "groq": is_groq_configured(),
        "cerebras": is_cerebras_configured(),
        "mistral": is_mistral_configured(),
        "tavily": is_tavily_configured(),
        "database": is_database_configured(),
        "telegram": is_telegram_configured(),
    }
