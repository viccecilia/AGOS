"""Runtime review session report generator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class RuntimeReviewSession:
    def __init__(self, root: str | Path = "runtime/runtime_reviews") -> None:
        self.root = Path(root)

    def generate(self, state: dict[str, Any], corrections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        corrections = corrections or []
        report = {
            "review_id": f"review_{state.get('cycle', 'cycle')}_{utc_now_iso().replace(':', '-')}",
            "workspace": state.get("workspace"),
            "cycle": state.get("cycle"),
            "created_at": utc_now_iso(),
            "learned": state.get("runtime_intelligence", {}).get("best_answer", []),
            "mislearned": corrections,
            "effective": state.get("runtime_intelligence", {}).get("best_hook", []),
            "ineffective": state.get("runtime_intelligence", {}).get("failed_strategy", []),
            "needs_human_correction": [item for item in corrections if item.get("status") in {"needs_human_review", "rejected"}],
        }
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{report['review_id']}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return report

    def list(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.root.glob("*.json"))]
