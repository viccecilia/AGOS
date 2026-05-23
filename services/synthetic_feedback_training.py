"""Synthetic feedback training dataset for local AGOS acceleration."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.runtime_replay_training import RuntimeReplayTraining


SYNTHETIC_TYPES = ["user_question", "user_feedback", "user_interaction", "user_risk"]
PLATFORM_SEQUENCE = ["Reddit", "TikTok", "X", "YouTube"]


class SyntheticFeedbackTraining:
    """Generate synthetic questions, feedback, interactions, and risk samples."""

    def __init__(self, root: str | Path = "runtime/synthetic_training") -> None:
        self.root = Path(root)
        self.report_path = self.root / "SYNTHETIC_FEEDBACK_TRAINING_REPORT.json"
        self.dataset_path = self.root / "synthetic_training_dataset.json"
        self.feed_path = self.root / "synthetic_training_feed.json"
        self.summary_path = self.root / "synthetic_training_summary.json"

    def generate(self, replay_memory: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_memory = replay_memory
        if source_memory is None:
            source_memory = RuntimeReplayTraining().state().get("replayMemory", [])
        dataset = self._dataset(source_memory)
        report = {
            "report_id": "SYNTHETIC_FEEDBACK_TRAINING_REPORT",
            "created_at": utc_now_iso(),
            "status": "synthetic_training_ready",
            "scope": "local_synthetic_feedback_training",
            "syntheticTypes": SYNTHETIC_TYPES,
            "syntheticTrainingDataset": dataset,
            "syntheticTrainingFeed": self._feed(dataset),
            "syntheticTrainingSummary": self._summary(dataset),
            "safetyBoundary": "Synthetic Feedback Training creates local simulated data only. It does not post, reply, follow, DM, log in, register accounts, or call external APIs.",
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
        self.dataset_path.write_text(json.dumps(report["syntheticTrainingDataset"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["syntheticTrainingFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["syntheticTrainingSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _dataset(replay_memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seeds = SyntheticFeedbackTraining._balanced_seeds(replay_memory) if replay_memory else SyntheticFeedbackTraining._fallback_seeds()
        dataset: list[dict[str, Any]] = []
        for index, seed in enumerate(seeds, start=1):
            platform = PLATFORM_SEQUENCE[(index - 1) % len(PLATFORM_SEQUENCE)]
            topic = seed.get("topic", f"synthetic_topic_{index}")
            dataset.extend(
                [
                    SyntheticFeedbackTraining._record(index, "user_question", platform, topic, seed),
                    SyntheticFeedbackTraining._record(index, "user_feedback", platform, topic, seed),
                    SyntheticFeedbackTraining._record(index, "user_interaction", platform, topic, seed),
                    SyntheticFeedbackTraining._record(index, "user_risk", platform, topic, seed),
                ]
            )
        return dataset

    @staticmethod
    def _balanced_seeds(replay_memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seeds: list[dict[str, Any]] = []
        for source_type in ["historical_question", "historical_reply", "historical_feedback", "historical_failure"]:
            seeds.extend([item for item in replay_memory if item.get("source_type") == source_type][:2])
        if len(seeds) < 8:
            seen = {item.get("replay_id") for item in seeds}
            for item in replay_memory:
                if item.get("replay_id") not in seen:
                    seeds.append(item)
                if len(seeds) >= 8:
                    break
        return seeds[:8]

    @staticmethod
    def _record(seed_index: int, synthetic_type: str, platform: str, topic: str, seed: dict[str, Any]) -> dict[str, Any]:
        scenario = SyntheticFeedbackTraining._scenario(synthetic_type, platform, topic, seed)
        return {
            "synthetic_id": f"SYNTH-{synthetic_type.upper().replace('_', '-')}-{seed_index:04d}",
            "synthetic_type": synthetic_type,
            "platform": platform,
            "workspace": "JAG-LAB",
            "topic": topic,
            "source_replay_id": seed.get("replay_id", ""),
            "source_signal": seed.get("replay_result", seed.get("previous_signal", "synthetic_seed")),
            "simulated_user_input": scenario["input"],
            "simulated_feedback": scenario["feedback"],
            "simulated_interaction": scenario["interaction"],
            "simulated_risk": scenario["risk"],
            "training_label": scenario["label"],
            "training_objective": scenario["objective"],
            "training_weight": scenario["weight"],
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _scenario(synthetic_type: str, platform: str, topic: str, seed: dict[str, Any]) -> dict[str, Any]:
        replay_result = seed.get("replay_result", "")
        risk_source = replay_result == "risk_pattern_reinforced" or seed.get("source_type") == "historical_failure"
        if synthetic_type == "user_question":
            return {
                "input": f"I am confused about {topic}. What should I do first?",
                "feedback": "needs clear step-by-step guidance",
                "interaction": "question_follow_up_expected",
                "risk": "low",
                "label": "synthetic_question",
                "objective": "train question understanding and pain-point routing",
                "weight": 0.72,
            }
        if synthetic_type == "user_feedback":
            return {
                "input": f"Your answer about {topic} was useful, but I still need a concrete example.",
                "feedback": "partially_helpful_needs_specificity",
                "interaction": "reply_likely",
                "risk": "watch",
                "label": "synthetic_feedback",
                "objective": "train feedback interpretation and answer refinement",
                "weight": 0.78,
            }
        if synthetic_type == "user_interaction":
            return {
                "input": f"Saved this {platform} advice about {topic} for my trip.",
                "feedback": "save_signal",
                "interaction": "saved_shared_or_replied",
                "risk": "low",
                "label": "synthetic_interaction",
                "objective": "train engagement and conversion proxy recognition",
                "weight": 0.84,
            }
        return {
            "input": f"This {platform} reply about {topic} feels too promotional.",
            "feedback": "negative_risk_signal" if risk_source else "possible_tone_drift",
            "interaction": "ignored_or_rejected",
            "risk": "high" if risk_source else "medium",
            "label": "synthetic_risk",
            "objective": "train risk detection before real-world execution",
            "weight": 0.9 if risk_source else 0.8,
        }

    @staticmethod
    def _fallback_seeds() -> list[dict[str, Any]]:
        return [
            {"replay_id": "SYNTH-SEED-001", "topic": "Tokyo transport anxiety", "replay_result": "question_priority_retrained"},
            {"replay_id": "SYNTH-SEED-002", "topic": "JR Pass decision pressure", "replay_result": "engagement_pattern_reinforced"},
        ]

    @staticmethod
    def _summary(dataset: list[dict[str, Any]]) -> dict[str, Any]:
        types = Counter(item["synthetic_type"] for item in dataset)
        risks = Counter(item["simulated_risk"] for item in dataset)
        platforms = Counter(item["platform"] for item in dataset)
        return {
            "synthetic_items": len(dataset),
            "simulated_user_questions": types.get("user_question", 0),
            "simulated_user_feedback": types.get("user_feedback", 0),
            "simulated_user_interactions": types.get("user_interaction", 0),
            "simulated_user_risks": types.get("user_risk", 0),
            "high_risk_samples": risks.get("high", 0),
            "platform_coverage": dict(platforms),
            "synthetic_training_ready": bool(dataset),
        }

    @staticmethod
    def _feed(dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["created_at"],
                "synthetic_id": item["synthetic_id"],
                "synthetic_type": item["synthetic_type"],
                "platform": item["platform"],
                "topic": item["topic"],
                "simulated_feedback": item["simulated_feedback"],
                "simulated_interaction": item["simulated_interaction"],
                "simulated_risk": item["simulated_risk"],
                "training_objective": item["training_objective"],
                "training_weight": item["training_weight"],
            }
            for item in dataset[:16]
        ]


if __name__ == "__main__":
    result = SyntheticFeedbackTraining().generate()
    print(json.dumps({"status": result["status"], "items": result["syntheticTrainingSummary"]["synthetic_items"]}, indent=2))
