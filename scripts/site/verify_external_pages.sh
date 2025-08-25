#!/bin/bash
set -euo pipefail
TARGET="${1:?Usage: verify_external_pages.sh <owner/repo>}"
command -v gh >/dev/null 2>&1 || { echo "Missing gh CLI"; exit 1; }
if ! gh repo view "$TARGET" --json name,visibility,isPrivate,viewerPermission >/dev/null 2>&1; then
  echo "[!] Cannot access $TARGET. It may be private or not exist. Check gh auth or repo visibility."; exit 1
fi
INFO=$(gh api repos/$TARGET/pages -H "Accept: application/vnd.github+json" 2>/dev/null || true)
[ -n "$INFO" ] || { echo "No Pages configuration found."; exit 1; }
echo "$INFO" | sed 's/\\n/\\n/g'
URL=$(echo "$INFO" | grep -oE '"html_url":"[^"]+"' | head -n1 | cut -d'"' -f4)
echo "[✓] URL: ${URL:-<not available>}"
gh api repos/$TARGET/branches/gh-pages >/dev/null 2>&1 && echo "[✓] Branch gh-pages exists." || echo "[!] Branch gh-pages not found."
