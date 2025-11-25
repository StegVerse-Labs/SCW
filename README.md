# StegVerse SCW (StegVerse-Labs/SCW)

SCW = **StegVerse Continuous Workflows**.  
This repo hosts the Orchestrator workflow plus SCW core scripts that can:
- `self-test` token + org visibility
- `autopatch` StegVerse repo hygiene across target repos

## How to run
1. Go to **Actions → StegVerse SCW Orchestrator → Run workflow**
2. Pick:
   - command: `self-test`
   - target_repo: e.g. `StegVerse-Labs/TVC`

### Autopatch safety
Autopatch will:
- create a branch `autopatch/<timestamp>`
- add/refresh `SECURITY.md`
- add/refresh `stegverse-module.json`
- add `.github/workflows/scw_bridge_repo.yml`
- push branch & open PR **only if token has push rights** and `dry_run=false`.

Use `allowlist` to constrain which repos can be patched.

## Required secrets (org-level recommended)

In **StegVerse-Labs org secrets**:
- `GH_STEGVERSE_LABS_AI_TOKEN` → fine-grained PAT with access to StegVerse-Labs repos

In **StegVerse org secrets** (if you want cross-org):
- `GH_STEGVERSE_AI_TOKEN` → PAT with access to StegVerse repos

Repo-level secrets override org-level if present.

