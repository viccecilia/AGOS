"""Gate for controlled, human-only external interaction trials."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.external_drift_monitor import ExternalDriftMonitor
from services.external_evidence_ledger import ExternalEvidenceLedger
from services.manual_external_feedback_intake import ManualExternalFeedbackIntake
from services.manual_promotion_export_pack import ManualPromotionExportPack
from services.platform_survival_rulebook import PlatformSurvivalRulebook
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/controlled_external_interaction_gate")


class ControlledExternalInteractionGate:
    """Decide whether AGOS can enter a small human-controlled external trial."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "CONTROLLED_EXTERNAL_INTERACTION_GATE_REPORT.json"
        self.safety_path = self.output_dir / "CONTROLLED_EXTERNAL_INTERACTION_SAFETY_REVIEW.json"
        self.actions_path = self.output_dir / "controlled_external_interaction_actions.json"
        self.checks_path = self.output_dir / "controlled_external_interaction_checks.json"
        self.summary_path = self.output_dir / "controlled_external_interaction_summary.json"

    def evaluate(
        self,
        export_pack: dict[str, Any] | None = None,
        evidence_ledger: dict[str, Any] | None = None,
        manual_feedback: dict[str, Any] | None = None,
        survival_rulebook: dict[str, Any] | None = None,
        drift_monitor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        export_pack = export_pack or ManualPromotionExportPack().state()
        evidence_ledger = evidence_ledger or ExternalEvidenceLedger().state()
        manual_feedback = manual_feedback or ManualExternalFeedbackIntake().state()
        survival_rulebook = survival_rulebook or PlatformSurvivalRulebook().state()
        drift_monitor = drift_monitor or ExternalDriftMonitor().state()

        checks = self._checks(export_pack, evidence_ledger, manual_feedback, survival_rulebook, drift_monitor)
        safety_review = self._safety_review(export_pack, evidence_ledger, survival_rulebook, drift_monitor)
        actions = self._actions(export_pack, evidence_ledger, survival_rulebook, drift_monitor)
        summary = self._summary(checks, safety_review, actions)
        report = {
            "report_id": "CONTROLLED_EXTERNAL_INTERACTION_GATE_REPORT",
            "created_at": utc_now_iso(),
            "status": "controlled_external_interaction_gate_ready",
            "phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "gateDecision": summary["gate_decision"],
            "controlledExternalInteractionReport": {
                "export_pack_ready": checks["export_pack_ready"]["passed"],
                "evidence_ledger_ready": checks["evidence_ledger_ready"]["passed"],
                "manual_feedback_ready": checks["manual_feedback_ready"]["passed"],
                "survival_rulebook_ready": checks["survival_rulebook_ready"]["passed"],
                "drift_monitor_ready": checks["drift_monitor_ready"]["passed"],
                "human_controlled_trial_allowed": summary["human_controlled_trial_allowed"],
                "automatic_external_execution_allowed": False,
                "next_stage_recommendation": summary["next_stage_recommendation"],
            },
            "controlledExternalInteractionSafetyReview": safety_review,
            "controlledExternalInteractionActions": actions,
            "controlledExternalInteractionChecks": list(checks.values()),
            "controlledExternalInteractionSummary": summary,
            "safetyBoundary": "Gate permits only human-controlled external trial preparation. It does not enable automatic posting, replying, login, account operation, platform API writes, scraping, DMs, follows, or likes.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            report = self._read_json(self.report_path, {})
            return {
                "report_id": "CONTROLLED_EXTERNAL_INTERACTION_GATE_REPORT",
                "status": "controlled_external_interaction_gate_ready",
                "controlledExternalInteractionReport": report.get("controlledExternalInteractionReport", {}),
                "controlledExternalInteractionSafetyReview": self._read_json(self.safety_path, {}),
                "controlledExternalInteractionActions": self._read_json(self.actions_path, []),
                "controlledExternalInteractionChecks": self._read_json(self.checks_path, []),
                "controlledExternalInteractionSummary": self._read_json(self.summary_path, {}),
            }
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.safety_path.write_text(json.dumps(report["controlledExternalInteractionSafetyReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.actions_path.write_text(json.dumps(report["controlledExternalInteractionActions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(report["controlledExternalInteractionChecks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["controlledExternalInteractionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _checks(
        export_pack: dict[str, Any],
        evidence_ledger: dict[str, Any],
        manual_feedback: dict[str, Any],
        survival_rulebook: dict[str, Any],
        drift_monitor: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        export_summary = export_pack.get("manualExportSummary", {})
        evidence_report = evidence_ledger.get("externalEvidenceLedgerReport", {})
        feedback_summary = manual_feedback.get("manualExternalFeedbackSummary", {})
        rulebook_summary = survival_rulebook.get("platformSurvivalRulebookSummary", {})
        drift_summary = drift_monitor.get("externalDriftSummary", {})
        return {
            "export_pack_ready": {
                "check": "Manual Promotion Export Pack",
                "passed": bool(export_summary.get("manual_export_pack_ready")) and export_summary.get("external_execution_allowed") is False,
                "evidence": f"items={export_summary.get('export_item_count', 0)}; human_gate={export_summary.get('human_gate_required')}; external_execution_allowed={export_summary.get('external_execution_allowed')}",
            },
            "evidence_ledger_ready": {
                "check": "External Evidence Ledger",
                "passed": bool(evidence_report.get("ledger_ready")) and evidence_report.get("all_export_items_bound") is True,
                "evidence": f"records={evidence_report.get('evidence_record_count', 0)}; all_bound={evidence_report.get('all_export_items_bound')}; allowed_feedback={evidence_report.get('feedback_learning_allowed_count', 0)}",
            },
            "manual_feedback_ready": {
                "check": "Manual External Feedback Intake",
                "passed": bool(feedback_summary.get("manual_feedback_intake_ready")) and feedback_summary.get("feedback_source") == "manual_import",
                "evidence": f"records={feedback_summary.get('feedback_record_count', 0)}; accepted={feedback_summary.get('accepted_to_learning_count', 0)}; blocked={feedback_summary.get('evidence_blocked_count', 0)}",
            },
            "survival_rulebook_ready": {
                "check": "Platform Survival Rulebook",
                "passed": bool(rulebook_summary.get("platform_survival_rulebook_ready")) and rulebook_summary.get("write_api_called") is False,
                "evidence": f"review_required={rulebook_summary.get('review_required_count', 0)}; rejected={rulebook_summary.get('rejected_count', 0)}; reddit_blocked={rulebook_summary.get('reddit_strong_marketing_blocked')}",
            },
            "drift_monitor_ready": {
                "check": "External Drift Monitor",
                "passed": bool(drift_summary.get("external_drift_monitor_ready")) and drift_summary.get("external_execution_change_allowed") is False,
                "evidence": f"signals={drift_summary.get('signal_count', 0)}; declining={drift_summary.get('recommendation_effectiveness_declining')}; recommendation_only={drift_summary.get('recommendation_only')}",
            },
        }

    @staticmethod
    def _safety_review(
        export_pack: dict[str, Any],
        evidence_ledger: dict[str, Any],
        survival_rulebook: dict[str, Any],
        drift_monitor: dict[str, Any],
    ) -> dict[str, Any]:
        export_summary = export_pack.get("manualExportSummary", {})
        evidence_report = evidence_ledger.get("externalEvidenceLedgerReport", {})
        survival_summary = survival_rulebook.get("platformSurvivalRulebookSummary", {})
        drift_summary = drift_monitor.get("externalDriftSummary", {})
        return {
            "safety_boundary_passed": True,
            "automatic_posting_allowed": False,
            "automatic_reply_allowed": False,
            "automatic_login_allowed": False,
            "platform_write_api_allowed": False,
            "automatic_dm_allowed": False,
            "automatic_follow_allowed": False,
            "automatic_like_allowed": False,
            "login_scraping_allowed": False,
            "platform_crawling_allowed": False,
            "human_controlled_external_trial_allowed": True,
            "allowed_scope": "manual_copy_execute_only_after_human_review",
            "blocked_scope": [
                "auto_post",
                "auto_reply",
                "auto_login",
                "platform_write_api",
                "auto_dm",
                "auto_follow",
                "auto_like",
                "login_scraping",
                "platform_crawling",
            ],
            "source_boundaries": {
                "export_pack_external_execution_allowed": export_summary.get("external_execution_allowed", True),
                "evidence_platform_api_called": evidence_report.get("platform_api_called", True),
                "survival_write_api_called": survival_summary.get("write_api_called", True),
                "drift_auto_strategy_change_allowed": drift_summary.get("auto_strategy_change_allowed", True),
                "drift_external_execution_change_allowed": drift_summary.get("external_execution_change_allowed", True),
            },
        }

    @staticmethod
    def _actions(
        export_pack: dict[str, Any],
        evidence_ledger: dict[str, Any],
        survival_rulebook: dict[str, Any],
        drift_monitor: dict[str, Any],
    ) -> list[dict[str, Any]]:
        export_items = export_pack.get("manualExportItems", [])
        evidence_by_export = {item.get("export_id"): item for item in evidence_ledger.get("externalEvidenceLedger", [])}
        governed_by_platform = {}
        for item in survival_rulebook.get("governedPromotionReviewItems", []):
            platform = item.get("platform") or item.get("platform_survival_platform")
            governed_by_platform.setdefault(platform, item)
        drift_summary = drift_monitor.get("externalDriftSummary", {})
        actions = []
        for index, item in enumerate(export_items, start=1):
            evidence = evidence_by_export.get(item.get("export_id"), {})
            governed = governed_by_platform.get(item.get("platform"), {})
            survival_status = governed.get("platform_survival_status", "review_required")
            if survival_status == "rejected":
                gate_status = "blocked"
                reason = "Platform survival rulebook rejected this action."
            elif drift_summary.get("highest_severity") == "high":
                gate_status = "review_required"
                reason = "External drift monitor has high-severity findings; human review required before trial."
            elif evidence.get("feedback_learning_allowed"):
                gate_status = "allowed"
                reason = "Human-approved export has evidence-backed feedback and no automatic execution path."
            else:
                gate_status = "review_required"
                reason = "Evidence or feedback is incomplete; human review required before manual trial."
            actions.append(
                {
                    "gate_action_id": f"CONTROLLED-EXT-ACTION-{index:03d}",
                    "export_id": item.get("export_id", ""),
                    "platform": item.get("platform", ""),
                    "content_format": item.get("content_format", ""),
                    "risk_level": item.get("risk_level", "medium"),
                    "gate_status": gate_status,
                    "gate_reason": reason,
                    "human_review_required": gate_status != "allowed",
                    "human_controlled_trial_allowed": gate_status in {"allowed", "review_required"},
                    "automatic_posting_allowed": False,
                    "automatic_reply_allowed": False,
                    "automatic_login_allowed": False,
                    "platform_write_api_allowed": False,
                    "external_execution_allowed": False,
                    "evidence_status": evidence.get("execution_status", "evidence_pending"),
                    "survival_status": survival_status,
                    "drift_highest_severity": drift_summary.get("highest_severity", "unknown"),
                }
            )
        if not actions:
            actions.append(
                {
                    "gate_action_id": "CONTROLLED-EXT-ACTION-000",
                    "export_id": "",
                    "platform": "none",
                    "gate_status": "blocked",
                    "gate_reason": "No manual export items are available for controlled external trial.",
                    "human_review_required": True,
                    "human_controlled_trial_allowed": False,
                    "automatic_posting_allowed": False,
                    "automatic_reply_allowed": False,
                    "automatic_login_allowed": False,
                    "platform_write_api_allowed": False,
                    "external_execution_allowed": False,
                }
            )
        return actions

    @staticmethod
    def _summary(checks: dict[str, dict[str, Any]], safety_review: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
        blocked = [item for item in actions if item["gate_status"] == "blocked"]
        review_required = [item for item in actions if item["gate_status"] == "review_required"]
        allowed = [item for item in actions if item["gate_status"] == "allowed"]
        checks_passed = all(item["passed"] for item in checks.values())
        human_trial_allowed = checks_passed and safety_review["human_controlled_external_trial_allowed"] and len(actions) > 0
        return {
            "controlled_external_interaction_gate_ready": True,
            "gate_decision": "human_controlled_trial_allowed" if human_trial_allowed else "blocked",
            "checks_passed": checks_passed,
            "human_controlled_trial_allowed": human_trial_allowed,
            "automatic_external_execution_allowed": False,
            "allowed_action_count": len(allowed),
            "review_required_action_count": len(review_required),
            "blocked_action_count": len(blocked),
            "action_count": len(actions),
            "auto_post_allowed": False,
            "auto_reply_allowed": False,
            "auto_login_allowed": False,
            "platform_write_api_allowed": False,
            "next_stage_recommendation": "Start only a small human-controlled external trial. Keep all automatic external execution disabled.",
        }


if __name__ == "__main__":
    result = ControlledExternalInteractionGate().evaluate()
    print(json.dumps({"status": result["status"], "summary": result["controlledExternalInteractionSummary"]}, indent=2))
