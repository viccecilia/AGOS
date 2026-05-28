"""Evidence ledger for manually executed external promotion items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.manual_promotion_export_pack import ManualPromotionExportPack
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/external_evidence_ledger")
LEDGER_STATUSES = {"planned", "manually_executed", "evidence_pending", "rejected"}


class ExternalEvidenceLedger:
    """Track manual external execution evidence without crawling or validating platforms."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.ledger_path = self.output_dir / "external_evidence_ledger.json"
        self.report_path = self.output_dir / "EXTERNAL_EVIDENCE_LEDGER_REPORT.json"

    def build(self) -> dict[str, Any]:
        export_pack = ManualPromotionExportPack().state()
        existing = self._read_existing_records()
        records = [self._record_for_export_item(item, existing.get(item.get("export_id", ""))) for item in export_pack.get("manualExportItems", [])]
        report = self._report(records, export_pack)
        payload = {
            "report_id": "EXTERNAL_EVIDENCE_LEDGER_REPORT",
            "created_at": utc_now_iso(),
            "status": "external_evidence_ledger_ready",
            "phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "schema": self.schema(),
            "externalEvidenceLedger": records,
            "externalEvidenceLedgerReport": report,
            "safetyBoundary": "Evidence Ledger records human-provided publication evidence only. It does not crawl, scrape, log in, verify external pages, post, reply, DM, follow, like, or call platform APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.report_path.exists() and self.ledger_path.exists():
            records = self._read_json(self.ledger_path, [])
            report = self._read_json(self.report_path, {})
            return {
                "report_id": "EXTERNAL_EVIDENCE_LEDGER_REPORT",
                "status": "external_evidence_ledger_ready",
                "schema": self.schema(),
                "externalEvidenceLedger": records,
                "externalEvidenceLedgerReport": report,
            }
        return self.build()

    def record_evidence(
        self,
        export_id: str,
        *,
        execution_status: str,
        manual_published_at: str = "",
        platform_url: str = "",
        screenshot_path: str = "",
        executor: str = "",
        risk_notes: str = "",
    ) -> dict[str, Any]:
        if execution_status not in LEDGER_STATUSES:
            raise ValueError(f"execution_status must be one of {sorted(LEDGER_STATUSES)}")
        payload = self.build()
        records = payload["externalEvidenceLedger"]
        matched = False
        for record in records:
            if record["export_id"] == export_id:
                record.update(
                    {
                        "execution_status": execution_status,
                        "manual_published_at": manual_published_at,
                        "platform_url": platform_url,
                        "screenshot_path": screenshot_path,
                        "executor": executor,
                        "risk_notes": risk_notes,
                        "updated_at": utc_now_iso(),
                    }
                )
                record.update(self._evidence_flags(record))
                matched = True
        if not matched:
            raise ValueError(f"export_id not found: {export_id}")
        report = self._report(records, ManualPromotionExportPack().state())
        updated = {
            **payload,
            "externalEvidenceLedger": records,
            "externalEvidenceLedgerReport": report,
        }
        self.persist(updated)
        return updated

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps(payload["externalEvidenceLedger"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.report_path.write_text(json.dumps(payload["externalEvidenceLedgerReport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def schema() -> dict[str, Any]:
        return {
            "required_fields": [
                "evidence_id",
                "export_id",
                "platform",
                "manual_published_at",
                "platform_url",
                "screenshot_path",
                "executor",
                "risk_notes",
                "execution_status",
                "feedback_learning_allowed",
            ],
            "execution_status_enum": sorted(LEDGER_STATUSES),
            "evidence_policy": "Only manually_executed records with platform_url or screenshot_path can enter feedback learning.",
            "external_validation": "disabled",
        }

    def _read_existing_records(self) -> dict[str, dict[str, Any]]:
        records = self._read_json(self.ledger_path, [])
        return {item.get("export_id", ""): item for item in records}

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _record_for_export_item(self, item: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
        if existing:
            base = dict(existing)
        else:
            base = {
                "evidence_id": f"EVIDENCE-{item.get('export_id', 'UNKNOWN')}",
                "export_id": item.get("export_id", ""),
                "review_id": item.get("review_id", ""),
                "source_id": item.get("source_id", ""),
                "workspace_id": item.get("workspace_id", ""),
                "merchant_name": item.get("merchant_name", ""),
                "platform": item.get("platform", ""),
                "content_format": item.get("content_format", ""),
                "risk_level": item.get("risk_level", "medium"),
                "human_approval_status": item.get("human_approval_status", ""),
                "manual_published_at": "",
                "platform_url": "",
                "screenshot_path": "",
                "executor": "",
                "risk_notes": "",
                "execution_status": "evidence_pending",
                "created_at": utc_now_iso(),
                "updated_at": "",
                "external_page_checked": False,
                "external_page_auto_verified": False,
                "platform_api_called": False,
                "write_api_called": False,
                "login_scraping_used": False,
            }
        base.update(self._evidence_flags(base))
        return base

    @staticmethod
    def _evidence_flags(record: dict[str, Any]) -> dict[str, Any]:
        has_evidence = bool(record.get("platform_url") or record.get("screenshot_path"))
        executed_with_evidence = record.get("execution_status") == "manually_executed" and has_evidence
        return {
            "evidence_present": has_evidence,
            "feedback_learning_allowed": executed_with_evidence,
            "feedback_learning_blocked": not executed_with_evidence,
            "feedback_block_reason": "" if executed_with_evidence else "Missing human evidence or execution is not marked manually_executed.",
        }

    @staticmethod
    def _report(records: list[dict[str, Any]], export_pack: dict[str, Any]) -> dict[str, Any]:
        status_counts = {status: len([item for item in records if item.get("execution_status") == status]) for status in sorted(LEDGER_STATUSES)}
        return {
            "ledger_ready": True,
            "manual_export_item_count": len(export_pack.get("manualExportItems", [])),
            "evidence_record_count": len(records),
            "all_export_items_bound": len(records) == len(export_pack.get("manualExportItems", [])),
            "status_counts": status_counts,
            "evidence_present_count": len([item for item in records if item.get("evidence_present")]),
            "feedback_learning_allowed_count": len([item for item in records if item.get("feedback_learning_allowed")]),
            "feedback_learning_blocked_count": len([item for item in records if item.get("feedback_learning_blocked")]),
            "missing_evidence_export_ids": [item.get("export_id") for item in records if item.get("feedback_learning_blocked") and item.get("execution_status") != "rejected"],
            "rejected_export_ids": [item.get("export_id") for item in records if item.get("execution_status") == "rejected"],
            "external_page_auto_verification_enabled": False,
            "platform_crawling_enabled": False,
            "platform_api_called": any(item.get("platform_api_called") for item in records),
            "write_api_called": any(item.get("write_api_called") for item in records),
            "login_scraping_used": any(item.get("login_scraping_used") for item in records),
            "feedback_learning_gate": "blocked_without_evidence",
        }


if __name__ == "__main__":
    result = ExternalEvidenceLedger().build()
    print(json.dumps({"status": result["status"], "report": result["externalEvidenceLedgerReport"]}, indent=2))
