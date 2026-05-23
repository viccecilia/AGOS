"""Gate review for Runtime Batch Intelligence acceleration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.batch_human_review import BatchHumanReview
from services.batch_scout_runtime import BatchScoutRuntime
from services.batch_topic_clustering import BatchTopicClustering
from services.runtime_pattern_learning import RuntimePatternLearning
from services.runtime_persistence import utc_now_iso
from services.runtime_replay_training import RuntimeReplayTraining
from services.synthetic_feedback_training import SyntheticFeedbackTraining


class IntelligenceAccelerationGate:
    """Validate Batch Intelligence Acceleration readiness."""

    def __init__(self, root: str | Path = "runtime/intelligence_acceleration_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "INTELLIGENCE_ACCELERATION_REPORT.json"
        self.review_path = self.root / "RUNTIME_INTELLIGENCE_EVOLUTION_REVIEW.json"
        self.checks_path = self.root / "intelligence_acceleration_checks.json"
        self.feed_path = self.root / "intelligence_acceleration_feed.json"

    def evaluate(self, sources: dict[str, Any] | None = None) -> dict[str, Any]:
        data = sources if sources is not None else self._default_sources()
        checks = self._checks(data)
        gate_passed = all(item["status"] == "passed" for item in checks)
        review = self._evolution_review(data, checks, gate_passed)
        report = {
            "report_id": "INTELLIGENCE_ACCELERATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "passed" if gate_passed else "needs_review",
            "scope": "runtime_batch_intelligence_gate",
            "batchIntelligenceAccelerationReady": gate_passed,
            "gateChecks": checks,
            "runtimeIntelligenceEvolutionReview": review,
            "intelligenceAccelerationFeed": self._feed(checks, review),
            "nextStage": "Controlled Real External Interaction Stage" if gate_passed else "Batch Intelligence correction",
            "safetyBoundary": "Intelligence Acceleration Gate validates local runtime intelligence only. It does not post, reply, follow, DM, log in, register accounts, or call external write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_path.write_text(json.dumps(report["runtimeIntelligenceEvolutionReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(report["gateChecks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["intelligenceAccelerationFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _default_sources() -> dict[str, Any]:
        batch_scout = BatchScoutRuntime().state()
        batch_clusters = BatchTopicClustering().state()
        batch_review = BatchHumanReview().state()
        pattern_learning = RuntimePatternLearning().state()
        replay_training = RuntimeReplayTraining().state()
        synthetic_training = SyntheticFeedbackTraining().state()
        return {
            "batch_scout": batch_scout,
            "batch_clusters": batch_clusters,
            "batch_review": batch_review,
            "pattern_learning": pattern_learning,
            "replay_training": replay_training,
            "synthetic_training": synthetic_training,
        }

    @staticmethod
    def _checks(data: dict[str, Any]) -> list[dict[str, Any]]:
        scout_summary = data["batch_scout"].get("batchScoutSummary", {})
        cluster_summary = data["batch_clusters"].get("batchClusterSummary", {})
        review_summary = data["batch_review"].get("batchHumanReviewSummary", {})
        pattern_summary = data["pattern_learning"].get("patternLearningSummary", {})
        replay_summary = data["replay_training"].get("replayTrainingSummary", {})
        synthetic_summary = data["synthetic_training"].get("syntheticTrainingSummary", {})
        checks = [
            IntelligenceAccelerationGate._check(
                "Batch Scout Runtime",
                scout_summary.get("batch_runtime_ready") is True and scout_summary.get("questions_processed", 0) >= 50,
                f"Processed {scout_summary.get('questions_processed', 0)} questions through Scout, Analyze, Classify, and Priority Ranking.",
            ),
            IntelligenceAccelerationGate._check(
                "Batch Topic Clustering",
                cluster_summary.get("batch_clustering_ready") is True and cluster_summary.get("clusters_created", 0) >= 1,
                f"Created {cluster_summary.get('clusters_created', 0)} clusters with {cluster_summary.get('high_growth_signal_clusters', 0)} high-growth groups.",
            ),
            IntelligenceAccelerationGate._check(
                "Batch Human Review",
                review_summary.get("batch_training_ready") is True and review_summary.get("review_items", 0) >= 1,
                f"Reviewed {review_summary.get('review_items', 0)} clusters with approve/reject/modify/classify labels.",
            ),
            IntelligenceAccelerationGate._check(
                "Pattern Learning",
                pattern_summary.get("pattern_memory_ready") is True
                and pattern_summary.get("high_value_patterns", 0) >= 1
                and pattern_summary.get("high_risk_patterns", 0) >= 1,
                f"Learned {pattern_summary.get('patterns_learned', 0)} patterns across value, engagement, conversion, and risk.",
            ),
            IntelligenceAccelerationGate._check(
                "Replay Training",
                replay_summary.get("replay_training_ready") is True
                and replay_summary.get("historical_questions", 0) >= 1
                and replay_summary.get("historical_failures", 0) >= 1,
                f"Replayed {replay_summary.get('replay_items', 0)} historical intelligence items.",
            ),
            IntelligenceAccelerationGate._check(
                "Synthetic Feedback Training",
                synthetic_summary.get("synthetic_training_ready") is True
                and synthetic_summary.get("simulated_user_questions", 0) >= 1
                and synthetic_summary.get("simulated_user_risks", 0) >= 1,
                f"Generated {synthetic_summary.get('synthetic_items', 0)} synthetic samples with {synthetic_summary.get('high_risk_samples', 0)} high-risk samples.",
            ),
        ]
        return checks

    @staticmethod
    def _check(name: str, passed: bool, evidence: str) -> dict[str, Any]:
        return {
            "check": name,
            "status": "passed" if passed else "needs_review",
            "evidence": evidence,
            "checked_at": utc_now_iso(),
        }

    @staticmethod
    def _evolution_review(data: dict[str, Any], checks: list[dict[str, Any]], gate_passed: bool) -> dict[str, Any]:
        scout_summary = data["batch_scout"].get("batchScoutSummary", {})
        cluster_summary = data["batch_clusters"].get("batchClusterSummary", {})
        review_summary = data["batch_review"].get("batchHumanReviewSummary", {})
        pattern_summary = data["pattern_learning"].get("patternLearningSummary", {})
        replay_summary = data["replay_training"].get("replayTrainingSummary", {})
        synthetic_summary = data["synthetic_training"].get("syntheticTrainingSummary", {})
        passed_checks = len([item for item in checks if item["status"] == "passed"])
        total_checks = len(checks)
        acceleration_score = round(passed_checks / max(total_checks, 1), 2)
        return {
            "review_id": "RUNTIME_INTELLIGENCE_EVOLUTION_REVIEW",
            "created_at": utc_now_iso(),
            "gate_status": "passed" if gate_passed else "needs_review",
            "acceleration_score": acceleration_score,
            "questions_processed": scout_summary.get("questions_processed", 0),
            "clusters_created": cluster_summary.get("clusters_created", 0),
            "human_review_items": review_summary.get("review_items", 0),
            "patterns_learned": pattern_summary.get("patterns_learned", 0),
            "replay_items": replay_summary.get("replay_items", 0),
            "synthetic_items": synthetic_summary.get("synthetic_items", 0),
            "evolution_summary": IntelligenceAccelerationGate._evolution_summary(gate_passed),
            "readiness_to_next_stage": gate_passed,
            "next_stage": "Controlled Real External Interaction Stage" if gate_passed else "Batch Intelligence correction",
            "safety_boundary_confirmed": True,
        }

    @staticmethod
    def _evolution_summary(gate_passed: bool) -> str:
        if gate_passed:
            return "AGOS has completed Runtime Batch Intelligence Phase and can accelerate intelligence through batch discovery, review, pattern learning, replay, and synthetic training."
        return "AGOS has not fully passed Runtime Batch Intelligence Gate; correction is required before external interaction preparation."

    @staticmethod
    def _feed(checks: list[dict[str, Any]], review: dict[str, Any]) -> list[dict[str, Any]]:
        feed = [
            {
                "time": item["checked_at"],
                "event": "gate_check",
                "check": item["check"],
                "status": item["status"],
                "evidence": item["evidence"],
            }
            for item in checks
        ]
        feed.insert(
            0,
            {
                "time": review["created_at"],
                "event": "intelligence_acceleration_gate",
                "status": review["gate_status"],
                "acceleration_score": review["acceleration_score"],
                "evolution_summary": review["evolution_summary"],
                "next_stage": review["next_stage"],
            },
        )
        return feed


if __name__ == "__main__":
    result = IntelligenceAccelerationGate().evaluate()
    print(json.dumps({"status": result["status"], "ready": result["batchIntelligenceAccelerationReady"]}, indent=2))
