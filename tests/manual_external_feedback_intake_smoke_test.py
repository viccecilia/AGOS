from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.external_evidence_ledger import ExternalEvidenceLedger
from services.manual_external_feedback_intake import ManualExternalFeedbackIntake
from services.manual_promotion_export_pack import ManualPromotionExportPack


def main() -> None:
    export_pack = ManualPromotionExportPack().build()
    export_items = export_pack["manualExportItems"]
    assert len(export_items) >= 2, "manual export items are required"

    ledger = ExternalEvidenceLedger()
    ledger.build()
    ledger.record_evidence(
        export_items[0]["export_id"],
        execution_status="manually_executed",
        manual_published_at="2026-05-28T19:30:00+09:00",
        platform_url="https://example.com/manual-feedback-source",
        screenshot_path="runtime/evidence_screenshots/manual-feedback-source.png",
        executor="human_operator",
        risk_notes="Manual evidence entered after human execution.",
    )
    ledger.record_evidence(
        export_items[1]["export_id"],
        execution_status="evidence_pending",
        executor="human_operator",
        risk_notes="No external evidence yet.",
    )
    if len(export_items) > 2:
        ledger.record_evidence(
            export_items[2]["export_id"],
            execution_status="rejected",
            executor="human_operator",
            risk_notes="Human rejected external execution after manual review.",
        )

    manual_feedback = [
        {
            "export_id": export_items[0]["export_id"],
            "views": 680,
            "likes": 31,
            "replies": 7,
            "saves": 12,
            "comments": ["Useful answer", "The homepage reference was not pushy"],
            "rejection_reason": "",
            "source_boundary": "real_external_feedback",
        },
        {
            "export_id": export_items[1]["export_id"],
            "views": 95,
            "likes": 3,
            "replies": 0,
            "saves": 1,
            "comments": ["No evidence should block learning"],
            "rejection_reason": "",
            "source_boundary": "manual",
        },
    ]
    if len(export_items) > 2:
        manual_feedback.append(
            {
                "export_id": export_items[2]["export_id"],
                "views": 0,
                "likes": 0,
                "replies": 0,
                "saves": 0,
                "comments": [],
                "rejection_reason": "Manual operator rejected this external action.",
                "source_boundary": "manual",
            }
        )

    report = ManualExternalFeedbackIntake().build(manual_feedback=manual_feedback)
    records = report["manualExternalFeedbackRecords"]
    learning_events = report["manualFeedbackLearningEvents"]
    rejected = report["manualFeedbackRejected"]
    summary = report["manualExternalFeedbackSummary"]

    assert report["status"] == "manual_external_feedback_intake_ready"
    assert summary["manual_feedback_intake_ready"] is True
    assert summary["feedback_source"] == "manual_import"
    assert {"sample", "manual", "real_external_feedback"} <= set(summary["boundaries"])
    assert summary["accepted_to_learning_count"] >= 1
    assert summary["evidence_blocked_count"] >= 1
    assert summary["rejected_count"] >= 1
    assert summary["missing_evidence_blocked_from_learning"] is True
    assert summary["promotion_feedback_learning_updated"] is True
    assert summary["auto_collection_used"] is False
    assert summary["platform_api_called"] is False
    assert summary["external_page_auto_verified"] is False

    accepted = [item for item in records if item["intake_status"] == "accepted_to_learning"]
    blocked = [item for item in records if item["intake_status"] == "evidence_blocked"]
    assert accepted, "at least one evidence-backed feedback record must enter learning"
    assert blocked, "missing evidence feedback must be blocked"
    assert rejected, "rejected or blocked records must be traceable"

    for record in records:
        assert record["feedback_source"] == "manual_import"
        assert record["intake_status"] in {"accepted_to_learning", "evidence_blocked", "rejected"}
        assert record["auto_collection_used"] is False
        assert record["platform_api_called"] is False
        assert record["external_page_verified"] is False
        if not record["evidence_present"]:
            assert record["learning_memory_allowed"] is False

    learned_sources = {event["source_id"] for event in learning_events}
    assert accepted[0]["feedback_intake_id"] in learned_sources
    assert not any(item["feedback_intake_id"] in learned_sources for item in blocked), "blocked feedback cannot enter learning memory"

    for output_name in [
        "manual_external_feedback_records.json",
        "manual_feedback_learning_events.json",
        "manual_feedback_rejected.json",
        "manual_external_feedback_summary.json",
        "MANUAL_EXTERNAL_FEEDBACK_INTAKE_REPORT.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "manual_external_feedback_intake" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("manual_external_feedback_intake_smoke_test passed")


if __name__ == "__main__":
    main()
