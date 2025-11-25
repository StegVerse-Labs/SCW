"""
=== STEGVERSE FILE METADATA ===
sv_file: scw/org_health.py
sv_kind: python
sv_module: SCW
sv_version: 4.0.0
sv_build_id: 20251125-000000Z
sv_epoch: 9
sv_parent_build: 20251124-000000Z
sv_hash: auto
sv_sig: svmeta:v1
=== END STEGVERSE FILE METADATA ===

SCW Org Health (v4)

Key upgrades:
- Index-first scan (fast)
- Structure vs logic queues (safe)
- svmeta-based staleness decisions
- Fix queue with pending-perms retry
- Writes/updates scw/file_index.json per repo touched (when autofixing)

This module is called by scw_core.py.
"""

from __future__ import annotations

import os, json, fnmatch, hashlib, datetime as dt, pathlib, re
from typing import Dict, List, Any, Optional, Tuple
import requests
import yaml

from .svmeta import SvMeta, compare, strip_metadata
from .risk import RiskInputs, score as risk_score

API = "https://api.github.com"

def log(msg): print(f"[ORG_HEALTH] {msg}", flush=True)

def gh_headers(token:str)->dict:
    return {"Authorization": f"Bearer {token}",
            "Accept":"application/vnd.github+json",
            "User-Agent":"StegVerse-SCW-v4"}

def gh_get(token, path, params=None):
    r = requests.get(f"{API}{path}", headers=gh_headers(token), params=params, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub GET {path} failed: {r.status_code} {r.text[:200]}")
    return r.json()

def gh_put(token, path, data):
    r = requests.put(f"{API}{path}", headers=gh_headers(token), json=data, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub PUT {path} failed: {r.status_code} {r.text[:200]}")
    return r.json()

def glob_any(name:str, patterns:List[str])->bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)

def load_policy(root: pathlib.Path) -> dict:
    p = root / "scw" / "policy.yml"
    return yaml.safe_load(p.read_text())

def list_org_repos(token:str, org:str):
    repos=[]
    page=1
    while True:
        batch = gh_get(token, f"/orgs/{org}/repos", {"per_page":100,"page":page,"type":"all"})
        if not batch: break
        repos.extend(batch); page+=1
        if page>10: break
    return repos

def repo_default_branch(token:str, full_name:str)->str:
    owner, repo = full_name.split("/")
    info = gh_get(token, f"/repos/{owner}/{repo}")
    return info.get("default_branch","main")

def get_file(token:str, full_name:str, path:str, ref:str)->Optional[str]:
    owner, repo = full_name.split("/")
    try:
        blob = gh_get(token, f"/repos/{owner}/{repo}/contents/{path}", {"ref":ref})
        if blob.get("type") != "file":
            return None
        import base64
        return base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
    except Exception:
        return None

def content_hash(txt:str)->str:
    h = hashlib.sha256(strip_metadata(txt).encode("utf-8")).hexdigest()
    return f"sha256:{h}"

def parse_index(txt:str)->Optional[dict]:
    try:
        return json.loads(txt)
    except Exception:
        return None

def read_index_if_present(token, full_name, ref)->Optional[dict]:
    idx_txt = get_file(token, full_name, "scw/file_index.json", ref)
    if not idx_txt: return None
    data = parse_index(idx_txt)
    if not data or data.get("sv_index_sig") != "fileindex:v1":
        return None
    return data

def staleness(policy_epoch:int, min_ver:str, meta:SvMeta)->bool:
    if meta.sv_epoch < policy_epoch: return True
    # semver compare
    def semver_tuple(v): 
        parts=v.split("."); 
        return tuple(int(x) if x.isdigit() else 0 for x in (parts+["0","0","0"])[:3])
    if semver_tuple(meta.sv_version) < semver_tuple(min_ver): return True
    return False

def build_required_map(policy:dict)->Dict[str,dict]:
    return {f["path"]:f for f in policy["required_files"]}

def scan_repo(token:str, full_name:str, policy:dict)->dict:
    ref = repo_default_branch(token, full_name)
    required = build_required_map(policy)
    policy_epoch = policy["policy_epoch"]

    # Index-first
    index = read_index_if_present(token, full_name, ref) if policy["scan"]["index_first"] else None

    report = {
        "repo": full_name,
        "ref": ref,
        "scanned_utc": dt.datetime.utcnow().isoformat()+"Z",
        "structure_queue": [],
        "logic_queue": [],
        "notes": [],
        "index_present": bool(index),
    }

    def queue_item(path, action, reason, meta=None, depends=None, risk=0.0):
        item = {
            "path": path,
            "action": action,   # add/replace/triage
            "reason": reason,
            "wanted_epoch": policy_epoch,
            "wanted_version": policy["min_versions"].get("workflow","0.0.0"),
            "meta_found": meta.__dict__ if meta else {},
            "depends_on_secrets": depends or [],
            "risk_score": risk,
        }
        is_structure = glob_any(path, policy["structure_allowlist_globs"])
        (report["structure_queue"] if is_structure else report["logic_queue"]).append(item)

    # Use index data if possible
    file_states = {}
    if index:
        for f in index.get("files",[]):
            file_states[f["path"]] = f

    # Required files checks
    for path, spec in required.items():
        depends = spec.get("depends_on_secrets", [])
        min_ver = policy["min_versions"].get("workflow","0.0.0")

        if index and path in file_states:
            # index says file exists with meta summary
            meta = SvMeta(
                sv_file=path,
                sv_kind=file_states[path].get("kind",""),
                sv_module=file_states[path].get("module",""),
                sv_version=file_states[path].get("sv_version","0.0.0"),
                sv_build_id=file_states[path].get("sv_build_id",""),
                sv_epoch=int(file_states[path].get("sv_epoch",0)),
                sv_hash=file_states[path].get("sv_hash",""),
            )
            if staleness(policy_epoch, min_ver, meta):
                r = risk_score(RiskInputs(freshness_risk=1.0))
                queue_item(path, "replace", "stale_metadata(index)", meta, depends, r)
        else:
            # fall back to tree read for required paths
            txt = get_file(token, full_name, path, ref)
            if not txt:
                r = risk_score(RiskInputs(freshness_risk=1.0))
                queue_item(path, "add", "missing_required", None, depends, r)
                continue
            meta = SvMeta.from_text(txt)
            if staleness(policy_epoch, min_ver, meta):
                r = risk_score(RiskInputs(freshness_risk=1.0))
                queue_item(path, "replace", "stale_metadata(tree)", meta, depends, r)

    return report

def scan_org(token:str, orgs:List[str], policy:dict)->dict:
    out = {
        "sig":"orgscan:v4",
        "generated_utc": dt.datetime.utcnow().isoformat()+"Z",
        "policy_epoch": policy["policy_epoch"],
        "repos": [],
        "fix_queue": {"sig":"fixqueue:v1","items":[]}
    }

    for org in orgs:
        log(f"Scanning org {org}...")
        repos = list_org_repos(token, org)
        for r in repos:
            full = r["full_name"]
            if glob_any(full, policy.get("exclude_repos_globs", [])):
                continue
            rep = scan_repo(token, full, policy)
            out["repos"].append(rep)

            # Accumulate fix queue from structure+logic (logic queued as triage only)
            for item in rep["structure_queue"]:
                out["fix_queue"]["items"].append({
                    "repo": full,
                    "path": item["path"],
                    "action": item["action"],
                    "reason": item["reason"],
                    "wanted_epoch": item["wanted_epoch"],
                    "wanted_version": item["wanted_version"],
                    "status": "pending",
                    "last_attempt_utc": None,
                    "risk_score": item["risk_score"],
                })
            for item in rep["logic_queue"]:
                out["fix_queue"]["items"].append({
                    "repo": full,
                    "path": item["path"],
                    "action": "triage",
                    "reason": item["reason"],
                    "wanted_epoch": item["wanted_epoch"],
                    "wanted_version": item["wanted_version"],
                    "status": "triage",
                    "last_attempt_utc": None,
                    "risk_score": item["risk_score"],
                })

    return out

def main():
    root = pathlib.Path(os.getenv("GITHUB_WORKSPACE","."))
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Missing GH_TOKEN")
    policy = load_policy(root)
    orgs = os.getenv("SCW_ORGS","StegVerse,StegVerse-Labs").split(",")

    report = scan_org(token, [o.strip() for o in orgs if o.strip()], policy)

    (root/"reports").mkdir(exist_ok=True)
    out_path = root/"reports"/"org_scan.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
