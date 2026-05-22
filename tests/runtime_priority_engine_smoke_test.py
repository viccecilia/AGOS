from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_priority_engine import RuntimePriorityEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "runtime_priority"
        report = RuntimePriorityEngine(root).evolve()

        assert report["report_id"] == "RUNTIME_PRIORITY_REPORT"
        assert report["status"] == "priority_evolving"
        assert report["scope"] == "local_autonomous_growth_preparation_only"
        assert report["platformPriority"], "platform priority must exist"
        assert report["questionPriority"], "question priority must exist"
        assert report["trendPriority"], "trend priority must exist"
        assert report["contentPriority"], "content priority must exist"
        assert report["priorityEvolutionHistory"], "priority history must exist"
        assert report["runtimePriorityFeed"], "runtime priority feed must exist"
        assert report["prioritySummary"]["can_explain_priority_change"] is True

        for item in report["runtimePriorityFeed"]:
            assert item["why_changed"], "each priority feed item must explain why priority changed"
            assert item["ai_action"], "each priority feed item must include next AI action"

        assert (root / "RUNTIME_PRIORITY_REPORT.json").exists()
        assert (root / "runtime_priority_feed.json").exists()
        assert (root / "priority_evolution_history.json").exists()

    print("runtime priority engine smoke test passed")


if __name__ == "__main__":
    main()
