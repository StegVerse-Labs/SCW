
#!/bin/bash
set -euo pipefail
need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need git; need gh
gh auth status >/dev/null 2>&1 || gh auth login -w
read -r -p "Target repo (<owner>/<repo>) [StegVerse/site]: " TARGET
TARGET="${TARGET:-StegVerse/site}"
read -r -p "Custom domain (e.g., stegverse.org) [stegverse.org, blank to skip]: " DOMAIN
DOMAIN="${DOMAIN:-stegverse.org}"
if [ -z "$DOMAIN" ]; then DOMAIN_FLAG=""; else DOMAIN_FLAG="--domain $DOMAIN"; fi
scripts/site/publish_to_external_repo.sh "$TARGET" ${DOMAIN_FLAG}
scripts/site/verify_external_pages.sh "$TARGET" || true
echo "If custom domain set ($DOMAIN), add/confirm DNS: A (apex) 185.199.108.153 109.153 110.153 111.153 ; www CNAME -> <owner>.github.io"
