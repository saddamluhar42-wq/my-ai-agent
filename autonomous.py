
import json
import os
import subprocess
import threading
import time
import urllib.request
from datetime import datetime, timezone

import psycopg

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
LEARNING_MINUTES = max(10, int(os.getenv("LEARNING_INTERVAL_MINUTES", "30")))

_started = False
_stop = threading.Event()
_offset = 0
_lock = threading.Lock()
_status = {"mode": "idle", "task": None, "last_learning": None, "last_health": None}


def http_json(url, method="GET", payload=None, headers=None, timeout=30):
    data = None
    h = {"User-Agent": "My-AI-Agent/1.0"}
    if headers:
        h.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def db(query, params=(), fetch=False):
    if not DATABASE_URL:
        return None
    with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            value = cur.fetchall() if fetch else None
            conn.commit()
            return value


def init_tables():
    if not DATABASE_URL:
        return
    db("""
    CREATE TABLE IF NOT EXISTS agent_tasks (
        id BIGSERIAL PRIMARY KEY,
        source TEXT NOT NULL,
        chat_id TEXT,
        task TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        result TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS agent_learning (
        id BIGSERIAL PRIMARY KEY,
        topic TEXT NOT NULL,
        knowledge TEXT NOT NULL,
        source TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS agent_health (
        id BIGSERIAL PRIMARY KEY,
        status TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """)


def tg(method, payload=None):
    return http_json(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        "POST",
        payload or {},
        timeout=35,
    )


def send(chat, text):
    if not chat:
        return
    try:
        tg("sendMessage", {"chat_id": str(chat), "text": text[:3900]})
    except Exception:
        pass


def ai(prompt):
    system = (
        "You are My AI Agent. Be factual. Do not claim that a file, "
        "GitHub repository, deployment, or test was changed unless a "
        "real tool performed that action. Prefer reversible operations."
    )

    if OPENROUTER_API_KEY:
        result = http_json(
            "https://openrouter.ai/api/v1/chat/completions",
            "POST",
            {
                "model": os.getenv("OPENROUTER_MODEL", "openrouter/free"),
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "X-Title": "My AI Agent",
            },
            90,
        )
        return result["choices"][0]["message"]["content"].strip()

    if GEMINI_API_KEY:
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        result = http_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={GEMINI_API_KEY}",
            "POST",
            {"contents": [{"parts": [{"text": system + "\n\n" + prompt}]}]},
            timeout=90,
        )
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()

    raise RuntimeError("No AI provider configured.")


def run_task(task, chat):
    with _lock:
        _status["mode"] = "working"
        _status["task"] = task

    send(chat, f"🤖 Agent Started\n\n{task}\n\nPlanning and working...")

    try:
        if DATABASE_URL:
            db(
                "INSERT INTO agent_tasks(source,chat_id,task,status) VALUES(%s,%s,%s,'running')",
                ("telegram", str(chat), task),
            )

        result = ai(
            "Work on this Telegram task as far as the available agent "
            "capabilities allow:\n\n"
            + task
            + "\n\nSeparate what was actually executed from recommendations. "
            "If clarification is needed, give 2-6 concise options."
        )

        if DATABASE_URL:
            db(
                "UPDATE agent_tasks SET status='completed',result=%s,updated_at=NOW() "
                "WHERE id=(SELECT id FROM agent_tasks WHERE chat_id=%s ORDER BY id DESC LIMIT 1)",
                (result, str(chat)),
            )

        send(chat, "✅ Agent Update\n\n" + result)

    except Exception as e:
        send(chat, "❌ Agent Error\n\n" + str(e))

    finally:
        with _lock:
            _status["mode"] = "idle"
            _status["task"] = None


def learn(chat=None):
    topic = os.getenv(
        "LEARNING_TOPIC",
        "Python, AI agents, Streamlit, PostgreSQL, GitHub, Telegram bots and software engineering",
    )

    try:
        material = "No web search configured."

        if TAVILY_API_KEY:
            result = http_json(
                "https://api.tavily.com/search",
                "POST",
                {
                    "api_key": TAVILY_API_KEY,
                    "query": topic,
                    "search_depth": "advanced",
                    "max_results": 5,
                    "include_answer": True,
                },
                timeout=60,
            )
            material = json.dumps(result, ensure_ascii=False)[:25000]

        knowledge = ai(
            "Learning mode. Study this material about "
            + topic
            + ". Extract durable technical lessons, common mistakes "
              "and practical rules. Do not invent facts.\n\n"
            + material
        )

        if DATABASE_URL:
            db(
                "INSERT INTO agent_learning(topic,knowledge,source) VALUES(%s,%s,%s)",
                (topic, knowledge, "Tavily + AI" if TAVILY_API_KEY else "AI"),
            )

        with _lock:
            _status["last_learning"] = datetime.now(timezone.utc).isoformat()

        if chat:
            send(chat, "🧠 Learning completed\n\n" + knowledge[:3500])

    except Exception as e:
        if chat:
            send(chat, "⚠️ Learning failed\n\n" + str(e))


def health():
    checks = []

    try:
        if DATABASE_URL:
            db("SELECT 1")
            checks.append("PostgreSQL: OK")
        else:
            checks.append("PostgreSQL: not configured")
    except Exception as e:
        checks.append("PostgreSQL: FAIL - " + str(e))

    try:
        r = subprocess.run(
            ["python", "-m", "compileall", "-q", "."],
            capture_output=True,
            text=True,
            timeout=60,
        )
        checks.append(
            "Python syntax: OK"
            if r.returncode == 0
            else "Python syntax: FAIL - " + r.stderr[-1000:]
        )
    except Exception as e:
        checks.append("Python check unavailable - " + str(e))

    result = "\n".join(checks)

    with _lock:
        _status["last_health"] = datetime.now(timezone.utc).isoformat()

    if DATABASE_URL:
        db(
            "INSERT INTO agent_health(status,details) VALUES(%s,%s)",
            ("ok" if "FAIL" not in result else "fail", result),
        )

    return result


def status():
    with _lock:
        s = dict(_status)

    return (
        "🤖 Agent Status\n\n"
        f"Mode: {s['mode']}\n"
        f"Task: {s['task'] or 'None'}\n"
        f"Last learning: {s['last_learning'] or '—'}\n"
        f"Last health: {s['last_health'] or '—'}"
    )


def repair(chat):
    send(chat, "🔧 Self-Repair: diagnosing the current project...")
    report = health()

    try:
        plan = ai(
            "Analyze this real health report and create a safe repair plan. "
            "Do not claim repairs were applied. Prefer reversible changes.\n\n"
            + report
        )
        send(chat, "🔍 Repair diagnosis\n\n" + plan[:3500])
    except Exception as e:
        send(chat, "❌ Repair analysis failed\n\n" + str(e))


def upgrade(chat):
    send(chat, "⬆️ Checking for dependency upgrades...")

    try:
        r = subprocess.run(
            ["python", "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if r.returncode:
            raise RuntimeError(r.stderr[-1500:])

        items = json.loads(r.stdout or "[]")

        if not items:
            send(chat, "✅ No outdated Python packages detected.")
            return

        lines = [
            f"{x['name']}: {x['version']} → {x['latest_version']}"
            for x in items[:25]
        ]

        send(
            chat,
            "⬆️ Upgrade candidates:\n\n"
            + "\n".join(lines)
            + "\n\nNo production package was automatically replaced.",
        )

    except Exception as e:
        send(chat, "❌ Upgrade scan failed\n\n" + str(e))


def handle(message):
    chat = str(message["chat"]["id"])

    if not CHAT_ID:
        return

    if chat != str(CHAT_ID):
        return

    text = (message.get("text") or "").strip()

    if not text:
        return

    if text == "/start":
        send(
            chat,
            "🤖 My AI Agent online.\n\n"
            "Send any task directly.\n\n"
            "/status\n/learn\n/repair\n/upgrade\n/stop",
        )
        return

    if text == "/status":
        send(chat, status())
        return

    if text == "/learn":
        threading.Thread(target=learn, args=(chat,), daemon=True).start()
        return

    if text == "/repair":
        threading.Thread(target=repair, args=(chat,), daemon=True).start()
        return

    if text == "/upgrade":
        threading.Thread(target=upgrade, args=(chat,), daemon=True).start()
        return

    if text == "/stop":
        _stop.set()
        send(chat, "⏹️ Background autonomous worker stopped.")
        return

    threading.Thread(target=run_task, args=(text, chat), daemon=True).start()


def telegram_loop():
    global _offset

    while not _stop.is_set():
        try:
            result = tg(
                "getUpdates",
                {"timeout": 25, "offset": _offset + 1},
            )

            for update in result.get("result", []):
                _offset = max(
                    _offset,
                    int(update["update_id"]),
                )

                if update.get("message"):
                    handle(update["message"])

        except Exception:
            time.sleep(5)


def learning_loop():
    while not _stop.wait(LEARNING_MINUTES * 60):
        with _lock:
            busy = _status["mode"] == "working"

        if not busy:
            learn()


def health_loop():
    while not _stop.wait(900):
        try:
            health()
        except Exception:
            pass


def start_background_services():
    global _started

    if _started:
        return

    _started = True

    try:
        init_tables()
    except Exception:
        pass

    if BOT_TOKEN and CHAT_ID:
        threading.Thread(
            target=telegram_loop,
            daemon=True,
            name="telegram-agent",
        ).start()

    threading.Thread(
        target=learning_loop,
        daemon=True,
        name="agent-learning",
    ).start()

    threading.Thread(
        target=health_loop,
        daemon=True,
        name="agent-health",
    ).start()
