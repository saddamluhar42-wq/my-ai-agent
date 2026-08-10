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

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free",
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

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
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


def is_openrouter_configured():
    return bool(OPENROUTER_API_KEY)


def is_tavily_configured():
    return bool(TAVILY_API_KEY)


def is_database_configured():
    return bool(DATABASE_URL)


def is_telegram_configured():
    return bool(TELEGRAM_BOT_TOKEN)


def get_config_status():
    return {
        "gemini": is_gemini_configured(),
        "openrouter": is_openrouter_configured(),
        "tavily": is_tavily_configured(),
        "database": is_database_configured(),
        "telegram": is_telegram_configured(),
    }
