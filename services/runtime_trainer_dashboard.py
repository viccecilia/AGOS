"""Runtime Trainer Console aggregation for AGOS personality training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.human_feedback_learning import HumanFeedbackLearning
from services.personality_drift_engine import PersonalityDriftEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.personality_review_session import PersonalityReviewSession
from services.strategy_evolution_engine import StrategyEvolutionEngine
from services.runtime_persistence import utc_now_iso


class RuntimeTrainerDashboard:
    """Build a trainer-facing view of what AGOS has learned recently."""

    def __init__(self, root: str | Path = "runtime/trainer_dashboard") -> None:
        self.root = Path(root)
        self.report_path = self.root / "RUNTIME_TRAINER_DASHBOARD.json"

    def build(self) -> dict[str, Any]:
        personality = PersonalityMemoryDeposit().status()
        drift = PersonalityDriftEngine().summary()
        feedback = HumanFeedbackLearning().summary()
        review = PersonalityReviewSession().state()
        strategy = StrategyEvolutionEngine().state()
        best_personality = personality.get("bestPersonality", {})
        worst_personality = personality.get("failedPersonality", {})
        drift_alerts = drift.get("personalityDriftAlerts", [])
        correction_history = feedback.get("correctionHistory", [])
        dashboard = {
            "dashboard_id": "RUNTIME_TRAINER_DASHBOARD",
            "created_at": utc_now_iso(),
            "status": "needs_training_attention" if drift_alerts or worst_personality else "training_stable",
            "bestPersonality": best_personality,
            "worstPersonality": worst_personality,
            "driftAlerts": drift_alerts[-10:],
            "correctionFrequency": {
                "human_decisions_today": feedback.get("humanDecisionsToday", 0),
                "correction_count": len(correction_history),
                "top_corrected_mistakes": feedback.get("topCorrectedMistakes", []),
            },
            "strategyChanges": strategy.get("evolutionFeed", []),
            "recentLearning": self._recent_learning(personality, review, strategy, feedback),
            "trainerActions": [
                "Approve stable personality signals.",
                "Reject drift-heavy tones before they enter long-term memory.",
                "Promote long-term growth strategies over short-term traffic spikes.",
                "Review correction frequency before changing active personality.",
            ],
        }
        self.persist(dashboard)
        return dashboard

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, dashboard: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _recent_learning(
        personality: dict[str, Any],
        review: dict[str, Any],
        strategy: dict[str, Any],
        feedback: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "best_personality",
                "summary": personality.get("bestPersonality", {}).get("tone", "trusted_guide"),
                "evidence": personality.get("bestPersonality", {}).get("reason", ""),
            },
            {
                "type": "failed_tone",
                "summary": review.get("recentFailedTone", "none"),
                "evidence": review.get("reviewSummary", ""),
            },
            {
                "type": "strategy_direction",
                "summary": strategy.get("strategyEvolutionMemory", {}).get("primary_direction", ""),
                "evidence": strategy.get("strategyEvolutionMemory", {}).get("next_review", ""),
            },
            {
                "type": "human_correction",
                "summary": f"{feedback.get('humanDecisionsToday', 0)} human decisions today",
                "evidence": "Human feedback is part of Runtime training memory.",
            },
        ]
