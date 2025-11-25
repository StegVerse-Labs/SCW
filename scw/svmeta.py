"""
=== STEGVERSE FILE METADATA ===
sv_file: scw/svmeta.py
sv_kind: python
sv_module: SCW
sv_version: 4.0.0
sv_build_id: 20251125-000000Z
sv_epoch: 9
sv_parent_build: none
sv_hash: auto
sv_sig: svmeta:v1
=== END STEGVERSE FILE METADATA ===

svmeta parser + comparator.

- Extracts STEGVERSE FILE METADATA blocks from YAML/MD/PY.
- Computes ordering (epoch > semver > build_id).
- Supports hash-excluding-metadata (optional).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

META_RE = re.compile(
    r"(?:^|\n)(?:#|\")\s*===\s*STEGVERSE FILE METADATA\s*===\s*(.*?)"
    r"(?:#|\")\s*===\s*END STEGVERSE FILE METADATA\s*===\s*",
    re.DOTALL | re.IGNORECASE
)

KV_RE = re.compile(r"^\s*(sv_[a-z0-9_]+)\s*:\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)

def parse_semver(v: str) -> Tuple[int, int, int]:
    try:
        parts = v.strip().split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return (0, 0, 0)

@dataclass
class SvMeta:
    sv_file: str = ""
    sv_kind: str = ""
    sv_module: str = ""
    sv_version: str = "0.0.0"
    sv_build_id: str = "00000000-000000Z"
    sv_epoch: int = 0
    sv_parent_build: str = ""
    sv_hash: str = ""
    sv_sig: str = ""

    @staticmethod
    def from_text(txt: str) -> "SvMeta":
        m = META_RE.search(txt)
        if not m:
            return SvMeta()
        block = m.group(1)
        kv = {k.lower(): v.strip().strip('"') for k, v in KV_RE.findall(block)}
        return SvMeta(
            sv_file=kv.get("sv_file", ""),
            sv_kind=kv.get("sv_kind", ""),
            sv_module=kv.get("sv_module", ""),
            sv_version=kv.get("sv_version", "0.0.0"),
            sv_build_id=kv.get("sv_build_id", "00000000-000000Z"),
            sv_epoch=int(kv.get("sv_epoch", "0") or 0),
            sv_parent_build=kv.get("sv_parent_build", ""),
            sv_hash=kv.get("sv_hash", ""),
            sv_sig=kv.get("sv_sig", "")
        )

    def ordering_key(self) -> Tuple[int, Tuple[int,int,int], str]:
        return (self.sv_epoch, parse_semver(self.sv_version), self.sv_build_id)

def compare(a: SvMeta, b: SvMeta) -> int:
    """Return 1 if a newer, -1 if older, 0 if same."""
    ka, kb = a.ordering_key(), b.ordering_key()
    if ka > kb: return 1
    if ka < kb: return -1
    return 0

def strip_metadata(txt: str) -> str:
    """Remove metadata block for stable content hashing."""
    return META_RE.sub("", txt)
