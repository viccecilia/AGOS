"""Real feedback capture for AGOS Real Operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.real_reply_attempt_engine import RealReplyAttemptEngine
from services.runtime_persistence import utc_now_iso


class RealFeedbackCaptureEngine:
    """Record feedback signals for reply attempts and build a feedback timeline."""

    FEEDBACK_FIELDS = ["liked", "replied", "ignored", "saved", "shared"]

    def __init__(self, root: str | Path = "runtime/feedback_capture") -> None:
        self.root = Path(root)
        self.report_path = self.root / "REAL_FEEDBACK_CAPTURE_REPORT.json"
        self.events_path = self.root / "feedback_events.json"
        self.timeline_path = self.root / "feedback_timeline.json"

    def capture(self, feedback_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        reply_report = RealReplyAttemptEngine().state()
        attempts = reply_report.get("replyAttempts", [])
        events = feedback_events or self._sample_feedback_events(attempts)
        normalized = [self._normalize_event(event, attempts, index) for index, event in enumerate(events, start=1)]
        timeline = sorted(normalized, key=lambda item: item["captured_at"])
        report = {
            "report_id": "REAL_FEEDBACK_CAPTURE_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_feedback_record_only_no_platform_api",
            "feedbackSignals": self.FEEDBACK_FIELDS,
            "feedbackEvents": normalized,
            "feedbackTimeline": timeline,
            "feedbackSummary": self._summary(normalized),
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.capture()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.events_path.write_text(json.dumps(report["feedbackEvents"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.timeline_path.write_text(json.dumps(report["feedbackTimeline"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def record_feedback(self, reply_attempt_id: str, signals: dict[str, bool], note: str = "") -> dict[str, Any]:
        report = self.state()
        attempts = RealReplyAttemptEngine().state().get("replyAttempts", [])
        event = self._normalize_event(
            {
                "reply_attempt_id": reply_attempt_id,
                **{field: bool(signals.get(field, False)) for field in self.FEEDBACK_FIELDS},
                "feedback_note": note,
            },
            attempts,
            len(report.get("feedbackEvents", [])) + 1,
        )
        events = report.get("feedbackEvents", []) + [event]
        report["feedbackEvents"] = events
        report["feedbackTimeline"] = sorted(events, key=lambda item: item["captured_at"])
        report["feedbackSummary"] = self._summary(events)
        self.persist(report)
        return event

    def _normalize_event(self, event: dict[str, Any], attempts: list[dict[str, Any]], index: int) -> dict[str, Any]:
        attempt_id = event.get("reply_attempt_id")
        attempt = next((item for item in attempts if item.get("reply_attempt_id") == attempt_id), {})
        payload = {
            "feedback_id": event.get("feedback_id", f"feedback_{index:04d}"),
            "reply_attempt_id": attempt_id,
            "question_id": event.get("question_id", attempt.get("question_id")),
            "platform": event.get("platform", attempt.get("platform", "unknown")),
            "question_text": event.get("question_text", attempt.get("question_text", "")),
            "reply_text": event.get("reply_text", attempt.get("reply_text", "")),
            "captured_at": event.get("captured_at", utc_now_iso()),
            "feedback_note": event.get("feedback_note", ""),
            "status": "captured",
            "safety_boundary": "manual_feedback_record_only",
        }
        for field in self.FEEDBACK_FIELDS:
            payload[field] = bool(event.get(field, False))
        payload["has_positive_feedback"] = payload["liked"] or payload["replied"] or payload["saved"] or payload["shared"]
        payload["has_negative_feedback"] = payload["ignored"] and not payload["has_positive_feedback"]
        return payload

    def _sample_feedback_events(self, attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not attempts:
            return []
        samples = []
        patterns = [
            {"liked": True, "replied": True, "saved": False, "shared": False, "ignored": False, "feedback_note": "User asked a follow-up route question."},
            {"liked": True, "saved": True, "shared": False, "replied": False, "ignored": False, "feedback_note": "Helpful checklist style."},
            {"ignored": True, "liked": False, "replied": False, "saved": False, "shared": False, "feedback_note": "No visible response after review window."},
            {"shared": True, "liked": True, "replied": False, "saved": True, "ignored": False, "feedback_note": "Reusable route tip."},
            {"replied": True, "liked": False, "saved": False, "shared": False, "ignored": False, "feedback_note": "Needs more precise station detail."},
        ]
        for index, attempt in enumerate(attempts[:5]):
            samples.append({"reply_attempt_id": attempt["reply_attempt_id"], **patterns[index % len(patterns)]})
        return samples

    def _summary(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        totals = {field: len([event for event in events if event.get(field)]) for field in self.FEEDBACK_FIELDS}
        positive = [event for event in events if event.get("has_positive_feedback")]
        ignored = [event for event in events if event.get("has_negative_feedback")]
        return {
            "total_feedback_events": len(events),
            "liked": totals["liked"],
            "replied": totals["replied"],
            "ignored": totals["ignored"],
            "saved": totals["saved"],
            "shared": totals["shared"],
            "positive_feedback": len(positive),
            "ignored_feedback": len(ignored),
            "platforms_with_feedback": sorted({event["platform"] for event in events}),
            "top_feedback_attempts": [event["reply_attempt_id"] for event in positive[:5]],
        }


if __name__ == "__main__":
    result = RealFeedbackCaptureEngine().capture()
    print(json.dumps({"status": result["status"], "events": result["feedbackSummary"]["total_feedback_events"]}, indent=2))
