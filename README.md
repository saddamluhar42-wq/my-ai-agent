My AI Agent Autonomous Master

Telegram commands: `/start`, `/status`, `/learn`, `/repair`, `/upgrade`, `/stop`

Normal Telegram messages are treated as tasks.
Repair performs diagnostics and produces a safe plan. Upgrade scans dependencies without silently replacing production packages.

## Deployment Checklist

- Set `TELEGRAM_BOT_TOKEN`
- Set `TELEGRAM_CHAT_ID`
- Set `TELEGRAM_WEBHOOK_SECRET`
- Set all model/API keys you actually intend to use
- Set `DATABASE_URL` if you want chat memory
- Keep `TELEGRAM_WEBHOOK_SECRET` private and unique per deployment
- Do not leave `TELEGRAM_CHAT_ID` empty in production

## Telegram Webhook Setup

Configure Telegram to send webhook updates to the public `POST /telegram/webhook` endpoint and include the same secret value you set in `TELEGRAM_WEBHOOK_SECRET`.

The server rejects webhook requests that do not include the expected `X-Telegram-Bot-Api-Secret-Token` header.

## Security Notes

- Webhook traffic is rejected unless the secret token matches
- Telegram task intake is disabled unless `TELEGRAM_CHAT_ID` is configured
- Upload size limits are aligned between the UI and the backend
- Python dependencies are pinned to specific versions
