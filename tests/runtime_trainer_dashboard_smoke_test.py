from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_trainer_dashboard import RuntimeTrainerDashboard


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dashboard = RuntimeTrainerDashboard(Path(tmp) / "trainer_dashboard").build()

        assert dashboard["dashboard_id"] == "RUNTIME_TRAINER_DASHBOARD"
        assert dashboard["bestPersonality"] is not None
        assert dashboard["worstPersonality"] is not None
        assert "driftAlerts" in dashboard
        assert dashboard["correctionFrequency"]["correction_count"] >= 0
        assert dashboard["strategyChanges"], "Strategy changes must be visible to trainer"
        assert dashboard["recentLearning"], "Trainer dashboard must show what AGOS recently learned"

        learning_types = {item["type"] for item in dashboard["recentLearning"]}
        assert {"best_personality", "failed_tone", "strategy_direction", "human_correction"}.issubset(learning_types)
        assert dashboard["trainerActions"], "Trainer actions are required"

        path = Path(tmp) / "trainer_dashboard" / "RUNTIME_TRAINER_DASHBOARD.json"
        assert path.exists()
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert saved["dashboard_id"] == dashboard["dashboard_id"]

    print("runtime trainer dashboard smoke test passed")


if __name__ == "__main__":
    main()
