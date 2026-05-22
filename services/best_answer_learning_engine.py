"""Best answer learning for AGOS Real Operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.runtime_persistence import utc_now_iso


class BestAnswerLearningEngine:
    """Learn best and failed answer patterns from captured feedback."""

    def __init__(self, root: str | Path = "runtime/best_answer_learning") -> None:
        self.root = Path(root)
        self.report_path = self.root / "BEST_ANSWER_LEARNING_REPORT.json"
        self.memory_path = self.root / "best_answer_memory.json"
        self.timeline_path = self.root / "answer_learning_timeline.json"

    def learn(self, feedback_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        feedback_report = RealFeedbackCaptureEngine().state()
        events = feedback_events or feedback_report.get("feedbackEvents", [])
        scored = [self._score_event(event) for event in events]
        best = sorted([item for item in scored if item["feedback_score"] > 0], key=lambda item: item["feedback_score"], reverse=True)
        failed = [item for item in scored if item["ignored"] and item["feedback_score"] <= 0]
        memory = {
            "bestAnswer": best[0] if best else None,
            "bestHook": self._best_hook(best),
            "bestTone": self._best_tone(best),
            "bestPlatformStyle": self._best_platform_style(best),
            "failedAnswers": failed,
            "failedHooks": self._failed_hooks(failed),
            "failedStrategies": self._failed_strategies(failed),
        }
        timeline = self._timeline(best, failed)
        report = {
            "report_id": "BEST_ANSWER_LEARNING_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_learning_from_feedback_only",
            "learningInputs": {
                "feedback_events": len(events),
                "positive_events": len(best),
                "failed_events": len(failed),
            },
            "bestAnswerLearning": memory,
            "answerLearningTimeline": timeline,
            "learningSummary": {
                "best_answer_id": memory["bestAnswer"]["reply_attempt_id"] if memory["bestAnswer"] else "none",
                "best_hook": memory["bestHook"],
                "best_tone": memory["bestTone"],
                "best_platform_style": memory["bestPlatformStyle"],
                "failed_answer_count": len(failed),
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.learn()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.memory_path.write_text(json.dumps(report["bestAnswerLearning"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.timeline_path.write_text(json.dumps(report["answerLearningTimeline"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _score_event(event: dict[str, Any]) -> dict[str, Any]:
        score = 0
        score += 2 if event.get("liked") else 0
        score += 3 if event.get("replied") else 0
        score += 3 if event.get("saved") else 0
        score += 4 if event.get("shared") else 0
        score -= 2 if event.get("ignored") else 0
        return {
            **event,
            "feedback_score": score,
            "learned_at": utc_now_iso(),
            "answer_pattern": BestAnswerLearningEngine._answer_pattern(event),
            "hook_pattern": BestAnswerLearningEngine._hook_pattern(event),
            "tone": BestAnswerLearningEngine._tone_for(event),
            "platform_style": BestAnswerLearningEngine._platform_style(event),
        }

    @staticmethod
    def _answer_pattern(event: dict[str, Any]) -> str:
        if event.get("saved") or event.get("shared"):
            return "specific checklist or reusable route tip"
        if event.get("replied"):
            return "reply that invites a practical follow-up"
        if event.get("liked"):
            return "concise helpful answer"
        return "low-response answer"

    @staticmethod
    def _hook_pattern(event: dict[str, Any]) -> str:
        text = event.get("question_text", "").lower()
        if "station" in text or "train" in text or "subway" in text:
            return "reduce transit uncertainty first"
        if "suica" in text or "cash" in text:
            return "make payment decision simple"
        return "name the practical travel pain clearly"

    @staticmethod
    def _tone_for(event: dict[str, Any]) -> str:
        if event.get("platform") == "Reddit":
            return "detailed, calm, non-promotional"
        if event.get("platform") == "TikTok":
            return "short, reassuring, practical"
        return "concise, useful, low-hype"

    @staticmethod
    def _platform_style(event: dict[str, Any]) -> str:
        platform = event.get("platform", "unknown")
        if platform == "Reddit":
            return "longer practical explanation"
        if platform == "TikTok":
            return "comment-sized checklist"
        if platform == "X":
            return "compact advice thread"
        return "local review style"

    @staticmethod
    def _best_hook(best: list[dict[str, Any]]) -> str:
        return best[0]["hook_pattern"] if best else "none"

    @staticmethod
    def _best_tone(best: list[dict[str, Any]]) -> str:
        return best[0]["tone"] if best else "none"

    @staticmethod
    def _best_platform_style(best: list[dict[str, Any]]) -> str:
        return best[0]["platform_style"] if best else "none"

    @staticmethod
    def _failed_hooks(failed: list[dict[str, Any]]) -> list[str]:
        return sorted({item["hook_pattern"] for item in failed})

    @staticmethod
    def _failed_strategies(failed: list[dict[str, Any]]) -> list[str]:
        return ["generic answer without visible follow-up"] if failed else []

    @staticmethod
    def _timeline(best: list[dict[str, Any]], failed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline = []
        for item in best[:5]:
            timeline.append(
                {
                    "time": item["learned_at"],
                    "type": "best_answer_learning",
                    "reply_attempt_id": item["reply_attempt_id"],
                    "platform": item["platform"],
                    "score": item["feedback_score"],
                    "learned": item["answer_pattern"],
                    "status": "learned",
                }
            )
        for item in failed[:5]:
            timeline.append(
                {
                    "time": item["learned_at"],
                    "type": "failed_answer_learning",
                    "reply_attempt_id": item["reply_attempt_id"],
                    "platform": item["platform"],
                    "score": item["feedback_score"],
                    "learned": "Avoid low-specificity replies that get ignored.",
                    "status": "failed",
                }
            )
        return timeline


if __name__ == "__main__":
    result = BestAnswerLearningEngine().learn()
    print(json.dumps({"status": result["status"], "best": result["learningSummary"]["best_answer_id"]}, indent=2))
