#!/bin/bash
set -euo pipefail
echo "=== StegVerse Doctor ==="
for p in scripts/site/one_prompt_public_site.sh scripts/site/publish_to_external_repo.sh scripts/site/verify_external_pages.sh scripts/github/bp.sh site_public; do
  [ -e "$p" ] && echo "  ✓ $p" || echo "  ✗ MISSING: $p"
done
for bin in gh git rsync unzip; do
  command -v "$bin" >/dev/null 2>&1 && echo "  ✓ $bin" || echo "  ✗ missing: $bin"
done
