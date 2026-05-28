"""Monitor drift between expected external results and manual feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.external_action_sandbox import ExternalActionSandbox
from services.manual_external_feedback_intake import ManualExternalFeedbackIntake
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.runtime_persistence import utc_now_iso
from services.strategy_evolution_engine import StrategyEvolutionEngine


DEFAULT_OUTPUT_DIR = Path("runtime/external_drift_monitor")
DRIFT_TYPES = ["strategy_drift", "platform_drift", "audience_drift", "tone_drift"]


class ExternalDriftMonitor:
    """Detect external promotion drift without changing execution strategy."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.signals_path = self.output_dir / "external_drift_signals.json"
        self.report_path = self.output_dir / "EXTERNAL_DRIFT_REPORT.json"
        self.summary_path = self.output_dir / "external_drift_summary.json"
        self.recommendations_path = self.output_dir / "external_drift_recommendations.json"

    def monitor(
        self,
        expected_actions: list[dict[str, Any]] | None = None,
        manual_feedback: list[dict[str, Any]] | None = None,
        strategy_state: dict[str, Any] | None = None,
        feedback_learning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sandbox = ExternalActionSandbox().state()
        expected_actions = expected_actions if expected_actions is not None else sandbox.get("externalActionSimulations", [])
        if manual_feedback is None:
            manual_feedback = ManualExternalFeedbackIntake().state().get("manualExternalFeedbackRecords", [])
        strategy_state = strategy_state or StrategyEvolutionEngine().state()
        feedback_learning = feedback_learning or PromotionFeedbackLearning().state()

        signals = self._signals(expected_actions, manual_feedback, strategy_state, feedback_learning)
        recommendations = [self._recommendation(signal, index + 1) for index, signal in enumerate(signals)]
        summary = self._summary(signals, recommendations)
        report = {
            "report_id": "EXTERNAL_DRIFT_REPORT",
            "created_at": utc_now_iso(),
            "status": "external_drift_monitor_ready",
            "phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "externalDriftSignals": signals,
            "externalDriftRecommendations": recommendations,
            "externalDriftSummary": summary,
            "safetyBoundary": "External Drift Monitor only creates review recommendations. It does not change external execution strategy, publish, reply, DM, follow, like, crawl platforms, or call write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            report = self._read_json(self.report_path, {})
            return {
                "report_id": "EXTERNAL_DRIFT_REPORT",
                "status": "external_drift_monitor_ready",
                "externalDriftSignals": self._read_json(self.signals_path, []),
                "externalDriftRecommendations": self._read_json(self.recommendations_path, []),
                "externalDriftSummary": self._read_json(self.summary_path, {}),
                **{key: value for key, value in report.items() if key not in {"externalDriftSignals", "externalDriftRecommendations", "externalDriftSummary"}},
            }
        return self.monitor()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.signals_path.write_text(json.dumps(report["externalDriftSignals"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.recommendations_path.write_text(json.dumps(report["externalDriftRecommendations"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["externalDriftSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _signals(
        self,
        expected_actions: list[dict[str, Any]],
        manual_feedback: list[dict[str, Any]],
        strategy_state: dict[str, Any],
        feedback_learning: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feedback_records = [item for item in manual_feedback if item.get("learning_memory_allowed") or item.get("intake_status") == "rejected"]
        if not feedback_records:
            feedback_records = manual_feedback[:1]
        signals = []
        for index, feedback in enumerate(feedback_records, start=1):
            expected = expected_actions[(index - 1) % max(len(expected_actions), 1)] if expected_actions else {}
            signals.extend(self._classify_drift(index, expected, feedback, strategy_state, feedback_learning))
        return signals

    def _classify_drift(
        self,
        index: int,
        expected: dict[str, Any],
        feedback: dict[str, Any],
        strategy_state: dict[str, Any],
        feedback_learning: dict[str, Any],
    ) -> list[dict[str, Any]]:
        engagement_score = self._engagement_score(feedback)
        expected_strength = self._expected_strength(expected, strategy_state)
        delta = round(engagement_score - expected_strength, 3)
        platform = feedback.get("platform") or expected.get("target_platform") or "unknown"
        signals = []

        if delta <= -0.25 or feedback.get("intake_status") == "rejected":
            signals.append(
                self._signal(
                    index,
                    "strategy_drift",
                    platform,
                    expected,
                    feedback,
                    expected_strength,
                    engagement_score,
                    delta,
                    "Recommendation effectiveness appears lower than expected.",
                )
            )
        if platform.lower() in self._weak_platforms(feedback_learning) or feedback.get("replies", 0) == 0:
            signals.append(
                self._signal(
                    index,
                    "platform_drift",
                    platform,
                    expected,
                    feedback,
                    expected_strength,
                    engagement_score,
                    delta,
                    "Platform response is weaker than expected or platform has failed-pattern pressure.",
                )
            )
        if feedback.get("views", 0) > 100 and (feedback.get("likes", 0) + feedback.get("replies", 0) + feedback.get("saves", 0)) <= 2:
            signals.append(
                self._signal(
                    index,
                    "audience_drift",
                    platform,
                    expected,
                    feedback,
                    expected_strength,
                    engagement_score,
                    delta,
                    "Audience saw the content but did not engage enough.",
                )
            )
        if feedback.get("rejection_reason") or any("pushy" in str(comment).lower() for comment in feedback.get("comments", [])):
            signals.append(
                self._signal(
                    index,
                    "tone_drift",
                    platform,
                    expected,
                    feedback,
                    expected_strength,
                    engagement_score,
                    delta,
                    "Manual feedback indicates tone or CTA may be too aggressive.",
                )
            )
        if not signals:
            signals.append(
                self._signal(
                    index,
                    "no_drift",
                    platform,
                    expected,
                    feedback,
                    expected_strength,
                    engagement_score,
                    delta,
                    "Manual feedback is broadly aligned with expected result.",
                )
            )
        return signals

    @staticmethod
    def _engagement_score(feedback: dict[str, Any]) -> float:
        views = max(feedback.get("views", 0), 1)
        positive = feedback.get("likes", 0) * 0.35 + feedback.get("replies", 0) * 0.35 + feedback.get("saves", 0) * 0.3
        if feedback.get("intake_status") == "rejected":
            return 0.0
        return round(min(1.0, positive / max(views * 0.08, 1)), 3)

    @staticmethod
    def _expected_strength(expected: dict[str, Any], strategy_state: dict[str, Any]) -> float:
        text = " ".join([str(expected.get("expected_result", "")), str(expected.get("would_do", ""))]).lower()
        base = 0.55
        if "human can review" in text or "expected" in text:
            base += 0.1
        if "reddit" in text:
            base += 0.08
        long_term_count = strategy_state.get("strategyEvolutionMemory", {}).get("long_term_count", 0)
        if long_term_count:
            base += 0.05
        return round(min(base, 0.85), 3)

    @staticmethod
    def _weak_platforms(feedback_learning: dict[str, Any]) -> set[str]:
        failed_patterns = feedback_learning.get("failedPromotionPatterns", [])
        return {str(item.get("value", "")).lower() for item in failed_patterns if item.get("dimension") == "platform"}

    @staticmethod
    def _signal(
        index: int,
        drift_type: str,
        platform: str,
        expected: dict[str, Any],
        feedback: dict[str, Any],
        expected_strength: float,
        actual_score: float,
        delta: float,
        reason: str,
    ) -> dict[str, Any]:
        severity = "high" if drift_type != "no_drift" and (delta <= -0.4 or feedback.get("intake_status") == "rejected") else "medium"
        if drift_type == "no_drift":
            severity = "low"
        return {
            "drift_id": f"EXT-DRIFT-{index:03d}-{drift_type.upper().replace('_', '-')}",
            "drift_type": drift_type,
            "platform": platform,
            "expected_result": expected.get("expected_result", expected.get("would_do", "")),
            "feedback_intake_id": feedback.get("feedback_intake_id", ""),
            "views": feedback.get("views", 0),
            "likes": feedback.get("likes", 0),
            "replies": feedback.get("replies", 0),
            "saves": feedback.get("saves", 0),
            "rejection_reason": feedback.get("rejection_reason", ""),
            "expected_strength_score": expected_strength,
            "actual_feedback_score": actual_score,
            "effectiveness_delta": delta,
            "severity": severity,
            "drift_reason": reason,
            "recommendation_only": True,
            "auto_strategy_change_allowed": False,
            "external_execution_change_allowed": False,
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _recommendation(signal: dict[str, Any], index: int) -> dict[str, Any]:
        if signal["drift_type"] == "no_drift":
            action = "Keep monitoring; do not change external strategy automatically."
        elif signal["drift_type"] == "tone_drift":
            action = "Review CTA tone and reduce homepage emphasis before the next manual export."
        elif signal["drift_type"] == "platform_drift":
            action = "Re-check platform fit and cadence before recommending more actions on this platform."
        elif signal["drift_type"] == "audience_drift":
            action = "Review target audience and hook relevance before repeating this format."
        else:
            action = "Review strategy assumptions because recommendation effectiveness is declining."
        return {
            "recommendation_id": f"EXT-DRIFT-REC-{index:03d}",
            "drift_id": signal["drift_id"],
            "drift_type": signal["drift_type"],
            "platform": signal["platform"],
            "recommendation": action,
            "human_review_required": signal["drift_type"] != "no_drift",
            "recommendation_only": True,
            "auto_strategy_change_allowed": False,
            "external_execution_change_allowed": False,
        }

    @staticmethod
    def _summary(signals: list[dict[str, Any]], recommendations: list[dict[str, Any]]) -> dict[str, Any]:
        drift_signals = [item for item in signals if item["drift_type"] != "no_drift"]
        counts = {drift_type: len([item for item in signals if item["drift_type"] == drift_type]) for drift_type in DRIFT_TYPES}
        return {
            "external_drift_monitor_ready": True,
            "signal_count": len(signals),
            "drift_signal_count": len(drift_signals),
            "recommendation_count": len(recommendations),
            "drift_type_counts": counts,
            "recommendation_effectiveness_declining": any(item["drift_type"] == "strategy_drift" for item in drift_signals),
            "highest_severity": "high" if any(item["severity"] == "high" for item in drift_signals) else ("medium" if drift_signals else "low"),
            "strategy_drift_detected": counts["strategy_drift"] > 0,
            "platform_drift_detected": counts["platform_drift"] > 0,
            "audience_drift_detected": counts["audience_drift"] > 0,
            "tone_drift_detected": counts["tone_drift"] > 0,
            "recommendation_only": True,
            "auto_strategy_change_allowed": False,
            "external_execution_change_allowed": False,
            "next_recommendation": "Route drift findings to human review before changing promotion strategy or manual export priorities.",
        }


if __name__ == "__main__":
    result = ExternalDriftMonitor().monitor()
    print(json.dumps({"status": result["status"], "summary": result["externalDriftSummary"]}, indent=2))
