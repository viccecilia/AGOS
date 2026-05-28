from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agos_workbench_adapter_contract import AGOSWorkbenchAdapterContract


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "workbench_adapter_contract"
        contract = AGOSWorkbenchAdapterContract(root, PROJECT_ROOT).build()

        assert contract["report_id"] == "AGOS_WORKBENCH_ADAPTER_CONTRACT"
        assert contract["round_id"] == "ROUND-WB-AGOS-001"
        assert contract["status"] == "readonly_contract_ready"
        assert contract["access_policy"]["read_only"] is True
        assert contract["access_policy"]["business_code_write_allowed"] is False
        assert contract["access_policy"]["secret_read_allowed"] is False
        assert contract["access_policy"]["external_action_start_allowed"] is False
        assert contract["access_policy"]["platform_write_api_allowed"] is False

        allowed_sources = set(contract["allowed_read_sources"])
        assert "runtime/task_results/*" in allowed_sources
        assert "runtime/*/*REPORT.json" in allowed_sources
        assert "docs/project_control_center.html" in allowed_sources
        assert "services/runtime_ui_bridge.py output state" in allowed_sources

        forbidden = " ".join(contract["forbidden_operations"]).lower()
        assert "modify agos business code" in forbidden
        assert "secrets" in forbidden
        assert "external platform actions" in forbidden

        artifacts = contract["workbenchReadableArtifacts"]
        assert artifacts["taskResults"]
        assert artifacts["runtimeReports"]
        assert artifacts["controlCenter"]["exists"] is True
        assert artifacts["runtimeUiBridgeSource"]["exists"] is True
        assert all(item["read_allowed"] is True for item in artifacts["taskResults"])
        assert all(item["write_allowed"] is False for item in artifacts["taskResults"])

        summary = contract["workbenchAdapterSummary"]
        assert summary["workbench_adapter_contract_ready"] is True
        assert summary["task_result_round_count"] >= 1
        assert summary["runtime_report_count"] >= 1
        assert summary["gate_count"] >= 1
        assert summary["business_code_write_allowed"] is False
        assert summary["secret_read_allowed"] is False
        assert summary["external_action_start_allowed"] is False

        safety = contract["workbenchAdapterSafetyReview"]
        assert safety["safety_boundary_passed"] is True
        assert safety["business_code_write_allowed"] is False
        assert safety["secret_read_allowed"] is False
        assert ".env" in safety["forbidden_path_patterns"]

        for output_name in [
            "AGOS_WORKBENCH_ADAPTER_CONTRACT.json",
            "workbench_readable_artifacts.json",
            "workbench_gate_index.json",
            "workbench_adapter_safety_review.json",
            "workbench_adapter_summary.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("agos_workbench_adapter_contract_smoke_test passed")


if __name__ == "__main__":
    main()
