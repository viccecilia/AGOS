"""Training acceptance export package for Workbench."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.agos_workbench_adapter_contract import AGOSWorkbenchAdapterContract
from services.controlled_external_interaction_gate import ControlledExternalInteractionGate
from services.external_drift_monitor import ExternalDriftMonitor
from services.external_evidence_ledger import ExternalEvidenceLedger
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.runtime_persistence import utc_now_iso
from services.runtime_replay_training import RuntimeReplayTraining


DEFAULT_OUTPUT_DIR = Path("runtime/agos_training_acceptance_export")


class AGOSTrainingAcceptanceExport:
    """Export AGOS training acceptance evidence for read-only Workbench ingestion."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.package_path = self.output_dir / "AGOS_TRAINING_ACCEPTANCE_EXPORT.json"
        self.capability_score_path = self.output_dir / "capability_score.json"
        self.replay_result_path = self.output_dir / "replay_result.json"
        self.feedback_evidence_path = self.output_dir / "feedback_evidence.json"
        self.drift_result_path = self.output_dir / "drift_result.json"
        self.gate_status_path = self.output_dir / "gate_status.json"
        self.blocked_risks_path = self.output_dir / "blocked_risks.json"
        self.summary_path = self.output_dir / "training_acceptance_summary.json"

    def export(
        self,
        *,
        adapter_contract: dict[str, Any] | None = None,
        replay: dict[str, Any] | None = None,
        feedback: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        drift: dict[str, Any] | None = None,
        gate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        adapter_contract = adapter_contract or AGOSWorkbenchAdapterContract().state()
        replay = replay or RuntimeReplayTraining().state()
        feedback = feedback or PromotionFeedbackLearning().state()
        evidence = evidence or ExternalEvidenceLedger().state()
        drift = drift or ExternalDriftMonitor().state()
        gate = gate or ControlledExternalInteractionGate().state()

        replay_result = self._replay_result(replay)
        feedback_evidence = self._feedback_evidence(feedback, evidence)
        drift_result = self._drift_result(drift)
        gate_status = self._gate_status(gate, adapter_contract)
        blocked_risks = self._blocked_risks(adapter_contract, gate, drift, feedback_evidence)
        capability_score = self._capability_score(replay_result, feedback_evidence, drift_result, gate_status, blocked_risks)
        summary = self._summary(capability_score, replay_result, feedback_evidence, drift_result, gate_status, blocked_risks)

        package = {
            "report_id": "AGOS_TRAINING_ACCEPTANCE_EXPORT",
            "round_id": "ROUND-WB-AGOS-002",
            "created_at": utc_now_iso(),
            "status": "training_acceptance_export_ready",
            "phase": "WORKBENCH_AGOS_ADAPTER",
            "target_consumer": "Workbench",
            "export_policy": {
                "read_only": True,
                "contains_secret_values": False,
                "business_code_write_allowed": False,
                "external_action_start_allowed": False,
                "platform_write_api_allowed": False,
                "credential_value_export_allowed": False,
            },
            "capabilityScore": capability_score,
            "replayResult": replay_result,
            "feedbackEvidence": feedback_evidence,
            "driftResult": drift_result,
            "gateStatus": gate_status,
            "blockedRisks": blocked_risks,
            "trainingAcceptanceSummary": summary,
            "safetyBoundary": "Training Acceptance Export is a read-only evidence package for Workbench. It does not export secrets, modify AGOS code, start external platform actions, or call write APIs.",
        }
        self.persist(package)
        return package

    def state(self) -> dict[str, Any]:
        if self.package_path.exists():
            return json.loads(self.package_path.read_text(encoding="utf-8"))
        return self.export()

    def persist(self, package: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.capability_score_path.write_text(json.dumps(package["capabilityScore"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.replay_result_path.write_text(json.dumps(package["replayResult"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feedback_evidence_path.write_text(json.dumps(package["feedbackEvidence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.drift_result_path.write_text(json.dumps(package["driftResult"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.gate_status_path.write_text(json.dumps(package["gateStatus"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.blocked_risks_path.write_text(json.dumps(package["blockedRisks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(package["trainingAcceptanceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _replay_result(replay: dict[str, Any]) -> dict[str, Any]:
        summary = replay.get("replayTrainingSummary", {})
        memory = replay.get("replayMemory", [])
        replayed = len([item for item in memory if item.get("status") == "replayed"])
        avg_weight = round(sum(float(item.get("training_weight", 0)) for item in memory) / max(len(memory), 1), 3)
        return {
            "status": replay.get("status", "unknown"),
            "replay_items": len(replay.get("replayTrainingItems", [])),
            "replayed_memory_items": replayed,
            "average_training_weight": avg_weight,
            "source_types": replay.get("replaySourceTypes", []),
            "summary": summary,
            "acceptance_passed": replayed > 0 and avg_weight >= 0.5,
        }

    @staticmethod
    def _feedback_evidence(feedback: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        feedback_summary = feedback.get("promotionFeedbackSummary", {})
        evidence_report = evidence.get("externalEvidenceLedgerReport", {})
        best_patterns = feedback.get("bestPromotionPatterns", [])
        failed_patterns = feedback.get("failedPromotionPatterns", [])
        return {
            "feedback_status": feedback.get("status", "unknown"),
            "feedback_event_count": feedback_summary.get("feedback_event_count", len(feedback.get("promotionFeedbackEvents", []))),
            "best_pattern_count": len(best_patterns),
            "failed_pattern_count": len(failed_patterns),
            "supported_feedback_types": feedback.get("supportedFeedbackTypes", []),
            "evidence_ledger_ready": bool(evidence_report.get("ledger_ready")),
            "evidence_record_count": evidence_report.get("evidence_record_count", len(evidence.get("externalEvidenceLedger", []))),
            "feedback_learning_allowed_count": evidence_report.get("feedback_learning_allowed_count", 0),
            "missing_evidence_blocks_learning": evidence_report.get("feedback_learning_gate") == "blocked_without_evidence",
            "sample_or_manual_boundary": "Feedback evidence is local/manual/sample bounded unless evidence ledger marks a manually executed item.",
            "acceptance_passed": len(best_patterns) > 0 and len(failed_patterns) > 0 and bool(evidence_report.get("ledger_ready")),
        }

    @staticmethod
    def _drift_result(drift: dict[str, Any]) -> dict[str, Any]:
        summary = drift.get("externalDriftSummary", {})
        signals = drift.get("externalDriftSignals", [])
        return {
            "drift_status": drift.get("status", "unknown"),
            "signal_count": summary.get("signal_count", len(signals)),
            "highest_severity": summary.get("highest_severity", "unknown"),
            "recommendation_only": summary.get("recommendation_only", True),
            "external_execution_change_allowed": summary.get("external_execution_change_allowed", False),
            "auto_strategy_change_allowed": summary.get("auto_strategy_change_allowed", False),
            "drift_types": sorted({item.get("drift_type", "") for item in signals if item.get("drift_type")}),
            "acceptance_passed": drift.get("status") == "external_drift_monitor_ready"
            and summary.get("recommendation_only") is True
            and summary.get("external_execution_change_allowed") is False,
        }

    @staticmethod
    def _gate_status(gate: dict[str, Any], adapter_contract: dict[str, Any]) -> dict[str, Any]:
        gate_summary = gate.get("controlledExternalInteractionSummary", {})
        adapter_summary = adapter_contract.get("workbenchAdapterSummary", {})
        safety = gate.get("controlledExternalInteractionSafetyReview", {})
        return {
            "controlled_external_gate_decision": gate_summary.get("gate_decision", "unknown"),
            "controlled_external_gate_ready": gate_summary.get("controlled_external_interaction_gate_ready", False),
            "human_controlled_trial_allowed": gate_summary.get("human_controlled_trial_allowed", False),
            "automatic_external_execution_allowed": gate_summary.get("automatic_external_execution_allowed", True),
            "review_required_action_count": gate_summary.get("review_required_action_count", 0),
            "blocked_action_count": gate_summary.get("blocked_action_count", 0),
            "workbench_adapter_ready": adapter_summary.get("workbench_adapter_contract_ready", False),
            "workbench_read_only": adapter_summary.get("read_only", False),
            "platform_write_api_allowed": safety.get("platform_write_api_allowed", True),
            "secret_read_allowed": adapter_summary.get("secret_read_allowed", True),
            "business_code_write_allowed": adapter_summary.get("business_code_write_allowed", True),
            "acceptance_passed": gate_summary.get("controlled_external_interaction_gate_ready") is True
            and adapter_summary.get("workbench_adapter_contract_ready") is True
            and gate_summary.get("automatic_external_execution_allowed") is False
            and adapter_summary.get("read_only") is True,
        }

    @staticmethod
    def _blocked_risks(
        adapter_contract: dict[str, Any],
        gate: dict[str, Any],
        drift: dict[str, Any],
        feedback_evidence: dict[str, Any],
    ) -> list[dict[str, Any]]:
        adapter_safety = adapter_contract.get("workbenchAdapterSafetyReview", {})
        gate_safety = gate.get("controlledExternalInteractionSafetyReview", {})
        drift_summary = drift.get("externalDriftSummary", {})
        risks = [
            ("WB-RISK-001", "business_code_write", adapter_safety.get("business_code_write_allowed", True) is False, "Workbench cannot directly modify AGOS business code."),
            ("WB-RISK-002", "secret_read", adapter_safety.get("secret_read_allowed", True) is False, "Workbench cannot read secrets, tokens, .env, or credential payloads."),
            ("WB-RISK-003", "external_action_start", adapter_safety.get("external_action_start_allowed", True) is False, "Workbench cannot start external platform actions."),
            ("WB-RISK-004", "platform_write_api", gate_safety.get("platform_write_api_allowed", True) is False, "Platform write APIs remain disabled."),
            ("WB-RISK-005", "automatic_post_reply_login", all(gate_safety.get(key, True) is False for key in ["automatic_posting_allowed", "automatic_reply_allowed", "automatic_login_allowed"]), "Automatic posting, replying, and login remain disabled."),
            ("WB-RISK-006", "drift_auto_strategy_change", drift_summary.get("external_execution_change_allowed", True) is False, "Drift only creates recommendations; it cannot change external execution strategy."),
            ("WB-RISK-007", "feedback_without_evidence", feedback_evidence.get("missing_evidence_blocks_learning", False) is True or feedback_evidence.get("evidence_ledger_ready", False) is True, "Missing evidence is blocked or ledger-bound before feedback learning."),
        ]
        return [
            {
                "risk_id": risk_id,
                "risk": risk,
                "status": "blocked" if blocked else "needs_review",
                "blocked": blocked,
                "reason": reason,
                "workbench_action_allowed": False,
            }
            for risk_id, risk, blocked, reason in risks
        ]

    @staticmethod
    def _capability_score(
        replay_result: dict[str, Any],
        feedback_evidence: dict[str, Any],
        drift_result: dict[str, Any],
        gate_status: dict[str, Any],
        blocked_risks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        dimensions = {
            "replay_result": 20 if replay_result["acceptance_passed"] else 0,
            "feedback_evidence": 20 if feedback_evidence["acceptance_passed"] else 0,
            "drift_result": 20 if drift_result["acceptance_passed"] else 0,
            "gate_status": 20 if gate_status["acceptance_passed"] else 0,
            "blocked_risks": 20 if all(item["blocked"] for item in blocked_risks) else 0,
        }
        total = sum(dimensions.values())
        return {
            "score": total,
            "max_score": 100,
            "grade": "pass" if total >= 80 else "needs_review",
            "dimensions": dimensions,
            "acceptance_ready": total >= 80,
        }

    @staticmethod
    def _summary(
        capability_score: dict[str, Any],
        replay_result: dict[str, Any],
        feedback_evidence: dict[str, Any],
        drift_result: dict[str, Any],
        gate_status: dict[str, Any],
        blocked_risks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "training_acceptance_export_ready": True,
            "capability_score": capability_score["score"],
            "capability_grade": capability_score["grade"],
            "acceptance_ready": capability_score["acceptance_ready"],
            "replay_acceptance_passed": replay_result["acceptance_passed"],
            "feedback_evidence_passed": feedback_evidence["acceptance_passed"],
            "drift_acceptance_passed": drift_result["acceptance_passed"],
            "gate_acceptance_passed": gate_status["acceptance_passed"],
            "blocked_risk_count": len([item for item in blocked_risks if item["blocked"]]),
            "needs_review_risk_count": len([item for item in blocked_risks if not item["blocked"]]),
            "workbench_may_ingest": capability_score["acceptance_ready"],
            "workbench_may_execute": False,
            "next_recommendation": "Workbench can ingest this training acceptance package as read-only evidence; execution remains AGOS/human-gated.",
        }


if __name__ == "__main__":
    result = AGOSTrainingAcceptanceExport().export()
    print(json.dumps({"status": result["status"], "summary": result["trainingAcceptanceSummary"]}, indent=2))
