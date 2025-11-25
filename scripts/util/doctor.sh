#!/usr/bin/env bash
set -euo pipefail
echo "[doctor] SCW quick health check"
python scw/scw_core.py self-test --org "${ORG_GITHUB:-StegVerse-Labs}" --target-repo "${TARGET_REPO:-StegVerse-Labs/SCW}"
echo "[doctor] done"
