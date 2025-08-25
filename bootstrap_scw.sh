set -euo pipefail

mkdir -p scripts/site scripts/util scripts/github site_public

# --- minimal public site ---
cat > site_public/index.html <<'EOF'
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>StegVerse — Official</title></head><body><h1>StegVerse</h1><p>Sovereign, verifiable, resilient.</p><p><a href="./status.html">Status</a></p></body></html>
EOF

# --- doctor ---
cat > scripts/util/doctor.sh <<'EOF'
#!/bin/bash
set -euo pipefail
echo "=== StegVerse Doctor ==="
for p in scripts/site/one_prompt_public_site.sh scripts/site/publish_to_external_repo.sh scripts/site/verify_external_pages.sh scripts/github/bp.sh site_public; do
  [ -e "$p" ] && echo "  ✓ $p" || echo "  ✗ MISSING: $p"
done
for bin in gh git rsync unzip; do
  command -v "$bin" >/dev/null 2>&1 && echo "  ✓ $bin" || echo "  ✗ missing: $bin"
done
EOF
chmod +x scripts/util/doctor.sh

# --- branch protection helper (handles 403 by printing settings URL) ---
cat > scripts/github/bp.sh <<'EOF'
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
EOF
chmod +x scripts/github/bp.sh

# --- ensure branch protection (uses gh api) ---
cat > scripts/github/ensure_branch_protection.sh <<'EOF'
#!/bin/bash
set -euo pipefail
REPO="${1:?Usage: ensure_branch_protection.sh <owner/repo> [--require-signed]}"
SIGNED="${2:-}"
gh api -X PUT repos/$REPO/branches/main/protection -H "Accept: application/vnd.github+json" \
  -F required_status_checks='null' -F enforce_admins=true \
  -F required_pull_request_reviews='{"require_code_owner_reviews":true}' -F restrictions='null' \
  -F required_linear_history=true -F allow_force_pushes=false -F allow_deletions=false -F block_creations=false \
  -F required_conversation_resolution=true >/dev/null
if [ "$SIGNED" = "--require-signed" ]; then
  gh api -X POST repos/$REPO/branches/main/protection/required_signatures >/dev/null || true
fi
echo "[✓] Branch protection set on main."
EOF
chmod +x scripts/github/ensure_branch_protection.sh

# --- publish to external repo (auto-create optional) ---
cat > scripts/site/publish_to_external_repo.sh <<'EOF'
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
EOF
chmod +x scripts/site/publish_to_external_repo.sh

# --- verify pages ---
cat > scripts/site/verify_external_pages.sh <<'EOF'
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
EOF
chmod +x scripts/site/verify_external_pages.sh

# --- one-prompt site publish ---
cat > scripts/site/one_prompt_public_site.sh <<'EOF'
#!/bin/bash
set -euo pipefail
need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need git; need gh
gh auth status >/dev/null 2>&1 || gh auth login -w
read -r -p "Target repo (<owner>/<repo>) [StegVerse/site]: " TARGET; TARGET="${TARGET:-StegVerse/site}"
read -r -p "Custom domain (e.g., stegverse.org) [stegverse.org, blank to skip]: " DOMAIN; DOMAIN="${DOMAIN:-stegverse.org}"
[ -z "$DOMAIN" ] && DOMAIN_FLAG="" || DOMAIN_FLAG="--domain $DOMAIN"
read -r -p "Auto-create repo if missing? (Y/n): " AC; [ -z "$AC" -o "$AC" = "Y" -o "$AC" = "y" ] && ACFLAG="--auto-create" || ACFLAG=""
scripts/site/publish_to_external_repo.sh "$TARGET" ${DOMAIN_FLAG} $ACFLAG
scripts/site/verify_external_pages.sh "$TARGET" || true
echo "DNS: A (apex) 185.199.108.153 109.153 110.153 111.153 ; CNAME (www) -> <owner>.github.io"
EOF
chmod +x scripts/site/one_prompt_public_site.sh

echo "[✓] Bootstrap complete."
