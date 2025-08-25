#!/bin/bash
set -euo pipefail
FULL=$(git remote get-url origin | sed -E 's#.*github.com[:/]+([^/]+/[^/.]+)(\.git)?$#\1#')
URL="https://github.com/$FULL/settings/branches"
if scripts/github/ensure_branch_protection.sh "$FULL" "${1:-}"; then
  echo "[✓] Branch protection set."
else
  echo "[!] Could not set via API (likely 403). Open this on iPhone and set it manually:"
  echo "    $URL"
fi
