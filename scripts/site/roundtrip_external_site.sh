
#!/bin/bash
# Roundtrip external site edits: pull -> validate -> publish
# Usage: roundtrip_external_site.sh <owner/repo> [--domain example.org]
set -euo pipefail
TARGET="${1:?Usage: roundtrip_external_site.sh <owner/repo> [--domain example.org]}"
DOMAIN_FLAG="${2:-}"
DOMAIN_VAL="${3:-}"

echo ">>> Pulling site from $TARGET"
scripts/site/pull_from_external_repo.sh "$TARGET"

echo ">>> Validating site_public"
scripts/site/validate_public_site.sh || true

echo ">>> Republishing site_public back to $TARGET"
if [ "$DOMAIN_FLAG" = "--domain" ] && [ -n "$DOMAIN_VAL" ]; then
  scripts/site/publish_to_external_repo.sh "$TARGET" --domain "$DOMAIN_VAL"
else
  scripts/site/publish_to_external_repo.sh "$TARGET"
fi

echo "[✓] Roundtrip complete for $TARGET"
