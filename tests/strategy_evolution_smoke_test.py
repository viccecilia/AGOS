from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.strategy_evolution_engine import StrategyEvolutionEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = StrategyEvolutionEngine(Path(tmp) / "strategy_evolution")
        report = engine.evaluate()

        assert report["report_id"] == "STRATEGY_EVOLUTION_REPORT"
        assert report["status"] == "forming_long_term_strategy"
        assert report["longTermGrowthStrategies"], "AGOS must identify long-term growth strategies"
        assert report["shortTermTrafficTactics"], "AGOS must separate short-term traffic tactics"
        assert report["strategyEvolutionMemory"]["primary_direction"]
        assert report["strategyEvolutionMemory"]["long_term_count"] >= 1
        assert report["strategyEvolutionMemory"]["short_term_count"] >= 1

        classifications = {item["classification"] for item in report["evolutionFeed"]}
        assert {"long_term_growth", "short_term_traffic"}.issubset(classifications)

        reddit = [item for item in report["evolutionFeed"] if item["platform"] == "reddit"][0]
        tiktok = [item for item in report["evolutionFeed"] if item["platform"] == "tiktok"][0]
        assert reddit["classification"] == "long_term_growth"
        assert tiktok["classification"] == "short_term_traffic"
        assert reddit["score"] != tiktok["score"]

        assert engine.report_path.exists()
        assert engine.memory_path.exists()
        memory = json.loads(engine.memory_path.read_text(encoding="utf-8"))
        assert "primary_direction" in memory
        assert "avoid_overweighting" in memory

    print("strategy evolution smoke test passed")


if __name__ == "__main__":
    main()
