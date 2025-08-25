#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
SRC_DIR="$ROOT_DIR/site_public"

TARGET="${1:?Usage: publish_to_external_repo.sh <owner/repo> [--domain example.org] [--auto-create]}"
DOMAIN_FLAG="${2:-}"; DOMAIN_VAL="${3:-}"
AUTO_CREATE="no"; for a in "$@"; do [ "$a" = "--auto-create" ] && AUTO_CREATE="yes"; done

need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need gh; need git; need rsync
[ -d "$SRC_DIR" ] || { echo "site_public/ not found at $SRC_DIR"; exit 1; }

check_repo_access(){ gh repo view "$1" --json name,visibility,isPrivate,viewerPermission >/dev/null 2>&1; }

if check_repo_access "$TARGET"; then
  echo "[i] Repo access OK: $TARGET"
else
  echo "[!] Cannot access $TARGET. It may be private or not exist."
  if [ "$AUTO_CREATE" = "yes" ]; then
    echo "[i] Creating $TARGET via gh…"
    gh repo create "$TARGET" --public --confirm || gh repo create "$TARGET" --private --confirm || { echo "[x] Failed to create $TARGET"; exit 1; }
  else
    echo "Hint: login with gh auth login -w, or create the repo first, or pass --auto-create."; exit 1
  fi
fi

TMP=$(mktemp -d)
git clone --depth=1 "https://github.com/$TARGET.git" "$TMP/repo"
cd "$TMP/repo"
git checkout gh-pages 2>/dev/null || git checkout --orphan gh-pages
rm -rf * .[^.]* 2>/dev/null || true
rsync -a "$SRC_DIR"/ .
[ "$DOMAIN_FLAG" = "--domain" ] && [ -n "$DOMAIN_VAL" ] && echo "$DOMAIN_VAL" > CNAME || true
git add .; git commit -m "chore(site): publish to gh-pages" || true; git push origin gh-pages -f

gh api -X POST repos/$TARGET/pages -H "Accept: application/vnd.github+json" -f build_type="legacy" -F source='{"branch":"gh-pages","path":"/"}' >/dev/null 2>&1 || true
gh api -X PUT repos/$TARGET/pages  -H "Accept: application/vnd.github+json" -f build_type="legacy" -F source='{"branch":"gh-pages","path":"/"}' >/dev/null

INFO=$(gh api repos/$TARGET/pages -H "Accept: application/vnd.github+json" 2>/dev/null || true)
URL=$(echo "$INFO" | grep -oE '"html_url":"[^"]+"' | head -n1 | cut -d'"' -f4)
[ -z "$URL" ] && OWNER=$(echo "$TARGET" | cut -d'/' -f1) && REPO=$(echo "$TARGET" | cut -d'/' -f2) && URL="https://$OWNER.github.io/$REPO/"
echo "[✓] Published site to $TARGET → $URL"
echo "[i] If the repo is private, ensure your account has access and Pages is enabled."
