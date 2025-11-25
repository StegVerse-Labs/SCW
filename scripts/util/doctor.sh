#!/usr/bin/env bash
set -euo pipefail
echo "[doctor] SCW sanity checks"

python -V
git --version

echo "[doctor] Checking templates..."
for f in SECURITY.md stegverse-module.json .github/workflows/scw_bridge_repo.yml; do
  if [[ ! -f "templates/$f" ]]; then
    echo "[doctor] MISSING templates/$f"
    exit 1
  fi
done

echo "[doctor] OK"
