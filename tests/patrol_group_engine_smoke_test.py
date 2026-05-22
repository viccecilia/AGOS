from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.patrol_group_engine import PatrolGroupEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = PatrolGroupEngine(Path(tmp) / "patrol_groups")
        state = engine.build_all()

        assert state["state_id"] == "PATROL_GROUPS_STATE"
        assert state["status"] == "active"
        assert set(state["supportedPlatforms"]) == {"Reddit", "TikTok", "X", "YouTube", "Threads"}
        assert state["patrolSummary"]["total_groups"] == 10

        groups = state["activePatrolGroups"]
        travel = [group for group in groups if group["industry_pack"] == "Travel Pack"]
        appliance = [group for group in groups if group["industry_pack"] == "Home Appliance Pack"]
        assert len(travel) == 5
        assert len(appliance) == 5
        assert {"JapanTravel", "Tokyo", "Osaka", "travelhacks"}.issubset(set(travel[0]["targets"]))
        assert {"SmartHome", "AirFryer", "Vacuum"}.issubset(set(appliance[0]["targets"]))

        for group in groups:
            assert group["status"] == "active"
            assert group["collection_mode"] == "manual_import_or_public_api_only"
            assert "no automated posting" in group["safety_boundary"]
            assert "no platform limit bypass" in group["safety_boundary"]

        assert "JAG-LAB" in state["workspacePatrolGroups"]
        assert "PHILIPS-LAB" in state["workspacePatrolGroups"]
        assert "Travel Pack" in state["industryPackPatrolGroups"]
        assert "Home Appliance Pack" in state["industryPackPatrolGroups"]
        assert engine.state_path.exists()
        assert engine.matrix_path.exists()

        saved = json.loads(engine.state_path.read_text(encoding="utf-8"))
        assert saved["patrolSummary"]["total_groups"] == 10

    print("patrol group engine smoke test passed")


if __name__ == "__main__":
    main()
