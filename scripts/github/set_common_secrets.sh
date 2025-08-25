
#!/bin/bash
set -euo pipefail
REPO="${1:?Usage: set_common_secrets.sh <owner/repo>}"
set_secret(){ scripts/github/set_secret.sh "$REPO" "$1" "${2:-}"; }
echo "[i] Leave blank to skip"
read -r -p "VERCEL_TOKEN: " VERCEL_TOKEN; [ -n "$VERCEL_TOKEN" ] && set_secret VERCEL_TOKEN "$VERCEL_TOKEN"
read -r -p "NETLIFY_AUTH_TOKEN: " NETLIFY_AUTH_TOKEN; [ -n "$NETLIFY_AUTH_TOKEN" ] && set_secret NETLIFY_AUTH_TOKEN "$NETLIFY_AUTH_TOKEN"
read -r -p "MAILGUN_API_KEY: " MAILGUN_API_KEY; [ -n "$MAILGUN_API_KEY" ] && set_secret MAILGUN_API_KEY "$MAILGUN_API_KEY"
read -r -p "MAILGUN_DOMAIN: " MAILGUN_DOMAIN; [ -n "$MAILGUN_DOMAIN" ] && set_secret MAILGUN_DOMAIN "$MAILGUN_DOMAIN"
read -r -p "NOTIFY_EMAIL_TO: " NOTIFY_EMAIL_TO; [ -n "$NOTIFY_EMAIL_TO" ] && set_secret NOTIFY_EMAIL_TO "$NOTIFY_EMAIL_TO"
read -r -p "NOTIFY_EMAIL_FROM: " NOTIFY_EMAIL_FROM; [ -n "$NOTIFY_EMAIL_FROM" ] && set_secret NOTIFY_EMAIL_FROM "$NOTIFY_EMAIL_FROM"
read -r -p "SLACK_WEBHOOK_URL: " SLACK_WEBHOOK_URL; [ -n "$SLACK_WEBHOOK_URL" ] && set_secret SLACK_WEBHOOK_URL "$SLACK_WEBHOOK_URL"
read -r -p "DISCORD_WEBHOOK_URL: " DISCORD_WEBHOOK_URL; [ -n "$DISCORD_WEBHOOK_URL" ] && set_secret DISCORD_WEBHOOK_URL "$DISCORD_WEBHOOK_URL"
read -r -p "TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN; [ -n "$TELEGRAM_BOT_TOKEN" ] && set_secret TELEGRAM_BOT_TOKEN "$TELEGRAM_BOT_TOKEN"
read -r -p "TELEGRAM_CHAT_ID: " TELEGRAM_CHAT_ID; [ -n "$TELEGRAM_CHAT_ID" ] && set_secret TELEGRAM_CHAT_ID "$TELEGRAM_CHAT_ID"
echo "[✓] Secrets setup complete"
