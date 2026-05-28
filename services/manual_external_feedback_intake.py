"""Manual intake gate for external promotion feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.external_evidence_ledger import ExternalEvidenceLedger
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/manual_external_feedback_intake")
SUPPORTED_INTAKE_STATUSES = {"accepted_to_learning", "evidence_blocked", "rejected"}


class ManualExternalFeedbackIntake:
    """Import human-entered external feedback without platform collection."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.records_path = self.output_dir / "manual_external_feedback_records.json"
        self.learning_events_path = self.output_dir / "manual_feedback_learning_events.json"
        self.rejected_path = self.output_dir / "manual_feedback_rejected.json"
        self.summary_path = self.output_dir / "manual_external_feedback_summary.json"
        self.report_path = self.output_dir / "MANUAL_EXTERNAL_FEEDBACK_INTAKE_REPORT.json"

    def build(self, manual_feedback: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        ledger_state = ExternalEvidenceLedger().state()
        records = self._manual_records(ledger_state.get("externalEvidenceLedger", []), manual_feedback)
        learning_events = [self._learning_event(item, index + 1) for index, item in enumerate(records) if item["learning_memory_allowed"]]
        rejected = [item for item in records if item["intake_status"] in {"evidence_blocked", "rejected"}]
        learning_report = PromotionFeedbackLearning().learn(feedback_events=learning_events)
        summary = self._summary(records, learning_events, rejected, learning_report)
        payload = {
            "report_id": "MANUAL_EXTERNAL_FEEDBACK_INTAKE_REPORT",
            "created_at": utc_now_iso(),
            "status": "manual_external_feedback_intake_ready",
            "phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "manualExternalFeedbackRecords": records,
            "manualFeedbackLearningEvents": learning_events,
            "manualFeedbackRejected": rejected,
            "manualExternalFeedbackSummary": summary,
            "manualExternalFeedbackReport": summary,
            "safetyBoundary": "Manual feedback intake stores human-entered feedback only. It does not crawl platforms, collect external pages, call platform APIs, verify external URLs, post, reply, DM, follow, or like.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            records = self._read_json(self.records_path, [])
            learning_events = self._read_json(self.learning_events_path, [])
            rejected = self._read_json(self.rejected_path, [])
            summary = self._read_json(self.summary_path, {})
            return {
                "report_id": "MANUAL_EXTERNAL_FEEDBACK_INTAKE_REPORT",
                "status": "manual_external_feedback_intake_ready",
                "manualExternalFeedbackRecords": records,
                "manualFeedbackLearningEvents": learning_events,
                "manualFeedbackRejected": rejected,
                "manualExternalFeedbackSummary": summary,
                "manualExternalFeedbackReport": summary,
            }
        return self.build()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.records_path.write_text(json.dumps(payload["manualExternalFeedbackRecords"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.learning_events_path.write_text(json.dumps(payload["manualFeedbackLearningEvents"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.rejected_path.write_text(json.dumps(payload["manualFeedbackRejected"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["manualExternalFeedbackSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.report_path.write_text(json.dumps(payload["manualExternalFeedbackReport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _manual_records(self, ledger_records: list[dict[str, Any]], manual_feedback: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        feedback_by_export = {item.get("export_id", ""): item for item in manual_feedback or []}
        records = []
        for index, ledger in enumerate(ledger_records, start=1):
            feedback = feedback_by_export.get(ledger.get("export_id", ""), self._sample_feedback_for_ledger(ledger, index))
            records.append(self._record(index, ledger, feedback))
        return records

    @staticmethod
    def _sample_feedback_for_ledger(ledger: dict[str, Any], index: int) -> dict[str, Any]:
        if ledger.get("feedback_learning_allowed"):
            return {
                "views": 420 + index * 37,
                "likes": 12 + index,
                "replies": 3,
                "saves": 5,
                "comments": ["Manual feedback: helpful route answer", "Manual feedback: soft CTA was acceptable"],
                "rejection_reason": "",
                "source_boundary": "real_external_feedback",
            }
        if ledger.get("execution_status") == "rejected":
            return {
                "views": 0,
                "likes": 0,
                "replies": 0,
                "saves": 0,
                "comments": [],
                "rejection_reason": ledger.get("risk_notes") or "Human rejected manual execution.",
                "source_boundary": "manual",
            }
        return {
            "views": 0,
            "likes": 0,
            "replies": 0,
            "saves": 0,
            "comments": [],
            "rejection_reason": "",
            "source_boundary": "manual",
        }

    def _record(self, index: int, ledger: dict[str, Any], feedback: dict[str, Any]) -> dict[str, Any]:
        has_evidence = bool(ledger.get("feedback_learning_allowed"))
        rejected = bool(feedback.get("rejection_reason")) or ledger.get("execution_status") == "rejected"
        if rejected:
            intake_status = "rejected"
        elif has_evidence:
            intake_status = "accepted_to_learning"
        else:
            intake_status = "evidence_blocked"
        return {
            "feedback_intake_id": f"MANUAL-FEEDBACK-{index:03d}",
            "evidence_id": ledger.get("evidence_id", ""),
            "export_id": ledger.get("export_id", ""),
            "workspace_id": ledger.get("workspace_id", ""),
            "merchant_name": ledger.get("merchant_name", ""),
            "platform": ledger.get("platform", ""),
            "feedback_source": "manual_import",
            "source_boundary": feedback.get("source_boundary", "manual"),
            "views": int(feedback.get("views", 0) or 0),
            "likes": int(feedback.get("likes", 0) or 0),
            "replies": int(feedback.get("replies", 0) or 0),
            "saves": int(feedback.get("saves", 0) or 0),
            "comments": list(feedback.get("comments", []) or []),
            "rejection_reason": feedback.get("rejection_reason", ""),
            "intake_status": intake_status,
            "execution_status": ledger.get("execution_status", ""),
            "evidence_present": bool(ledger.get("evidence_present")),
            "platform_url": ledger.get("platform_url", ""),
            "screenshot_path": ledger.get("screenshot_path", ""),
            "learning_memory_allowed": has_evidence and intake_status == "accepted_to_learning",
            "learning_memory_block_reason": "" if has_evidence and intake_status == "accepted_to_learning" else "Missing execution evidence or feedback was rejected.",
            "sample_data_only": feedback.get("source_boundary") == "sample",
            "real_external_feedback": feedback.get("source_boundary") == "real_external_feedback" and has_evidence,
            "auto_collection_used": False,
            "platform_api_called": False,
            "external_page_verified": False,
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _learning_event(record: dict[str, Any], index: int) -> dict[str, Any]:
        positive_signal = record["likes"] + record["replies"] + record["saves"]
        feedback_type = "liked"
        if record["replies"] > 0:
            feedback_type = "replied"
        if record["saves"] > record["likes"]:
            feedback_type = "saved"
        if positive_signal == 0 and record["views"] > 0:
            feedback_type = "ignored"
        return {
            "feedback_id": f"MANUAL-EXTERNAL-LEARNING-{index:03d}",
            "feedback_type": feedback_type,
            "source_type": "manual_external_feedback",
            "source_id": record["feedback_intake_id"],
            "workspace_id": record["workspace_id"],
            "merchant_name": record["merchant_name"],
            "platform": record["platform"],
            "market": "Japan",
            "problem_type": "external_promotion_response",
            "pain_point": "manual_external_signal",
            "answer_style": "human_posted_export",
            "cta_style": "answer_first_soft_reference",
            "content_format": "manual_external_post",
            "risk_pattern": "evidence_backed",
            "evidence": f"external_evidence_ledger:{record['evidence_id']}",
            "views": record["views"],
            "likes": record["likes"],
            "replies": record["replies"],
            "saves": record["saves"],
            "comments": record["comments"],
            "sample_data_only": record["sample_data_only"],
            "real_business_result": False,
            "auto_next_action_allowed": False,
        }

    @staticmethod
    def _summary(
        records: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
        rejected: list[dict[str, Any]],
        learning_report: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "manual_feedback_intake_ready": True,
            "feedback_record_count": len(records),
            "accepted_to_learning_count": len([item for item in records if item["intake_status"] == "accepted_to_learning"]),
            "evidence_blocked_count": len([item for item in records if item["intake_status"] == "evidence_blocked"]),
            "rejected_count": len([item for item in records if item["intake_status"] == "rejected"]),
            "learning_event_count": len(learning_events),
            "feedback_source": "manual_import",
            "boundaries": ["sample", "manual", "real_external_feedback"],
            "missing_evidence_blocked_from_learning": all(
                item["learning_memory_allowed"] is False for item in records if not item["evidence_present"]
            ),
            "promotion_feedback_learning_updated": learning_report.get("status") == "promotion_feedback_learning_ready",
            "promotion_learning_event_count": learning_report.get("promotionFeedbackSummary", {}).get("feedback_event_count", 0),
            "auto_collection_used": False,
            "platform_api_called": False,
            "external_page_auto_verified": False,
        }


if __name__ == "__main__":
    result = ManualExternalFeedbackIntake().build()
    print(json.dumps({"status": result["status"], "summary": result["manualExternalFeedbackSummary"]}, indent=2))
