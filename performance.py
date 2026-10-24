"""Performance metrics helpers."""

from __future__ import annotations

from typing import Dict, List


def append_speedup_efficiency(rows: List[Dict], serial_runtime: float) -> List[Dict]:
    enriched: List[Dict] = []
    for row in rows:
        runtime = float(row["runtime"])
        workers = int(row["workers"])
        if runtime <= 0:
            speedup = 0.0
        else:
            speedup = serial_runtime / runtime
        efficiency = speedup / workers if workers > 0 else 0.0

        out = dict(row)
        out["speedup"] = speedup
        out["efficiency"] = efficiency
        enriched.append(out)
    return enriched
