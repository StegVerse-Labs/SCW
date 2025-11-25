"""
=== STEGVERSE FILE METADATA ===
sv_file: scw/risk.py
sv_kind: python
sv_module: SCW
sv_version: 4.0.0
sv_build_id: 20251125-000000Z
sv_epoch: 9
sv_parent_build: none
sv_hash: auto
sv_sig: svmeta:v1
=== END STEGVERSE FILE METADATA ===

Risk scoring hooks (v1).
Used by org_health to prioritize fix queue items.
"""

from __future__ import annotations

from dataclasses import dataclass

@dataclass
class RiskInputs:
    freshness_risk: float = 0.0   # 0..1
    usage_risk: float = 0.0       # 0..1
    fail_adjacent_risk: float = 0.0  # 0..1
    dep_volatility_risk: float = 0.0  # 0..1
    proximal_multiplier: float = 1.0

def score(inp: RiskInputs, stale_multiplier=1.5, high_usage_multiplier=1.4, failure_adjacent_multiplier=1.3) -> float:
    base = (
        inp.freshness_risk * stale_multiplier +
        inp.usage_risk * high_usage_multiplier +
        inp.fail_adjacent_risk * failure_adjacent_multiplier +
        inp.dep_volatility_risk
    )
    return base * inp.proximal_multiplier
