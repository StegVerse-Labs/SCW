
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
SRC_DIR="$ROOT_DIR/site_public"
TARGET="${1:?Usage: publish_to_external_repo.sh <owner/repo> [--domain example.org]}"
DOMAIN_FLAG="${2:-}"
DOMAIN_VAL="${3:-}"

need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need gh; need git; need rsync
[ -d "$SRC_DIR" ] || { echo "site_public/ not found at $SRC_DIR"; exit 1; }

# Auth and repo access
gh auth status >/dev/null 2>&1 || gh auth login -w
gh repo view "$TARGET" >/dev/null 2>&1 || { echo "Target repo $TARGET not found."; exit 1; }

TMP=$(mktemp -d)
git clone --depth=1 "https://github.com/$TARGET.git" "$TMP/repo"
cd "$TMP/repo"

git checkout gh-pages 2>/dev/null || git checkout --orphan gh-pages
rm -rf * .[^.]* 2>/dev/null || true
rsync -a "$SRC_DIR"/ .
if [ "$DOMAIN_FLAG" = "--domain" ] && [ -n "$DOMAIN_VAL" ]; then echo "$DOMAIN_VAL" > CNAME; fi

git add .
git commit -m "chore(site): publish to gh-pages" || true
git push origin gh-pages -f

# Enable and print Pages URL
gh api -X POST repos/$TARGET/pages -H "Accept: application/vnd.github+json" -f build_type="legacy" -F source='{"branch":"gh-pages","path":"/"}' >/dev/null 2>&1 || true
gh api -X PUT repos/$TARGET/pages  -H "Accept: application/vnd.github+json" -f build_type="legacy" -F source='{"branch":"gh-pages","path":"/"}' >/dev/null
INFO=$(gh api repos/$TARGET/pages -H "Accept: application/vnd.github+json" 2>/dev/null || true)
URL=$(echo "$INFO" | grep -oE '"html_url":"[^"]+"' | head -n1 | cut -d'"' -f4)
if [ -z "$URL" ]; then OWNER=$(echo "$TARGET" | cut -d'/' -f1); REPO=$(echo "$TARGET" | cut -d'/' -f2); URL="https://$OWNER.github.io/$REPO/"; fi
echo "[✓] Published site to $TARGET → $URL"
if [ -n "$DOMAIN_VAL" ]; then
  echo "DNS reminder for $DOMAIN_VAL:"
  echo " - A (apex): 185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153"
  echo " - CNAME (www): <owner>.github.io"
fi
