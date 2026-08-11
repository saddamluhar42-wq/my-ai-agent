import threading

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from streamlit.web import cli as stcli

from config import (
    RENDER_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_WEBHOOK_SECRET,
)
from telegram.bot import create_bot
from telegram.handlers import create_message_handler


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="My AI Agent Server",
    version="1.0.0",
)


# ============================================================
# TELEGRAM BOT
# ============================================================

telegram_bot = create_bot(
    message_handler=create_message_handler()
)


def verify_telegram_webhook_secret(request: Request) -> None:
    """
    Reject webhook traffic unless Telegram's secret token matches.
    """

    if not TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Telegram webhook secret is not configured.",
        )

    provided_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        "",
    ).strip()

    if not provided_secret or provided_secret != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Invalid Telegram webhook secret.",
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "My AI Agent",
        "telegram": bool(
            TELEGRAM_BOT_TOKEN
        ),
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "telegram": telegram_bot.running,
    }


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
):
    verify_telegram_webhook_secret(request)

    try:
        update = await request.json()

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid Telegram webhook payload.",
        ) from error

    telegram_bot.process_update(
        update
    )

    return JSONResponse(
        {
            "ok": True
        }
    )


# ============================================================
# STREAMLIT
# ============================================================

def run_streamlit():
    """
    Run Streamlit UI on internal port 8501.

    FastAPI remains the public Render server.
    """

    import sys

    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.address=127.0.0.1",
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    stcli.main()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    streamlit_thread = threading.Thread(
        target=run_streamlit,
        name="streamlit-ui",
        daemon=True,
    )

    streamlit_thread.start()

    port = 8000

    import os

    port = int(
        os.getenv(
            "PORT",
            "8000",
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
