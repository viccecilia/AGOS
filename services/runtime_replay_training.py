"""Runtime replay training from historical AGOS intelligence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.batch_human_review import BatchHumanReview
from services.batch_scout_runtime import BatchScoutRuntime
from services.failure_analysis_engine import FailureAnalysisEngine
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.real_reply_attempt_engine import RealReplyAttemptEngine
from services.runtime_pattern_learning import RuntimePatternLearning
from services.runtime_persistence import utc_now_iso


REPLAY_SOURCE_TYPES = ["historical_question", "historical_reply", "historical_feedback", "historical_failure"]


class RuntimeReplayTraining:
    """Replay historical questions, replies, feedback, and failures into updated intelligence."""

    def __init__(self, root: str | Path = "runtime/replay_training") -> None:
        self.root = Path(root)
        self.report_path = self.root / "RUNTIME_REPLAY_TRAINING_REPORT.json"
        self.replay_items_path = self.root / "replay_training_items.json"
        self.replay_memory_path = self.root / "replay_memory.json"
        self.replay_feed_path = self.root / "runtime_replay_feed.json"
        self.summary_path = self.root / "replay_training_summary.json"

    def replay(self, sources: dict[str, Any] | None = None) -> dict[str, Any]:
        replay_sources = sources if sources is not None else self._default_sources()
        items = self._build_replay_items(replay_sources)
        replay_memory = [self._memory_record(index, item) for index, item in enumerate(items, start=1)]
        report = {
            "report_id": "RUNTIME_REPLAY_TRAINING_REPORT",
            "created_at": utc_now_iso(),
            "status": "runtime_replay_trained",
            "scope": "local_runtime_replay_training",
            "replaySourceTypes": REPLAY_SOURCE_TYPES,
            "replayTrainingItems": items,
            "replayMemory": replay_memory,
            "runtimeReplayFeed": self._feed(replay_memory),
            "replayTrainingSummary": self._summary(replay_memory),
            "safetyBoundary": "Runtime Replay Training replays local historical intelligence only. It does not post, reply, follow, DM, log in, register accounts, or call external write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.replay()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.replay_items_path.write_text(json.dumps(report["replayTrainingItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.replay_memory_path.write_text(json.dumps(report["replayMemory"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.replay_feed_path.write_text(json.dumps(report["runtimeReplayFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["replayTrainingSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _default_sources() -> dict[str, Any]:
        batch_runtime = BatchScoutRuntime().state()
        batch_review = BatchHumanReview().state()
        pattern_learning = RuntimePatternLearning().state()
        reply_attempts = RealReplyAttemptEngine().state()
        feedback_capture = RealFeedbackCaptureEngine().state()
        failure_analysis = FailureAnalysisEngine().state()
        return {
            "questions": batch_runtime.get("batchPriorityRanking", [])[:4],
            "reviews": batch_review.get("batchReviewQueue", [])[:4],
            "patterns": pattern_learning.get("patternMemory", [])[:4],
            "replies": reply_attempts.get("replyAttempts", [])[:4],
            "feedback": feedback_capture.get("feedbackEvents", [])[:4],
            "failures": failure_analysis.get("failureItems", [])[:4],
        }

    @staticmethod
    def _build_replay_items(sources: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for question in sources.get("questions", []):
            items.append(
                {
                    "source_type": "historical_question",
                    "source_id": question.get("question_id", question.get("batch_item_id", "")),
                    "topic": question.get("detected_topic", question.get("topic", "unknown")),
                    "evidence": question.get("why_important", question.get("question_text", "")),
                    "previous_signal": question.get("priority_band", "unknown"),
                    "replay_action": "re-evaluate question priority and route into pattern memory",
                }
            )
        for reply in sources.get("replies", []):
            items.append(
                {
                    "source_type": "historical_reply",
                    "source_id": reply.get("reply_attempt_id", reply.get("attempt_id", "")),
                    "topic": reply.get("platform", "reply_attempt"),
                    "evidence": reply.get("reply_text", reply.get("draft_text", "")),
                    "previous_signal": reply.get("status", "unknown"),
                    "replay_action": "re-evaluate reply outcome and update reply intelligence",
                }
            )
        for feedback in sources.get("feedback", []):
            items.append(
                {
                    "source_type": "historical_feedback",
                    "source_id": feedback.get("feedback_id", feedback.get("event_id", "")),
                    "topic": feedback.get("content_id", feedback.get("reply_attempt_id", "feedback")),
                    "evidence": RuntimeReplayTraining._feedback_evidence(feedback),
                    "previous_signal": feedback.get("feedback_type", feedback.get("status", "unknown")),
                    "replay_action": "replay feedback into engagement and conversion intelligence",
                }
            )
        for failure in sources.get("failures", []):
            items.append(
                {
                    "source_type": "historical_failure",
                    "source_id": failure.get("failure_id", failure.get("item_id", "")),
                    "topic": failure.get("failure_type", failure.get("topic", "failure")),
                    "evidence": failure.get("failure_reason", failure.get("reason", "")),
                    "previous_signal": failure.get("severity", failure.get("status", "unknown")),
                    "replay_action": "replay failure into risk and correction intelligence",
                }
            )
        for pattern in sources.get("patterns", []):
            items.append(
                {
                    "source_type": RuntimeReplayTraining._source_type_for_pattern(pattern),
                    "source_id": pattern.get("pattern_id", ""),
                    "topic": pattern.get("cluster_name", pattern.get("pattern_type", "pattern")),
                    "evidence": pattern.get("result_pattern", ""),
                    "previous_signal": pattern.get("pattern_type", "unknown"),
                    "replay_action": "replay learned pattern into updated runtime intelligence",
                }
            )
        return [item for item in items if item.get("source_id") or item.get("evidence")]

    @staticmethod
    def _source_type_for_pattern(pattern: dict[str, Any]) -> str:
        if pattern.get("pattern_type") == "high_risk":
            return "historical_failure"
        if pattern.get("pattern_type") in {"high_engagement", "high_conversion"}:
            return "historical_feedback"
        return "historical_question"

    @staticmethod
    def _feedback_evidence(feedback: dict[str, Any]) -> str:
        keys = ["liked", "replied", "ignored", "saved", "shared"]
        observed = [key for key in keys if feedback.get(key)]
        return "feedback observed: " + (", ".join(observed) if observed else "no strong interaction")

    @staticmethod
    def _memory_record(index: int, item: dict[str, Any]) -> dict[str, Any]:
        replay_result = RuntimeReplayTraining._replay_result(item)
        return {
            "replay_id": f"RUNTIME-REPLAY-{index:04d}",
            "source_type": item["source_type"],
            "source_id": item.get("source_id", ""),
            "topic": item.get("topic", "unknown"),
            "historical_evidence": item.get("evidence", ""),
            "previous_signal": item.get("previous_signal", "unknown"),
            "replay_action": item.get("replay_action", ""),
            "replay_result": replay_result,
            "updated_intelligence": RuntimeReplayTraining._updated_intelligence(item["source_type"], replay_result),
            "training_weight": RuntimeReplayTraining._training_weight(item["source_type"], replay_result),
            "status": "replayed",
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _replay_result(item: dict[str, Any]) -> str:
        source_type = item["source_type"]
        previous = str(item.get("previous_signal", "unknown"))
        if source_type == "historical_failure":
            return "risk_pattern_reinforced"
        if source_type == "historical_feedback" and any(signal in previous for signal in ["high", "saved", "replied", "high_engagement"]):
            return "engagement_pattern_reinforced"
        if source_type == "historical_reply":
            return "reply_strategy_retrained"
        return "question_priority_retrained"

    @staticmethod
    def _updated_intelligence(source_type: str, replay_result: str) -> str:
        if replay_result == "risk_pattern_reinforced":
            return "Increase caution for repeated weak, spam-like, or dangerous patterns."
        if replay_result == "engagement_pattern_reinforced":
            return "Promote signals that repeatedly create replies, saves, or useful engagement."
        if replay_result == "reply_strategy_retrained":
            return "Update reply drafting memory from historical approved, rejected, or modified attempts."
        return "Update question priority memory from repeated historical pain-point evidence."

    @staticmethod
    def _training_weight(source_type: str, replay_result: str) -> float:
        base = {
            "historical_question": 0.72,
            "historical_reply": 0.76,
            "historical_feedback": 0.86,
            "historical_failure": 0.9,
        }.get(source_type, 0.65)
        if replay_result in {"risk_pattern_reinforced", "engagement_pattern_reinforced"}:
            base += 0.08
        return round(min(base, 1.0), 2)

    @staticmethod
    def _summary(replay_memory: list[dict[str, Any]]) -> dict[str, Any]:
        sources = Counter(item["source_type"] for item in replay_memory)
        results = Counter(item["replay_result"] for item in replay_memory)
        return {
            "replay_items": len(replay_memory),
            "historical_questions": sources.get("historical_question", 0),
            "historical_replies": sources.get("historical_reply", 0),
            "historical_feedback": sources.get("historical_feedback", 0),
            "historical_failures": sources.get("historical_failure", 0),
            "question_priority_retrained": results.get("question_priority_retrained", 0),
            "reply_strategy_retrained": results.get("reply_strategy_retrained", 0),
            "engagement_pattern_reinforced": results.get("engagement_pattern_reinforced", 0),
            "risk_pattern_reinforced": results.get("risk_pattern_reinforced", 0),
            "replay_training_ready": bool(replay_memory),
        }

    @staticmethod
    def _feed(replay_memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["created_at"],
                "replay_id": item["replay_id"],
                "source_type": item["source_type"],
                "topic": item["topic"],
                "previous_signal": item["previous_signal"],
                "replay_result": item["replay_result"],
                "updated_intelligence": item["updated_intelligence"],
                "training_weight": item["training_weight"],
                "status": item["status"],
            }
            for item in replay_memory
        ]


if __name__ == "__main__":
    result = RuntimeReplayTraining().replay()
    print(json.dumps({"status": result["status"], "items": result["replayTrainingSummary"]["replay_items"]}, indent=2))
