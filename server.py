import threading

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from streamlit.web import cli as stcli

from config import RENDER_URL, TELEGRAM_BOT_TOKEN
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
    try:
        update = await request.json()

        telegram_bot.process_update(
            update
        )

        return JSONResponse(
            {
                "ok": True
            }
        )

    except Exception as error:
        return JSONResponse(
            {
                "ok": False,
                "error": str(error)[:700],
            },
            status_code=200,
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
