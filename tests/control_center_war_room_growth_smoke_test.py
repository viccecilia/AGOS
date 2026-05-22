import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs" / "project_control_center.html"


def load_state():
    html = HTML_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="project-state" type="application/json">\s*([\s\S]*?)\s*</script>',
        html,
    )
    assert match, "project-state JSON script not found"
    return html, json.loads(match.group(1))


def main():
    html, state = load_state()
    war_room = state.get("warRoomGrowth")
    assert isinstance(war_room, dict), "warRoomGrowth field is missing"

    cycles = war_room.get("growthCycles") or []
    assert len(cycles) >= 3, "at least 3 sample growth cycles are required"

    stages = war_room.get("growthStages") or []
    assert len(stages) >= 1, "at least 1 10-cycle stage summary is required"
    assert any(stage.get("cycleRange") == "Cycle 001-010" for stage in stages), (
        "Cycle 001-010 stage summary is required"
    )

    workspace = war_room.get("jagWorkspace") or {}
    assert workspace.get("product") == "Japan AI Guide App", "JAG App workspace panel data missing"
    assert workspace.get("workspace_id") == "jag_app_growth", "JAG workspace_id is incorrect"
    assert "Travel Pack" in workspace.get("industryPack", ""), "JAG industry pack is incorrect"

    allowed_placeholders = {"pending_setup", "needs_account_url"}
    social_homepages = war_room.get("socialHomepages") or []
    assert len(social_homepages) >= 7, "JAG social homepage matrix must cover 7 platforms"
    for item in social_homepages:
        url = item.get("homepageUrl")
        assert url in allowed_placeholders, f"fabricated or unexpected URL found: {url}"
        assert not str(url).startswith(("http://", "https://")), (
            f"social homepage must not contain a real URL in this round: {url}"
        )

    control = war_room.get("systemControl") or {}
    expected_statuses = {
        "idle",
        "scouting",
        "analyzing",
        "classifying",
        "learning",
        "planning",
        "paused",
        "stopped",
        "needs_human_review",
        "needs_code_check",
    }
    assert set(control.get("statusEnum") or []) == expected_statuses, "status enum mismatch"
    assert control.get("currentWorkspace") == "jag_app_growth", "control panel workspace mismatch"

    required_ids = [
        'id="war-room-growth"',
        'id="war-room-control-panel"',
        'id="war-room-jag-workspace"',
        'id="war-room-social-homepages"',
        'id="war-room-growth-cycles"',
        'id="war-room-growth-stages"',
        'id="war-room-intelligence-trace"',
        'id="war-room-learning-deposit"',
        'id="war-room-correction-panel"',
    ]
    for marker in required_ids:
        assert marker in html, f"HTML marker missing: {marker}"

    assert "AGOS 成长可视化战情室" in html, "Chinese War Room title is required"
    assert "JAG 社交主页矩阵" in html, "Chinese JAG social homepage section is required"
    assert "纠偏检测面板" in html, "Chinese correction panel title is required"

    assert state.get("realGrowthVerification"), "realGrowthVerification must be preserved"
    assert state.get("phaseBlueprint"), "phaseBlueprint must be preserved"
    assert state.get("rounds") and len(state["rounds"]) >= 60, "original Round structure missing"
    assert war_room.get("sampleDataOnly") is True, "War Room data must be marked as sample"
    assert war_room.get("automationEnabled") is False, "War Room must not enable automation"
    assert war_room.get("noAutoPosting") is True, "War Room must block auto posting"
    assert war_room.get("noAutoRegistration") is True, "War Room must block auto registration"

    print("control_center_war_room_growth_smoke_test passed")


if __name__ == "__main__":
    main()
