# StegVerse SCW (StegVerse Code Worker)

SCW is the StegVerse root orchestrator. It receives commands (via workflow_dispatch or /scw issue comments),
runs validations, and will progressively host Guardians (Autopatch, Readme, Governance, Continuity, Deploy).

## Workflows

- **SCW Orchestrator**: `.github/workflows/scw_orchestrator.yml`
  - Run from Actions tab.
  - Commands: `self-test`, `autopatch`, `sync-templates`, `standardize-readme`.

- **SCW Bridge**: `.github/workflows/scw_bridge.yml`
  - Listen for `/scw <command> [json]` in issues/comments in any repo.

## Setup

1. Ensure org secret `GH_STEGVERSE_AI_TOKEN` exists in **StegVerse-Labs**.
2. Ensure repos are public or org plan allows org secrets for private repos.
3. Run **SCW Orchestrator → self-test**.

## Roadmap

Phase 2 will add real template syncing and autopatch PR generation.
