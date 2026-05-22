from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.personality_evolution_gate import PersonalityEvolutionGate


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        gate = PersonalityEvolutionGate(Path(tmp) / "personality_evolution_gate")
        report = gate.evaluate()

        assert report["report_id"] == "PERSONALITY_EVOLUTION_REPORT"
        assert report["status"] == "passed"
        assert report["stableOperatingPersonality"] is True
        assert report["platformPersonalityCount"] >= 4
        assert report["marketIsolationStatus"] == "clear"
        assert report["strategyPersonalityStatus"] == "forming_long_term_strategy"

        check_names = {item["name"] for item in report["checks"]}
        assert {
            "Workspace Personality",
            "Platform Personality",
            "Market Personality",
            "Strategy Personality",
            "Operating Team Behavior",
        }.issubset(check_names)
        assert all(item["status"] == "passed" for item in report["checks"])
        assert "stable operating personality" in report["personalityEvolutionSummary"]

        assert gate.report_path.exists()
        saved = json.loads(gate.report_path.read_text(encoding="utf-8"))
        assert saved["report_id"] == report["report_id"]

    print("personality evolution gate smoke test passed")


if __name__ == "__main__":
    main()
