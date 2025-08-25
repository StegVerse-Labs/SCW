
#!/bin/bash
set -euo pipefail
FULL="${1:?Usage: create_repo_and_push.sh <owner/repo> [--private]}"
VIS="--public"; [ "${2:-}" = "--private" ] && VIS="--private"
gh auth status >/dev/null 2>&1 || gh auth login -w
owner="${FULL%/*}"; repo="${FULL#*/}"
git init >/dev/null 2>&1 || true
git checkout -B main
gh repo view "$FULL" >/dev/null 2>&1 || gh repo create "$FULL" $VIS --confirm
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$FULL.git"
git add .; git commit -s -m "chore: initial import" || true
git push -u origin main
echo "[✓] Pushed main to https://github.com/$FULL"
