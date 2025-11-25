# StegVerse — Sovereign Control Workspace (SCW) — FULL Bundle v2

This bundle is a drop‑in orchestrator + autopatch system for the StegVerse ecosystem.
It is designed to run *from the SCW repo* and operate on your other repos using the
**organization secret** `GH_STEGVERSE_AI_TOKEN`.

## What’s fixed in v2
- Always prefers **org‑level token**; repo secret overrides are detected and warned.
- Push uses PAT‑auth URL `https://x-access-token:<TOKEN>@github.com/<org>/<repo>.git`
  to avoid “Permission denied to <user>”.
- Git identity is set inside workflows before any commit/push.
- Clear, actionable error messages for missing token / branch / permissions.

## Quick start (iPhone‑friendly)
1. Upload this zip into **StegVerse-Labs/SCW** (GitHub → Add file → Upload files → Commit).
2. Open Codespace → Terminal:
   ```bash
   unzip steg_scw_full_v2.zip -d .
   rm steg_scw_full_v2.zip
   git add .
   git commit -s -m "chore: import SCW full bundle v2"
   git push origin main
   scripts/util/doctor.sh
   ```
3. Run the orchestrator workflow:  
   Actions → **StegVerse SCW Orchestrator** → Run workflow  
   Target repo: `StegVerse-Labs/TVC`  
   Command: `self-test` (then `autopatch`).

## One‑prompt setup (optional)
```bash
./scripts/one_prompt_setup.sh
```

## Repo layout
- `scw/scw_core.py` — CLI core (self‑test, autopatch, publish site, etc.)
- `.github/workflows/scw.yml` — Orchestrator Action
- `.github/workflows/scw_bridge_repo.yml` — Bridge publisher (optional)
- `scripts/util/doctor.sh` — sanity checks
- `templates/` — standard StegVerse files injected by autopatch
