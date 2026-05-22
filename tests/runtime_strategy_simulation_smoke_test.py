from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_strategy_simulation import RuntimeStrategySimulation


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "strategy_simulation"
        report = RuntimeStrategySimulation(root).simulate()

        assert report["report_id"] == "STRATEGY_SIMULATION_REPORT"
        assert report["status"] == "simulating_strategy_outcomes"
        assert report["scope"] == "local_strategy_simulation_only"
        assert len(report["strategySimulationScenarios"]) >= 4
        scenarios = {item["scenario"]: item for item in report["strategySimulationScenarios"]}
        assert "increase_reddit_content" in scenarios
        assert "reduce_tiktok_weight" in scenarios
        assert "strengthen_korea_market" in scenarios
        assert "stop_failed_generic_strategy" in scenarios
        assert report["strategySimulationFeed"], "strategy simulation feed must exist"
        assert report["simulationSummary"]["can_predict_strategy_consequence"] is True
        assert report["simulationSummary"]["requires_human_review"] is True

        for item in report["strategySimulationScenarios"]:
            assert item["predicted_outcome"], "each scenario must predict outcome"
            assert item["recommendation"], "each scenario must recommend next action"
            assert item["review_status"] == "needs_human_review"
            assert item["simulation_only"] is True

        assert (root / "STRATEGY_SIMULATION_REPORT.json").exists()
        assert (root / "strategy_simulation_scenarios.json").exists()
        assert (root / "strategy_simulation_feed.json").exists()

    print("runtime strategy simulation smoke test passed")


if __name__ == "__main__":
    main()
