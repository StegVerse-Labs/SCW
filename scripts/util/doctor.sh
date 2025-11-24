#!/usr/bin/env bash
set -euo pipefail
echo "[doctor] SCW quick diagnostics"
echo "[doctor] Repo: $(pwd)"
echo "[doctor] Python: $(python --version)"
echo "[doctor] GH CLI: $(gh --version | head -n1 || true)"
echo "[doctor] Workflows present:"
ls -1 .github/workflows || true
echo "[doctor] OK"
