"""24-hour personality review session reporting."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from services.personality_drift_engine import PersonalityDriftEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.runtime_persistence import utc_now_iso


class PersonalityReviewSession:
    """Summarize recent personality change, drift, and tone outcomes."""

    def __init__(self, root: str | Path = "runtime/personality_reviews") -> None:
        self.root = Path(root)
        self.report_path = self.root / "PERSONALITY_REVIEW_SESSION_REPORT.json"
        self.history_path = self.root / "personality_review_sessions.json"

    def generate(self, window_hours: int = 24) -> dict[str, Any]:
        memory_status = PersonalityMemoryDeposit().status()
        drift_summary = PersonalityDriftEngine().summary()
        timeline = memory_status.get("personalityTimeline", [])
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        recent_timeline = [item for item in timeline if self._in_window(item.get("created_at"), cutoff)]
        recent_drift = [
            item
            for item in drift_summary.get("personalityDriftAlerts", [])
            if self._in_window(item.get("created_at"), cutoff)
        ]
        best_personality = memory_status.get("bestPersonality", {})
        failed_personality = memory_status.get("failedPersonality", {})
        failed_tone = failed_personality.get("tone") or (memory_status.get("rejectedTone", [{}])[-1] or {}).get("tone", "")
        trend = self._trend(recent_timeline, recent_drift, best_personality, failed_tone)
        report = {
            "report_id": "PERSONALITY_REVIEW_SESSION_REPORT",
            "created_at": utc_now_iso(),
            "window_hours": window_hours,
            "status": "needs_human_review" if recent_drift else "clear",
            "recentDrift": recent_drift,
            "recentBestPersonality": best_personality,
            "recentFailedTone": failed_tone or "none",
            "recentFailedPersonality": failed_personality,
            "personalityTrend": trend,
            "timelineEventsReviewed": len(recent_timeline),
            "driftEventsReviewed": len(recent_drift),
            "reviewSummary": self._summary(trend, recent_drift, best_personality, failed_tone),
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.generate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        history: list[dict[str, Any]] = []
        if self.history_path.exists():
            history = json.loads(self.history_path.read_text(encoding="utf-8"))
        history.append(report)
        self.history_path.write_text(json.dumps(history[-30:], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _in_window(value: str | None, cutoff: datetime) -> bool:
        if not value:
            return True
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized) >= cutoff
        except ValueError:
            return True

    @staticmethod
    def _trend(
        recent_timeline: list[dict[str, Any]],
        recent_drift: list[dict[str, Any]],
        best_personality: dict[str, Any],
        failed_tone: str,
    ) -> list[dict[str, Any]]:
        approved = [item for item in recent_timeline if item.get("type") == "approved_personality"]
        failed = [item for item in recent_timeline if item.get("type") == "failed_personality"]
        return [
            {
                "signal": "approved_personality",
                "status": "improving" if approved else "waiting",
                "count": len(approved),
                "summary": best_personality.get("tone", "trusted_guide") or "trusted_guide",
            },
            {
                "signal": "failed_tone",
                "status": "needs_human_review" if failed_tone and failed_tone != "none" else "clear",
                "count": len(failed),
                "summary": failed_tone or "none",
            },
            {
                "signal": "personality_drift",
                "status": "needs_human_review" if recent_drift else "clear",
                "count": len(recent_drift),
                "summary": recent_drift[-1].get("reason", "no recent drift") if recent_drift else "no recent drift",
            },
        ]

    @staticmethod
    def _summary(
        trend: list[dict[str, Any]],
        recent_drift: list[dict[str, Any]],
        best_personality: dict[str, Any],
        failed_tone: str,
    ) -> str:
        best = best_personality.get("tone", "trusted_guide") or "trusted_guide"
        if recent_drift:
            return f"Recent drift exists. Keep {best} as the preferred personality and review failed tone {failed_tone or 'none'}."
        return f"Personality trend is stable. Best personality remains {best}; failed tone is {failed_tone or 'none'}."
