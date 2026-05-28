from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agos_training_acceptance_export import AGOSTrainingAcceptanceExport


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "agos_training_acceptance_export"
        package = AGOSTrainingAcceptanceExport(root).export()

        assert package["report_id"] == "AGOS_TRAINING_ACCEPTANCE_EXPORT"
        assert package["round_id"] == "ROUND-WB-AGOS-002"
        assert package["status"] == "training_acceptance_export_ready"
        assert package["export_policy"]["read_only"] is True
        assert package["export_policy"]["contains_secret_values"] is False
        assert package["export_policy"]["business_code_write_allowed"] is False
        assert package["export_policy"]["external_action_start_allowed"] is False
        assert package["export_policy"]["platform_write_api_allowed"] is False

        capability = package["capabilityScore"]
        assert capability["score"] >= 80
        assert capability["max_score"] == 100
        assert capability["acceptance_ready"] is True
        assert {"replay_result", "feedback_evidence", "drift_result", "gate_status", "blocked_risks"}.issubset(capability["dimensions"])

        replay = package["replayResult"]
        assert replay["replay_items"] > 0
        assert replay["replayed_memory_items"] > 0
        assert replay["acceptance_passed"] is True

        feedback = package["feedbackEvidence"]
        assert feedback["feedback_event_count"] > 0
        assert feedback["best_pattern_count"] > 0
        assert feedback["failed_pattern_count"] > 0
        assert feedback["evidence_ledger_ready"] is True

        drift = package["driftResult"]
        assert drift["drift_status"] == "external_drift_monitor_ready"
        assert drift["recommendation_only"] is True
        assert drift["external_execution_change_allowed"] is False
        assert drift["acceptance_passed"] is True

        gate = package["gateStatus"]
        assert gate["workbench_adapter_ready"] is True
        assert gate["workbench_read_only"] is True
        assert gate["automatic_external_execution_allowed"] is False
        assert gate["secret_read_allowed"] is False
        assert gate["business_code_write_allowed"] is False
        assert gate["acceptance_passed"] is True

        risks = package["blockedRisks"]
        assert len(risks) >= 6
        assert all(item["workbench_action_allowed"] is False for item in risks)
        assert {item["risk"] for item in risks}.issuperset({"secret_read", "platform_write_api", "external_action_start"})

        summary = package["trainingAcceptanceSummary"]
        assert summary["training_acceptance_export_ready"] is True
        assert summary["workbench_may_ingest"] is True
        assert summary["workbench_may_execute"] is False

        for output_name in [
            "AGOS_TRAINING_ACCEPTANCE_EXPORT.json",
            "capability_score.json",
            "replay_result.json",
            "feedback_evidence.json",
            "drift_result.json",
            "gate_status.json",
            "blocked_risks.json",
            "training_acceptance_summary.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("agos_training_acceptance_export_smoke_test passed")


if __name__ == "__main__":
    main()
