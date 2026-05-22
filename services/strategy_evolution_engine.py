"""Long-term strategy evolution for AGOS Runtime personality training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class StrategyEvolutionEngine:
    """Classify tactics into long-term growth strategy versus short-term traffic."""

    DEFAULT_SIGNALS: list[dict[str, Any]] = [
        {
            "signal_id": "reddit_trust_answer",
            "platform": "reddit",
            "strategy": "Answer high-intent travel anxiety with detailed, non-promotional guidance.",
            "time_horizon": "long_term",
            "trust_score": 0.92,
            "learning_value": 0.86,
            "repeatability": 0.78,
            "traffic_spike": 0.24,
            "risk": 0.18,
        },
        {
            "signal_id": "tiktok_hook_spike",
            "platform": "tiktok",
            "strategy": "Test fast Tokyo transport hooks for save-worthy short videos.",
            "time_horizon": "short_term",
            "trust_score": 0.48,
            "learning_value": 0.52,
            "repeatability": 0.43,
            "traffic_spike": 0.88,
            "risk": 0.42,
        },
        {
            "signal_id": "youtube_evergreen_walkthrough",
            "platform": "youtube",
            "strategy": "Build evergreen walkthroughs for repeated travel pain points.",
            "time_horizon": "long_term",
            "trust_score": 0.9,
            "learning_value": 0.82,
            "repeatability": 0.81,
            "traffic_spike": 0.36,
            "risk": 0.2,
        },
        {
            "signal_id": "x_trend_reaction",
            "platform": "x",
            "strategy": "React to travel trend bursts with concise observations.",
            "time_horizon": "short_term",
            "trust_score": 0.58,
            "learning_value": 0.48,
            "repeatability": 0.45,
            "traffic_spike": 0.74,
            "risk": 0.35,
        },
    ]

    def __init__(self, root: str | Path = "runtime/strategy_evolution") -> None:
        self.root = Path(root)
        self.memory_path = self.root / "STRATEGY_EVOLUTION_MEMORY.json"
        self.report_path = self.root / "STRATEGY_EVOLUTION_REPORT.json"

    def evaluate(self, signals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        signals = signals or self.DEFAULT_SIGNALS
        decisions = [self.evaluate_signal(signal) for signal in signals]
        long_term = [item for item in decisions if item["classification"] == "long_term_growth"]
        short_term = [item for item in decisions if item["classification"] == "short_term_traffic"]
        report = {
            "report_id": "STRATEGY_EVOLUTION_REPORT",
            "created_at": utc_now_iso(),
            "status": "forming_long_term_strategy" if long_term else "needs_human_review",
            "longTermGrowthStrategies": long_term,
            "shortTermTrafficTactics": short_term,
            "strategyEvolutionMemory": {
                "primary_direction": self._primary_direction(long_term),
                "avoid_overweighting": [item["platform"] for item in short_term if item["risk"] >= 0.35],
                "long_term_count": len(long_term),
                "short_term_count": len(short_term),
                "next_review": "Promote strategies with durable trust, repeatable learning, and low drift risk.",
            },
            "evolutionFeed": [
                {
                    "platform": item["platform"],
                    "classification": item["classification"],
                    "score": item["evolution_score"],
                    "strategy": item["strategy"],
                    "reason": item["reason"],
                }
                for item in decisions
            ],
        }
        self.persist(report)
        return report

    def evaluate_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        durable_score = (
            signal.get("trust_score", 0) * 0.35
            + signal.get("learning_value", 0) * 0.3
            + signal.get("repeatability", 0) * 0.25
            - signal.get("risk", 0) * 0.1
        )
        spike_score = signal.get("traffic_spike", 0) * 0.7 + signal.get("risk", 0) * 0.3
        classification = "long_term_growth" if durable_score >= spike_score else "short_term_traffic"
        reason = (
            "Durable trust and learning value are stronger than traffic spike."
            if classification == "long_term_growth"
            else "Traffic spike is stronger than durable learning value; keep it as an experiment."
        )
        return {
            **signal,
            "classification": classification,
            "evolution_score": round(durable_score if classification == "long_term_growth" else spike_score, 3),
            "durable_score": round(durable_score, 3),
            "spike_score": round(spike_score, 3),
            "reason": reason,
            "human_review_status": "needs_human_review",
        }

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.memory_path.write_text(
            json.dumps(report["strategyEvolutionMemory"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _primary_direction(long_term: list[dict[str, Any]]) -> str:
        if not long_term:
            return "No durable strategy confirmed yet."
        best = sorted(long_term, key=lambda item: item["evolution_score"], reverse=True)[0]
        return f"{best['platform']}: {best['strategy']}"
