
#!/bin/bash
set -euo pipefail
python -m pip install --upgrade pip
pip install -r requirements.txt || true
pip install pre-commit detect-secrets black ruff || true
pre-commit install || true
echo "[✓] Bootstrap complete"
