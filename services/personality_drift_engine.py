"""Personality drift detection for AGOS operating style."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class PersonalityDriftEngine:
    def __init__(self, root: str | Path = "runtime/personality_drift") -> None:
        self.root = Path(root)
        self.alerts_path = self.root / "personality_drift_alerts.json"

    def detect(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        text = json.dumps(item, ensure_ascii=False).lower()
        checks = [
            ("过度营销", ["buy now", "limited offer", "must buy", "硬广", "立刻购买"], "needs_human_review"),
            ("过度情绪化", ["panic", "fear", "shocking", "过度情绪", "焦虑放大"], "needs_human_review"),
            ("平台人格错乱", ["reddit short hook", "tiktok long essay", "reddit 短促带货", "平台人格错乱"], "needs_human_review"),
            ("clickbait", ["you won't believe", "secret trick", "标题党", "震惊"], "needs_human_review"),
            ("机械回复", ["generic reply", "template answer", "as an ai", "模板化", "机械回复"], "needs_human_review"),
            ("内容重复", ["same hook repeated", "duplicate content", "重复内容", "重复 hook"], "needs_human_review"),
        ]
        alerts: list[dict[str, Any]] = []
        for issue, tokens, status in checks:
            matched = [token for token in tokens if token in text]
            if matched:
                alerts.append(
                    {
                        "alert_id": f"personality_drift_{utc_now_iso().replace(':', '-')}_{len(alerts) + 1}",
                        "issue": issue,
                        "status": status,
                        "severity": "high" if issue in {"平台人格错乱", "过度营销"} else "medium",
                        "reason": f"Detected personality drift tokens: {', '.join(matched)}",
                        "matched_tokens": matched,
                        "created_at": utc_now_iso(),
                        "action": "进入人工纠偏；不要把该人格样式沉淀为最佳人格。",
                    }
                )
        if alerts:
            self.root.mkdir(parents=True, exist_ok=True)
            history = self.history()
            history.extend(alerts)
            self.alerts_path.write_text(json.dumps(history, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return alerts

    def history(self) -> list[dict[str, Any]]:
        if not self.alerts_path.exists():
            return []
        return json.loads(self.alerts_path.read_text(encoding="utf-8"))

    def summary(self) -> dict[str, Any]:
        alerts = self.history()
        return {
            "personalityDriftAlerts": alerts[-20:],
            "personalityDriftStatus": "needs_human_review" if alerts else "clear",
            "latestDriftReason": alerts[-1]["reason"] if alerts else "",
        }
