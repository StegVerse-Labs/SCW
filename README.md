StegVerse — Sovereign Control Workspace (SCW)
====================================================

Root orchestrator for the StegVerse-Labs org.

Included
--------
- `.github/workflows/scw_orchestrator.yml`
- `.github/workflows/scw_bridge.yml`
- `scw/scw_core.py` (v2 PAT-auth push fix)
- `scw/guardian_manifest.json`
- `scw/templates/*`
- `scripts/*`

Quick start
-----------
1) Org secret:
   - GH_STEGVERSE_AI_TOKEN = fine-grained PAT with R/W on StegVerse-Labs (all repos)

2) Self-test:
   Actions → SCW Orchestrator → Run workflow
   command=self-test, target_repo=StegVerse-Labs/TVC

3) Autopatch pilot:
   command=autopatch, target_repo=StegVerse-Labs/TVC

Design notes
------------
- Orchestrator sets git identity so commits succeed.
- Autopatch pushes via explicit PAT-auth URL to prevent 403.
