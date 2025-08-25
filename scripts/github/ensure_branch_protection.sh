
#!/bin/bash
set -euo pipefail
REPO="${1:?Usage: ensure_branch_protection.sh <owner/repo> [--require-signed]}"
SIGNED="${2:-}"
gh api -X PUT repos/$REPO/branches/main/protection -H "Accept: application/vnd.github+json"   -F required_status_checks='null' -F enforce_admins=true   -F required_pull_request_reviews='{"require_code_owner_reviews":true}' -F restrictions='null'   -F required_linear_history=true -F allow_force_pushes=false -F allow_deletions=false -F block_creations=false   -F required_conversation_resolution=true >/dev/null
if [ "$SIGNED" = "--require-signed" ]; then gh api -X POST repos/$REPO/branches/main/protection/required_signatures >/dev/null || true; fi
echo "[✓] Branch protection set on main."
