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
