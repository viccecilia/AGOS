"""Runtime drift monitoring for human-gated AGOS training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class RuntimeDriftMonitor:
    def __init__(self, root: str | Path = "runtime/review_sessions") -> None:
        self.root = Path(root)
        self.path = self.root / "runtime_drift_events.json"

    def detect(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        text = json.dumps(item, ensure_ascii=False).lower()
        checks = [
            ("spam tendency", ["buy now", "limited offer", "click here", "dm me", "follow for more"], "needs_human_review"),
            ("platform personality drift", ["reddit short hook", "tiktok long essay", "x long essay", "emotional spam pattern"], "needs_human_review"),
            ("workspace pollution", ["philips", "air fryer", "home appliance"], "needs_code_check"),
            ("content repetition", ["same hook repeated", "repeat hook", "duplicate content"], "needs_human_review"),
            ("over marketing", ["guaranteed", "best ever", "must buy"], "needs_human_review"),
            ("clickbait tendency", ["shocking", "you won't believe", "secret trick"], "needs_human_review"),
            ("learning bias", ["always reply", "everything is high value"], "needs_human_review"),
        ]
        events: list[dict[str, Any]] = []
        for issue, tokens, status in checks:
            if any(token in text for token in tokens):
                events.append(
                    {
                        "drift_id": f"drift_{utc_now_iso().replace(':', '-')}_{len(events) + 1}",
                        "issue": issue,
                        "status": status,
                        "severity": "high" if status == "needs_code_check" else "medium",
                        "signal": f"Detected {issue}",
                        "action": "Send to human review before learning or publishing.",
                        "created_at": utc_now_iso(),
                    }
                )
        if events:
            self.root.mkdir(parents=True, exist_ok=True)
            history = self.history()
            history.extend(events)
            self.path.write_text(json.dumps(history, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return events

    def history(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def summary(self) -> dict[str, Any]:
        events = self.history()
        return {
            "runtimeDriftEvents": events[-20:],
            "runtimeDriftStatus": "needs_human_review" if any(item.get("status") == "needs_human_review" for item in events) else "clear",
            "needsCodeCheck": any(item.get("status") == "needs_code_check" for item in events),
        }
