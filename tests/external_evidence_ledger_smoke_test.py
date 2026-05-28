from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.external_evidence_ledger import ExternalEvidenceLedger
from services.manual_promotion_export_pack import ManualPromotionExportPack


def main() -> None:
    export_pack = ManualPromotionExportPack().build()
    export_items = export_pack["manualExportItems"]
    assert export_items, "manual export items are required"

    ledger = ExternalEvidenceLedger()
    initial = ledger.build()
    records = initial["externalEvidenceLedger"]
    report = initial["externalEvidenceLedgerReport"]

    assert initial["status"] == "external_evidence_ledger_ready"
    assert report["ledger_ready"] is True
    assert report["manual_export_item_count"] == len(export_items)
    assert report["evidence_record_count"] == len(export_items)
    assert report["all_export_items_bound"] is True
    assert report["feedback_learning_allowed_count"] >= 0
    assert report["feedback_learning_blocked_count"] + report["feedback_learning_allowed_count"] == len(export_items)
    assert report["external_page_auto_verification_enabled"] is False
    assert report["platform_crawling_enabled"] is False
    assert report["platform_api_called"] is False
    assert report["write_api_called"] is False
    assert report["login_scraping_used"] is False

    for record in records:
        assert record["execution_status"] in {"planned", "manually_executed", "evidence_pending", "rejected"}
        assert record["feedback_learning_allowed"] is (
            record["execution_status"] == "manually_executed" and bool(record["platform_url"] or record["screenshot_path"])
        )
        assert record["feedback_learning_blocked"] is (not record["feedback_learning_allowed"])
        assert record["external_page_checked"] is False
        assert record["external_page_auto_verified"] is False
        assert record["platform_api_called"] is False
        assert record["write_api_called"] is False
        assert record["login_scraping_used"] is False

    first_id = records[0]["export_id"]
    updated = ledger.record_evidence(
        first_id,
        execution_status="manually_executed",
        manual_published_at="2026-05-28T18:00:00+09:00",
        platform_url="https://example.com/manual-post-evidence",
        screenshot_path="runtime/evidence_screenshots/manual-post-evidence.png",
        executor="human_operator",
        risk_notes="Manually posted after platform rule check.",
    )
    first = next(item for item in updated["externalEvidenceLedger"] if item["export_id"] == first_id)
    assert first["execution_status"] == "manually_executed"
    assert first["evidence_present"] is True
    assert first["feedback_learning_allowed"] is True
    assert first["feedback_learning_blocked"] is False
    assert first["platform_url"]
    assert first["screenshot_path"]
    assert first["executor"] == "human_operator"

    if len(records) > 1:
        second_id = records[1]["export_id"]
        updated = ledger.record_evidence(second_id, execution_status="rejected", executor="human_operator", risk_notes="Human rejected manual execution.")
        second = next(item for item in updated["externalEvidenceLedger"] if item["export_id"] == second_id)
        assert second["execution_status"] == "rejected"
        assert second["feedback_learning_allowed"] is False
        assert second["feedback_learning_blocked"] is True

    final_report = updated["externalEvidenceLedgerReport"]
    assert final_report["all_export_items_bound"] is True
    assert final_report["feedback_learning_allowed_count"] >= 1
    assert final_report["feedback_learning_blocked_count"] + final_report["feedback_learning_allowed_count"] == len(records)
    assert final_report["status_counts"]["manually_executed"] >= 1
    assert final_report["status_counts"]["rejected"] >= 1 if len(records) > 1 else True
    assert final_report["external_page_auto_verification_enabled"] is False
    assert final_report["platform_crawling_enabled"] is False
    assert final_report["platform_api_called"] is False
    assert final_report["write_api_called"] is False
    assert final_report["login_scraping_used"] is False

    for output_name in [
        "external_evidence_ledger.json",
        "EXTERNAL_EVIDENCE_LEDGER_REPORT.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "external_evidence_ledger" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("external_evidence_ledger_smoke_test passed")


if __name__ == "__main__":
    main()
