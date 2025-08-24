
#!/bin/bash
# One-prompt public site setup for an external repo (e.g., StegVerse/site).
# - Prompts for <owner/repo> (default: StegVerse/site)
# - Prompts for custom domain (default: stegverse.org, blank to skip)
# - Publishes ./site_public to gh-pages on the target
# - Enables GitHub Pages via API
# - Prints final URL and DNS reminders
# - Optionally verifies Pages config
set -euo pipefail

banner() {
  echo; echo "===================================================="; echo "$1"; echo "===================================================="
}

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1"; exit 1; }; }

banner "StegVerse — One-Prompt Public Site"

need git
need gh

# Auth
gh auth status >/dev/null 2>&1 || gh auth login -w

# Gather inputs
read -r -p "Target repo (<owner>/<repo>) [StegVerse/site]: " TARGET
TARGET="${TARGET:-StegVerse/site}"

read -r -p "Custom domain (e.g., stegverse.org) [stegverse.org, blank to skip]: " DOMAIN
DOMAIN="${DOMAIN:-stegverse.org}"
if [ -z "$DOMAIN" ]; then
  DOMAIN_FLAG=""
else
  DOMAIN_FLAG="--domain $DOMAIN"
fi

banner "Publishing site_public to $TARGET"
scripts/site/publish_to_external_repo.sh "$TARGET" ${DOMAIN_FLAG}

banner "Verifying GitHub Pages"
scripts/site/verify_external_pages.sh "$TARGET" || true

# Final notes
echo
echo "[✓] Done."
echo "If you set a custom domain: $DOMAIN"
echo "- Configure DNS (GoDaddy/Cloudflare):"
echo "  • A (apex): 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153"
echo "  • CNAME (www): <your-username>.github.io"
echo "- Cloudflare users: turn proxy OFF (grey cloud) during initial setup."
