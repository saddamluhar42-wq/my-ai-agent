# Security Guide

This project exposes Telegram and AI-provider integrations. Use the following production checklist.

## Required Environment Variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_WEBHOOK_SECRET`
- `DATABASE_URL` if chat memory is enabled
- Only the provider API keys you actually intend to use

## Telegram Hardening

- Keep `TELEGRAM_WEBHOOK_SECRET` unique per deployment.
- Configure Telegram webhooks to send the `X-Telegram-Bot-Api-Secret-Token` header.
- Do not leave `TELEGRAM_CHAT_ID` empty in production.
- Rotate the bot token immediately if you suspect it was exposed.

## Repository Hygiene

- Do not commit `.env` files, API keys, or database URLs.
- Keep dependencies pinned to known versions.
- Review any new workflow files before enabling them.

## Operational Notes

- The webhook endpoint rejects requests without the expected secret token.
- Telegram task intake is disabled unless `TELEGRAM_CHAT_ID` is configured.
- File upload limits are enforced consistently by the UI and backend.
