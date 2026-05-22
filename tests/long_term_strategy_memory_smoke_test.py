from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.long_term_strategy_memory import LongTermStrategyMemory


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "long_term_strategy_memory"
        report = LongTermStrategyMemory(root).build()

        assert report["report_id"] == "LONG_TERM_STRATEGY_MEMORY_REPORT"
        assert report["status"] == "forming_long_term_memory"
        assert report["scope"] == "local_autonomous_growth_preparation_only"
        assert report["longTermEffectiveStrategies"], "long-term strategies must be stored"
        assert report["shortTermEffectiveStrategies"], "short-term strategies must be stored"
        assert report["longTermFailedStrategies"], "failed strategy memory must be stored"
        assert report["platformLongTermTrends"], "platform trends must be stored"
        assert report["marketLongTermTrends"], "market trends must be stored"
        assert report["strategyMemoryTimeline"], "strategy memory timeline must be stored"

        classification = report["strategyHorizonClassification"]
        assert classification["can_distinguish_short_vs_long"] is True
        assert classification["primary_long_term_direction"] != "No durable long-term strategy confirmed yet."

        assert (root / "LONG_TERM_STRATEGY_MEMORY_REPORT.json").exists()
        assert (root / "long_term_strategy_memory.json").exists()
        assert (root / "strategy_memory_timeline.json").exists()

    print("long term strategy memory smoke test passed")


if __name__ == "__main__":
    main()
