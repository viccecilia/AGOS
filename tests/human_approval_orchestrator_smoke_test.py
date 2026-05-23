from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.human_approval_orchestrator import HumanApprovalOrchestrator


def main() -> None:
    review_queue = [
        {
            "review_id": "REV-001",
            "workspace": "JAG-LAB",
            "target_type": "reply",
            "ai_reason": "Reply needs human review before learning.",
            "risk_level": "medium",
            "status": "needs_human_review",
            "source_platform": "Reddit",
            "country": "Japan",
            "created_at": "2026-05-23T00:00:00+00:00",
        }
    ]
    action_queue = [
        {
            "action_id": "ACT-001",
            "action_type": "today_reply",
            "recommendation": "Draft a Reddit reply.",
            "why_recommended": "Tokyo transport anxiety is high priority.",
            "risk_level": "medium",
            "status": "needs_human_approval",
            "recommended_platform": "Reddit",
            "recommended_market": "Japan",
            "created_at": "2026-05-23T00:01:00+00:00",
        }
    ]
    correction_queue = [
        {
            "correction_id": "COR-001",
            "target_type": "platform_style",
            "reason": "TikTok tone is too aggressive.",
            "risk_level": "high",
            "status": "needs_human_review",
            "workspace": "JAG-LAB",
            "platform": "TikTok",
            "market": "Japan",
            "created_at": "2026-05-23T00:02:00+00:00",
        }
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "human_approval"
        report = HumanApprovalOrchestrator(root).orchestrate(review_queue, action_queue, correction_queue)

        assert report["report_id"] == "HUMAN_APPROVAL_ORCHESTRATION_REPORT"
        assert report["scope"] == "local_unified_human_approval_only"
        assert report["approvalSummary"]["total_items"] == 3
        assert report["approvalSummary"]["review_queue_items"] == 1
        assert report["approvalSummary"]["action_queue_items"] == 1
        assert report["approvalSummary"]["correction_queue_items"] == 1
        assert report["approvalSummary"]["needs_human_approval"] == 3

        queue_types = {item["queue_type"] for item in report["unifiedApprovalQueue"]}
        assert queue_types == {"review", "action", "correction"}
        assert len(report["unifiedApprovalTimeline"]) == 3

        for item in report["unifiedApprovalQueue"]:
            assert item["unified_id"].startswith("APPROVAL-")
            assert item["target_id"]
            assert item["description"]
            assert item["required_decisions"]
            assert item["source"]

        assert (root / "HUMAN_APPROVAL_ORCHESTRATION_REPORT.json").exists()
        assert (root / "unified_approval_queue.json").exists()
        assert (root / "UNIFIED_APPROVAL_TIMELINE.json").exists()

    print("human approval orchestrator smoke test passed")


if __name__ == "__main__":
    main()
