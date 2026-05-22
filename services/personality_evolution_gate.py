"""Gate report for the Personality Evolution phase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.personality_isolation_engine import PersonalityIsolationEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.runtime_strategy_personality import RuntimeStrategyPersonalityEngine
from services.strategy_evolution_engine import StrategyEvolutionEngine
from services.runtime_persistence import utc_now_iso


class PersonalityEvolutionGate:
    """Validate whether AGOS has formed a stable operating personality."""

    def __init__(self, root: str | Path = "runtime/personality_evolution_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "PERSONALITY_EVOLUTION_REPORT.json"

    def evaluate(self) -> dict[str, Any]:
        personality = PersonalityMemoryDeposit().status()
        isolation = PersonalityIsolationEngine().state()
        strategy_personality = RuntimeStrategyPersonalityEngine().state()
        strategy_evolution = StrategyEvolutionEngine().state()
        checks = [
            self._check("Workspace Personality", bool(personality.get("currentPersonality", {}).get("workspacePersonality"))),
            self._check("Platform Personality", len(strategy_personality.get("strategyPersonalityMatrix", [])) >= 4),
            self._check("Market Personality", isolation.get("marketPersonalityPollution", {}).get("status") == "clear"),
            self._check("Strategy Personality", bool(strategy_evolution.get("longTermGrowthStrategies"))),
            self._check("Operating Team Behavior", strategy_evolution.get("status") == "forming_long_term_strategy"),
        ]
        passed = all(item["status"] == "passed" for item in checks)
        report = {
            "report_id": "PERSONALITY_EVOLUTION_REPORT",
            "created_at": utc_now_iso(),
            "status": "passed" if passed else "needs_human_review",
            "stableOperatingPersonality": passed,
            "checks": checks,
            "workspacePersonality": personality.get("currentPersonality", {}).get("workspacePersonality", {}),
            "platformPersonalityCount": len(strategy_personality.get("strategyPersonalityMatrix", [])),
            "marketIsolationStatus": isolation.get("marketPersonalityPollution", {}).get("status", "unknown"),
            "strategyPersonalityStatus": strategy_evolution.get("status", "unknown"),
            "personalityEvolutionSummary": (
                "AGOS has formed a stable operating personality with workspace, platform, market, and strategy layers."
                if passed
                else "AGOS personality is not ready for phase completion; human review is required."
            ),
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

    @staticmethod
    def _check(name: str, passed: bool) -> dict[str, Any]:
        return {
            "name": name,
            "status": "passed" if passed else "needs_human_review",
            "evidence": "validated" if passed else "missing or unstable",
        }
