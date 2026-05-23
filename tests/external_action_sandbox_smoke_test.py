from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.external_action_sandbox import ExternalActionSandbox, FORBIDDEN_WRITE_ACTIONS


def main() -> None:
    recommendations = [
        {
            "action_id": "REC-REPLY-TEST",
            "action_type": "today_reply",
            "recommendation": "Draft a helpful Reddit reply about Tokyo station confusion.",
            "why_recommended": "Reddit has high reply potential for transport anxiety.",
            "risk_level": "medium",
            "recommended_platform": "Reddit",
            "recommended_market": "Japan",
        },
        {
            "action_id": "REC-CONTENT-TEST",
            "action_type": "today_content",
            "recommendation": "Prepare a short TikTok hook about airport transfer mistakes.",
            "why_recommended": "TikTok trend strength is high for first-trip mistakes.",
            "risk_level": "high",
            "recommended_platform": "TikTok",
            "recommended_market": "Japan",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "external_action_sandbox"
        report = ExternalActionSandbox(root).build(recommendations)

        assert report["report_id"] == "EXTERNAL_ACTION_SANDBOX_REPORT"
        assert report["status"] == "sandbox_ready"
        assert report["scope"] == "controlled_external_action_preparation_only"
        assert report["externalActionSandboxSummary"]["total_actions"] == 2
        assert report["externalActionSandboxSummary"]["blocked_actions"] == 2
        assert report["externalActionSandboxSummary"]["write_api_calls_enabled"] is False
        assert report["externalActionSandboxSummary"]["external_execution_allowed"] is False
        assert report["externalActionSandboxSummary"]["human_gate_required"] is True
        assert set(FORBIDDEN_WRITE_ACTIONS).issubset(set(report["forbiddenWriteActions"]))

        action_types = {item["external_action_type"] for item in report["externalActionQueue"]}
        assert {"external_reply", "external_content_publish"}.issubset(action_types)

        for item in report["externalActionQueue"]:
            assert item["status"] == "waiting_human_approval"
            assert item["human_gate_status"] == "required"
            assert item["external_execution_allowed"] is False
            assert item["write_api_call_attempted"] is False
            assert item["write_api_call_allowed"] is False
            assert item["simulation_status"] == "simulated_only"
            assert item["blocked_reason"]
            assert item["why_suggested"]

        for item in report["externalActionSimulations"]:
            assert item["status"] == "simulated_only"
            assert item["write_api_call_attempted"] is False
            assert item["external_execution_allowed"] is False

        assert not hasattr(ExternalActionSandbox(root), "post")
        assert not hasattr(ExternalActionSandbox(root), "reply")
        assert not hasattr(ExternalActionSandbox(root), "follow")
        assert not hasattr(ExternalActionSandbox(root), "dm")
        assert not hasattr(ExternalActionSandbox(root), "login")
        assert not hasattr(ExternalActionSandbox(root), "register")

        assert (root / "EXTERNAL_ACTION_SANDBOX_REPORT.json").exists()
        assert (root / "external_action_queue.json").exists()
        assert (root / "external_action_feed.json").exists()
        assert (root / "external_action_simulations.json").exists()

    print("external action sandbox smoke test passed")


if __name__ == "__main__":
    main()
