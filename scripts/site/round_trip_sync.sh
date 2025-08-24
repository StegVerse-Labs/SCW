
#!/bin/bash
set -euo pipefail
EXT="${1:?Usage: round_trip_sync.sh <owner/repo> [--republish] [--domain example.org]}"
REP="no"; DOMAIN=""
shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --republish) REP="yes" ;;
    --domain) shift; DOMAIN="${1:-}" ;;
  esac
  shift || true
done
scripts/site/pull_from_external_repo.sh "$EXT"
echo "[i] (Lite) Skipping heavy validation; proceeding to publish."
if [ "$REP" = "yes" ]; then
  if [ -n "$DOMAIN" ]; then
    scripts/site/publish_to_external_repo.sh "$EXT" --domain "$DOMAIN"
  else
    scripts/site/publish_to_external_repo.sh "$EXT"
  fi
fi
echo "[✓] Round-trip complete."
