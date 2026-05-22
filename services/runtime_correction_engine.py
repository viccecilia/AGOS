"""Human correction and mislearning detection for Runtime Training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class RuntimeCorrectionEngine:
    def __init__(self, root: str | Path = "runtime/runtime_state") -> None:
        self.root = Path(root)
        self.path = self.root / "corrections.json"

    def detect_mislearning(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        text = f"{item.get('reply_text', '')} {item.get('hook', '')} {item.get('strategy', '')}".lower()
        alerts: list[dict[str, Any]] = []
        checks = [
            ("标题党风险", ["shocking", "你绝对想不到", "必须看"], "needs_human_review"),
            ("过度营销风险", ["buy now", "立刻购买", "limited offer"], "needs_human_review"),
            ("情绪过度风险", ["panic", "崩溃", "灾难"], "needs_human_review"),
            ("平台人格错乱", ["reddit短视频", "tiktok长论文"], "needs_human_review"),
            ("Workspace 污染", ["philips", "air fryer", "家电"], "needs_code_check"),
            ("内容重复", ["same hook repeated", "重复hook"], "needs_human_review"),
        ]
        for issue, tokens, status in checks:
            if any(token in text for token in tokens):
                alerts.append(
                    {
                        "issue": issue,
                        "status": status,
                        "severity": "high" if status == "needs_code_check" else "medium",
                        "signal": f"Detected token in runtime item: {issue}",
                        "action": "进入人工纠偏，不写入最佳学习",
                    }
                )
        return alerts

    def reject(self, correction: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "correction_id": correction.get("correction_id") or f"correction_{utc_now_iso().replace(':', '-')}",
            "target_type": correction.get("target_type", "learning"),
            "target_id": correction.get("target_id", "unknown"),
            "reason": correction.get("reason", ""),
            "rejected_learning": correction.get("rejected_learning", {}),
            "status": "rejected",
            "created_at": utc_now_iso(),
        }
        items = self.list()
        items.append(payload)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return payload

    def list(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))
