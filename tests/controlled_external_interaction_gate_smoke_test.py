from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.controlled_external_interaction_gate import ControlledExternalInteractionGate


def main() -> None:
    export_pack = {
        "manualExportItems": [
            {
                "export_id": "MANUAL-EXPORT-GATE-001",
                "platform": "Reddit",
                "content_format": "reply",
                "risk_level": "medium",
            },
            {
                "export_id": "MANUAL-EXPORT-GATE-002",
                "platform": "TikTok",
                "content_format": "short_video",
                "risk_level": "high",
            },
        ],
        "manualExportSummary": {
            "manual_export_pack_ready": True,
            "export_item_count": 2,
            "human_gate_required": True,
            "external_execution_allowed": False,
        },
    }
    evidence_ledger = {
        "externalEvidenceLedger": [
            {
                "export_id": "MANUAL-EXPORT-GATE-001",
                "execution_status": "manually_executed",
                "feedback_learning_allowed": True,
            },
            {
                "export_id": "MANUAL-EXPORT-GATE-002",
                "execution_status": "evidence_pending",
                "feedback_learning_allowed": False,
            },
        ],
        "externalEvidenceLedgerReport": {
            "ledger_ready": True,
            "all_export_items_bound": True,
            "evidence_record_count": 2,
            "feedback_learning_allowed_count": 1,
            "platform_api_called": False,
        },
    }
    manual_feedback = {
        "manualExternalFeedbackSummary": {
            "manual_feedback_intake_ready": True,
            "feedback_source": "manual_import",
            "feedback_record_count": 2,
            "accepted_to_learning_count": 1,
            "evidence_blocked_count": 1,
        }
    }
    survival_rulebook = {
        "governedPromotionReviewItems": [
            {
                "platform": "Reddit",
                "platform_survival_status": "safe_with_review",
            },
            {
                "platform": "TikTok",
                "platform_survival_status": "review_required",
            },
        ],
        "platformSurvivalRulebookSummary": {
            "platform_survival_rulebook_ready": True,
            "review_required_count": 1,
            "rejected_count": 0,
            "reddit_strong_marketing_blocked": True,
            "write_api_called": False,
        },
    }
    drift_monitor = {
        "externalDriftSummary": {
            "external_drift_monitor_ready": True,
            "signal_count": 2,
            "recommendation_effectiveness_declining": True,
            "recommendation_only": True,
            "highest_severity": "high",
            "auto_strategy_change_allowed": False,
            "external_execution_change_allowed": False,
        }
    }

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "controlled_external_interaction_gate"
        report = ControlledExternalInteractionGate(root).evaluate(
            export_pack=export_pack,
            evidence_ledger=evidence_ledger,
            manual_feedback=manual_feedback,
            survival_rulebook=survival_rulebook,
            drift_monitor=drift_monitor,
        )

        assert report["status"] == "controlled_external_interaction_gate_ready"
        gate_report = report["controlledExternalInteractionReport"]
        safety = report["controlledExternalInteractionSafetyReview"]
        actions = report["controlledExternalInteractionActions"]
        checks = report["controlledExternalInteractionChecks"]
        summary = report["controlledExternalInteractionSummary"]

        assert gate_report["human_controlled_trial_allowed"] is True
        assert gate_report["automatic_external_execution_allowed"] is False
        assert summary["gate_decision"] == "human_controlled_trial_allowed"
        assert summary["checks_passed"] is True
        assert summary["human_controlled_trial_allowed"] is True
        assert summary["automatic_external_execution_allowed"] is False
        assert summary["auto_post_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["auto_login_allowed"] is False
        assert summary["platform_write_api_allowed"] is False

        assert safety["automatic_posting_allowed"] is False
        assert safety["automatic_reply_allowed"] is False
        assert safety["automatic_login_allowed"] is False
        assert safety["platform_write_api_allowed"] is False
        assert safety["human_controlled_external_trial_allowed"] is True
        assert "auto_post" in safety["blocked_scope"]
        assert "platform_write_api" in safety["blocked_scope"]

        statuses = {item["gate_status"] for item in actions}
        assert "review_required" in statuses
        assert all(item["automatic_posting_allowed"] is False for item in actions)
        assert all(item["automatic_reply_allowed"] is False for item in actions)
        assert all(item["automatic_login_allowed"] is False for item in actions)
        assert all(item["platform_write_api_allowed"] is False for item in actions)
        assert all(item["external_execution_allowed"] is False for item in actions)

        assert len(checks) == 5
        assert all(item["passed"] is True for item in checks)

        for output_name in [
            "CONTROLLED_EXTERNAL_INTERACTION_GATE_REPORT.json",
            "CONTROLLED_EXTERNAL_INTERACTION_SAFETY_REVIEW.json",
            "controlled_external_interaction_actions.json",
            "controlled_external_interaction_checks.json",
            "controlled_external_interaction_summary.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("controlled_external_interaction_gate_smoke_test passed")


if __name__ == "__main__":
    main()
