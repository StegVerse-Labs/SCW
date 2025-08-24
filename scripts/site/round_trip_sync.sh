
#!/bin/bash
# Round-trip site sync:
# 1) Pull from external <owner/repo> (gh-pages preferred) into ./site_public
# 2) Validate links
# 3) Sync to deploy targets
# 4) Deploy via fallback orchestrator + publish status
# 5) (Optional) Republish back to external gh-pages (with optional --domain)
#
# Usage:
#   round_trip_sync.sh <owner/repo> [--republish] [--domain example.org]
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

echo "[1/5] Pulling from $EXT"
scripts/site/pull_from_external_repo.sh "$EXT"

echo "[2/5] Validating site"
scripts/site/validate_public_site.sh || true

echo "[3/5] Syncing to deploy targets"
scripts/site/sync_public_to_targets.sh

echo "[4/5] Deploying + publishing status"
scripts/deploy/deploy_orchestrator.sh
scripts/status/publish_status.sh

if [ "$REP" = "yes" ]; then
  echo "[5/5] Republishing back to $EXT"
  if [ -n "$DOMAIN" ]; then
    scripts/site/publish_to_external_repo.sh "$EXT" --domain "$DOMAIN"
  else
    scripts/site/publish_to_external_repo.sh "$EXT"
  fi
fi

echo "[✓] Round-trip completed."
