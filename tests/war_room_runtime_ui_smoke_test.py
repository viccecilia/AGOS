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
    war_room = state.get("warRoomGrowth") or {}

    assert state.get("realGrowthVerification"), "realGrowthVerification must be preserved"
    assert state.get("phaseBlueprint"), "phaseBlueprint must be preserved"
    assert len(state.get("rounds") or []) >= 60, "60 Round structure must be preserved"
    assert state.get("reports"), "reports must be preserved"
    assert state.get("modules"), "modules must be preserved"

    pipeline = war_room.get("runtimePipeline") or []
    assert len(pipeline) >= 10, "Runtime Pipeline must have at least 10 nodes"
    node_ids = {node.get("id") for node in pipeline}
    expected_nodes = {
        "Scout",
        "Collect",
        "Analyze",
        "Classify",
        "Prioritize",
        "Strategy",
        "Generate",
        "Human Review",
        "Learn",
        "Deposit",
    }
    assert expected_nodes.issubset(node_ids), "Runtime Pipeline is missing required nodes"
    assert war_room.get("current_runtime_stage"), "current_runtime_stage is required"

    required_markers = [
        'class="runtime-bar"',
        'id="runtime-pipeline"',
        'id="war-room-feed"',
        'id="war-room-jag-workspace"',
        'id="war-room-social-homepages"',
        'id="war-room-growth-cycles"',
        'id="war-room-growth-stages"',
        'id="war-room-correction-panel"',
        "AI Runtime OS",
    ]
    for marker in required_markers:
        assert marker in html, f"Runtime UI marker missing: {marker}"

    control = war_room.get("systemControl") or {}
    assert control.get("buttons") == ["启动", "停止"], "Runtime Bar must expose only start/stop"
    assert html.count('data-runtime-action="start"') == 1, "Start button must exist once"
    assert html.count('data-runtime-action="stop"') == 1, "Stop button must exist once"
    forbidden_buttons = ["运行分析", "保存学习", "生成策略", "导出证据包", "暂停侦察循环"]
    for label in forbidden_buttons:
        assert label not in control.get("buttons", []), f"Forbidden runtime button still present: {label}"

    assert "<details class=\"runtime-details\"" in html, "Growth Cycle must use collapsed details"
    assert "<details class=\"runtime-details\" open" not in html, "Growth Cycle must be collapsed by default"

    correction_statuses = {item.get("status") for item in war_room.get("correctionCenter") or []}
    assert "needs_human_review" in correction_statuses, "Correction Center needs human review status"
    assert "needs_code_check" in correction_statuses, "Correction Center needs code check status"
    assert "needs_runtime_validation" in correction_statuses, (
        "Correction Center needs runtime validation status"
    )

    feed = war_room.get("warRoomFeed") or []
    assert len(feed) >= 6, "War Room Feed must include runtime stream items"
    assert war_room.get("runtimeStatus") in {"RUNNING", "PAUSED", "STOPPED"}, (
        "Runtime status must use OS-level enum"
    )

    print("war_room_runtime_ui_smoke_test passed")


if __name__ == "__main__":
    main()
