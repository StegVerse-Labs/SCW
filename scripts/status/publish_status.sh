
#!/bin/bash
set -euo pipefail
python3 scripts/status/generate_status.py
rsync -a site_public/ site_pages/
echo "[✓] Status published into site_pages/"
