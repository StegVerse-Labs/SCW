
#!/bin/bash
set -euo pipefail
echo "=== StegVerse Doctor ==="
echo "[*] CWD: $(pwd -P)"
for p in scripts/site/one_prompt_public_site.sh scripts/site/publish_to_external_repo.sh scripts/site/verify_external_pages.sh site_public scripts/status/generate_status.py scripts/deploy/deploy_orchestrator.sh; do
  [ -e "$p" ] && echo "  ✓ $p" || echo "  ✗ MISSING: $p"
done
for bin in gh git unzip rsync python3; do
  command -v "$bin" >/dev/null 2>&1 && echo "  ✓ $bin" || echo "  ✗ missing: $bin"
done
