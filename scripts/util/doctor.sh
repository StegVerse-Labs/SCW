
#!/bin/bash
set -euo pipefail
echo "=== StegVerse Doctor (Lite) ==="
echo "[*] CWD: $(pwd -P)"
for p in scripts/site/one_prompt_public_site.sh scripts/site/publish_to_external_repo.sh scripts/site/verify_external_pages.sh site_public; do
  if [ -e "$p" ]; then echo "  ✓ $p"; else echo "  ✗ MISSING: $p"; fi
done
echo "[*] Checking dependencies..."
for bin in gh git unzip rsync; do
  if command -v "$bin" >/dev/null 2>&1; then echo "  ✓ $bin"; else echo "  ✗ missing: $bin"; fi
done
