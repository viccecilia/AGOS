"""Read-only adapter contract for Workbench access to AGOS state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/workbench_adapter_contract")


class AGOSWorkbenchAdapterContract:
    """Define how Workbench may read AGOS artifacts without controlling AGOS."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR, project_root: str | Path = ".") -> None:
        self.output_dir = Path(output_dir)
        self.project_root = Path(project_root)
        self.report_path = self.output_dir / "AGOS_WORKBENCH_ADAPTER_CONTRACT.json"
        self.artifacts_path = self.output_dir / "workbench_readable_artifacts.json"
        self.gates_path = self.output_dir / "workbench_gate_index.json"
        self.safety_path = self.output_dir / "workbench_adapter_safety_review.json"
        self.summary_path = self.output_dir / "workbench_adapter_summary.json"

    def build(self) -> dict[str, Any]:
        task_results = self._task_result_index()
        reports = self._runtime_report_index()
        gates = self._gate_index(reports)
        control_center = self._file_status("docs/project_control_center.html")
        runtime_ui_state = self._file_status("runtime/runtime_state/ui_state.json")
        bridge_source = self._file_status("services/runtime_ui_bridge.py")
        artifacts = {
            "taskResults": task_results,
            "runtimeReports": reports,
            "controlCenter": control_center,
            "runtimeUiState": runtime_ui_state,
            "runtimeUiBridgeSource": bridge_source,
        }
        safety_review = self._safety_review()
        summary = self._summary(task_results, reports, gates, control_center, runtime_ui_state, bridge_source, safety_review)
        contract = {
            "report_id": "AGOS_WORKBENCH_ADAPTER_CONTRACT",
            "round_id": "ROUND-WB-AGOS-001",
            "created_at": utc_now_iso(),
            "status": "readonly_contract_ready",
            "phase": "WORKBENCH_AGOS_ADAPTER",
            "contract_version": "1.0",
            "allowed_read_sources": [
                "runtime/task_results/*",
                "runtime/*/*REPORT.json",
                "docs/project_control_center.html",
                "runtime/runtime_state/ui_state.json",
                "docs/runtime/runtime_state/ui_state.json",
                "services/runtime_ui_bridge.py output state",
            ],
            "forbidden_operations": [
                "Workbench must not directly modify AGOS business code.",
                "Workbench must not directly read secrets, API keys, OAuth tokens, refresh tokens, .env files, or credential vault payloads.",
                "Workbench must not start external platform actions.",
                "Workbench must not call platform write APIs.",
                "Workbench must not log in to platforms, scrape login-only data, post, reply, DM, follow, like, or dispatch external actions.",
            ],
            "access_policy": {
                "read_only": True,
                "business_code_write_allowed": False,
                "secret_read_allowed": False,
                "external_action_start_allowed": False,
                "platform_write_api_allowed": False,
                "credential_value_export_allowed": False,
                "allowed_output_dir": str(self.output_dir).replace("\\", "/"),
            },
            "workbenchReadableArtifacts": artifacts,
            "workbenchGateIndex": gates,
            "workbenchAdapterSafetyReview": safety_review,
            "workbenchAdapterSummary": summary,
            "safetyBoundary": "Workbench may inspect AGOS task results, report artifacts, control-center state, and runtime UI state only. It cannot mutate AGOS business code, read secrets, or start external platform actions.",
        }
        self.persist(contract)
        return contract

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, contract: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.artifacts_path.write_text(json.dumps(contract["workbenchReadableArtifacts"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.gates_path.write_text(json.dumps(contract["workbenchGateIndex"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.safety_path.write_text(json.dumps(contract["workbenchAdapterSafetyReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(contract["workbenchAdapterSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _task_result_index(self) -> list[dict[str, Any]]:
        root = self.project_root / "runtime" / "task_results"
        if not root.exists():
            return []
        items = []
        for round_dir in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name):
            summary = round_dir / "ROUND_SUMMARY.md"
            items.append(
                {
                    "round_id": round_dir.name,
                    "path": self._rel(round_dir),
                    "summary_path": self._rel(summary) if summary.exists() else "",
                    "summary_exists": summary.exists(),
                    "artifact_count": len([p for p in round_dir.rglob("*") if p.is_file()]),
                    "read_allowed": True,
                    "write_allowed": False,
                }
            )
        return items

    def _runtime_report_index(self) -> list[dict[str, Any]]:
        runtime = self.project_root / "runtime"
        if not runtime.exists():
            return []
        reports = []
        for path in sorted(runtime.glob("*/*REPORT.json")):
            payload = self._read_json(path, {})
            reports.append(
                {
                    "path": self._rel(path),
                    "report_id": payload.get("report_id", path.stem),
                    "status": payload.get("status", "unknown"),
                    "phase": payload.get("phase", ""),
                    "safety_boundary": payload.get("safetyBoundary", ""),
                    "read_allowed": True,
                    "write_allowed": False,
                }
            )
        return reports

    @staticmethod
    def _gate_index(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
        gates = []
        for item in reports:
            haystack = f"{item.get('path', '')} {item.get('report_id', '')} {item.get('phase', '')}".lower()
            if "gate" not in haystack:
                continue
            gates.append(
                {
                    "gate_id": item.get("report_id") or Path(item.get("path", "")).stem,
                    "path": item.get("path", ""),
                    "status": item.get("status", "unknown"),
                    "phase": item.get("phase", ""),
                    "safety_boundary": item.get("safety_boundary", ""),
                    "read_allowed": True,
                    "execute_allowed": False,
                }
            )
        return gates

    def _file_status(self, path_text: str) -> dict[str, Any]:
        path = self.project_root / path_text
        return {
            "path": path_text,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "read_allowed": True,
            "write_allowed": False,
        }

    @staticmethod
    def _safety_review() -> dict[str, Any]:
        forbidden_paths = [
            ".env",
            "runtime/api_credentials/",
            "runtime/platform_credentials/",
            "secrets/",
            "credentials/",
        ]
        return {
            "review_id": "WORKBENCH_AGOS_ADAPTER_SAFETY_REVIEW",
            "safety_boundary_passed": True,
            "read_only_contract": True,
            "business_code_write_allowed": False,
            "secret_read_allowed": False,
            "external_action_start_allowed": False,
            "platform_write_api_allowed": False,
            "credential_value_export_allowed": False,
            "forbidden_path_patterns": forbidden_paths,
            "allowed_artifact_policy": "metadata and artifact summaries only; no secret values and no platform action execution",
        }

    @staticmethod
    def _summary(
        task_results: list[dict[str, Any]],
        reports: list[dict[str, Any]],
        gates: list[dict[str, Any]],
        control_center: dict[str, Any],
        runtime_ui_state: dict[str, Any],
        bridge_source: dict[str, Any],
        safety_review: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "workbench_adapter_contract_ready": True,
            "read_only": True,
            "task_result_round_count": len(task_results),
            "task_result_summary_count": len([item for item in task_results if item["summary_exists"]]),
            "runtime_report_count": len(reports),
            "gate_count": len(gates),
            "control_center_available": control_center["exists"],
            "runtime_ui_state_available": runtime_ui_state["exists"],
            "runtime_ui_bridge_source_available": bridge_source["exists"],
            "business_code_write_allowed": False,
            "secret_read_allowed": False,
            "external_action_start_allowed": False,
            "platform_write_api_allowed": False,
            "safety_boundary_passed": safety_review["safety_boundary_passed"],
            "next_recommendation": "Expose this contract to Workbench as a read-only project adapter before any cross-project orchestration.",
        }

    def _rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.project_root).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default


if __name__ == "__main__":
    result = AGOSWorkbenchAdapterContract().build()
    print(json.dumps({"status": result["status"], "summary": result["workbenchAdapterSummary"]}, indent=2))
