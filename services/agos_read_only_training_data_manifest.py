"""Read-only training data manifest for Workbench."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.agos_training_acceptance_export import AGOSTrainingAcceptanceExport
from services.agos_workbench_adapter_contract import AGOSWorkbenchAdapterContract
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/agos_read_only_training_data_manifest")
FORBIDDEN_PATH_PARTS = {
    ".env",
    "api_credentials",
    "platform_credentials",
    "credentials",
    "secrets",
    "token",
    "oauth",
    "refresh",
}


class AGOSReadOnlyTrainingDataManifest:
    """Build a Workbench-safe manifest of AGOS training data artifacts."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR, project_root: str | Path = ".") -> None:
        self.output_dir = Path(output_dir)
        self.project_root = Path(project_root)
        self.manifest_path = self.output_dir / "AGOS_READ_ONLY_TRAINING_DATA_MANIFEST.json"
        self.datasets_path = self.output_dir / "training_dataset_manifest.json"
        self.audit_path = self.output_dir / "training_data_audit_review.json"
        self.policy_path = self.output_dir / "training_data_access_policy.json"
        self.summary_path = self.output_dir / "training_data_manifest_summary.json"

    def build(
        self,
        *,
        adapter_contract: dict[str, Any] | None = None,
        training_acceptance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        adapter_contract = adapter_contract or AGOSWorkbenchAdapterContract().state()
        training_acceptance = training_acceptance or AGOSTrainingAcceptanceExport().state()
        candidates = self._candidate_paths()
        datasets = [self._dataset_record(index, path) for index, path in enumerate(candidates, start=1)]
        datasets = [item for item in datasets if item["read_allowed"] and not item["contains_credentials"]]
        audit = self._audit_review(datasets)
        policy = self._access_policy(adapter_contract, training_acceptance)
        summary = self._summary(datasets, audit, policy)
        manifest = {
            "report_id": "AGOS_READ_ONLY_TRAINING_DATA_MANIFEST",
            "round_id": "ROUND-WB-AGOS-003",
            "created_at": utc_now_iso(),
            "status": "read_only_training_data_manifest_ready",
            "phase": "WORKBENCH_AGOS_ADAPTER",
            "principles": {
                "sample_first": True,
                "read_only": True,
                "audit_first": True,
                "human_gated": True,
                "contains_credentials": False,
            },
            "trainingDataAccessPolicy": policy,
            "trainingDatasetManifest": datasets,
            "trainingDataAuditReview": audit,
            "trainingDataManifestSummary": summary,
            "safetyBoundary": "Training Data Manifest exposes only read-only, audit-first, human-gated training artifact metadata. It excludes credentials, tokens, secrets, and external action execution.",
        }
        self.persist(manifest)
        return manifest

    def state(self) -> dict[str, Any]:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, manifest: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.datasets_path.write_text(json.dumps(manifest["trainingDatasetManifest"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.audit_path.write_text(json.dumps(manifest["trainingDataAuditReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.policy_path.write_text(json.dumps(manifest["trainingDataAccessPolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(manifest["trainingDataManifestSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _candidate_paths(self) -> list[Path]:
        path_texts = [
            "runtime/samples",
            "runtime/seasonal_demand_calendar",
            "runtime/seasonal_trend_import_trial",
            "runtime/batch_runtime",
            "runtime/batch_clusters",
            "runtime/batch_reviews",
            "runtime/pattern_memory",
            "runtime/replay_training",
            "runtime/synthetic_training",
            "runtime/promotion_feedback_learning",
            "runtime/external_evidence_ledger",
            "runtime/external_drift_monitor",
            "runtime/controlled_external_interaction_gate",
            "runtime/agos_training_acceptance_export",
            "runtime/workbench_adapter_contract",
            "runtime/task_results",
        ]
        return [self.project_root / item for item in path_texts]

    def _dataset_record(self, index: int, path: Path) -> dict[str, Any]:
        rel_path = self._rel(path)
        files = [item for item in path.rglob("*") if item.is_file()] if path.exists() else []
        json_files = [item for item in files if item.suffix.lower() == ".json"]
        md_files = [item for item in files if item.suffix.lower() == ".md"]
        forbidden_files = [item for item in files if self._is_forbidden_path(item)]
        contains_credentials = self._is_forbidden_path(path)
        data_origin = self._origin_for_path(rel_path)
        return {
            "dataset_id": f"AGOS-TRAINING-DATA-{index:03d}",
            "path": rel_path,
            "exists": path.exists(),
            "data_origin": data_origin,
            "sample_first": data_origin in {"sample", "local_sample", "manual_sample"} or "sample" in rel_path.lower(),
            "read_only": True,
            "audit_first": True,
            "human_gated": True,
            "contains_credentials": contains_credentials,
            "read_allowed": path.exists() and not contains_credentials,
            "write_allowed": False,
            "workbench_execute_allowed": False,
            "file_count": len(files),
            "json_file_count": len(json_files),
            "markdown_file_count": len(md_files),
            "excluded_sensitive_file_count": len(forbidden_files),
            "sample_files": [self._rel(item) for item in json_files if not self._is_forbidden_path(item)][:5],
            "audit_note": self._audit_note(rel_path, data_origin, contains_credentials, len(forbidden_files)),
        }

    @staticmethod
    def _origin_for_path(path_text: str) -> str:
        lowered = path_text.lower()
        if "sample" in lowered or "synthetic" in lowered:
            return "local_sample"
        if "external_evidence" in lowered or "manual" in lowered:
            return "manual_evidence"
        if "task_results" in lowered:
            return "round_artifact"
        if "replay" in lowered or "pattern" in lowered or "feedback" in lowered:
            return "derived_training_artifact"
        return "local_runtime_artifact"

    @staticmethod
    def _audit_note(path_text: str, data_origin: str, contains_credentials: bool, excluded_sensitive_file_count: int = 0) -> str:
        if contains_credentials:
            return "Blocked from manifest because path may contain credentials or secrets."
        if excluded_sensitive_file_count:
            return f"Workbench may read non-sensitive {data_origin} artifacts; {excluded_sensitive_file_count} credential-looking child files are excluded from samples."
        return f"Workbench may read metadata and artifact contents as {data_origin}; any use remains audit-first and human-gated."

    @staticmethod
    def _access_policy(adapter_contract: dict[str, Any], training_acceptance: dict[str, Any]) -> dict[str, Any]:
        adapter_policy = adapter_contract.get("access_policy", {})
        export_policy = training_acceptance.get("export_policy", {})
        return {
            "sample_first": True,
            "read_only": True,
            "audit_first": True,
            "human_gated": True,
            "contains_credentials": False,
            "workbench_read_allowed": True,
            "workbench_write_allowed": False,
            "workbench_execute_allowed": False,
            "business_code_write_allowed": False,
            "secret_read_allowed": False,
            "credential_value_export_allowed": False,
            "platform_write_api_allowed": False,
            "adapter_contract_read_only": adapter_policy.get("read_only", False),
            "training_acceptance_read_only": export_policy.get("read_only", False),
            "training_acceptance_ready": training_acceptance.get("trainingAcceptanceSummary", {}).get("acceptance_ready", False),
            "forbidden_path_patterns": sorted(FORBIDDEN_PATH_PARTS),
        }

    @staticmethod
    def _audit_review(datasets: list[dict[str, Any]]) -> dict[str, Any]:
        blocked = [item for item in datasets if item["contains_credentials"] or not item["read_allowed"]]
        return {
            "review_id": "TRAINING_DATA_MANIFEST_AUDIT_REVIEW",
            "audit_first": True,
            "human_gated": True,
            "credential_scan_passed": len([item for item in datasets if item["contains_credentials"]]) == 0,
            "blocked_dataset_count": len(blocked),
            "readable_dataset_count": len([item for item in datasets if item["read_allowed"]]),
            "external_execution_allowed": False,
            "write_api_allowed": False,
            "blocked_datasets": blocked,
        }

    @staticmethod
    def _summary(datasets: list[dict[str, Any]], audit: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        return {
            "training_data_manifest_ready": True,
            "dataset_count": len(datasets),
            "readable_dataset_count": audit["readable_dataset_count"],
            "blocked_dataset_count": audit["blocked_dataset_count"],
            "sample_first": policy["sample_first"],
            "read_only": policy["read_only"],
            "audit_first": policy["audit_first"],
            "human_gated": policy["human_gated"],
            "contains_credentials": False,
            "credential_scan_passed": audit["credential_scan_passed"],
            "workbench_may_read": True,
            "workbench_may_write": False,
            "workbench_may_execute": False,
            "next_recommendation": "Workbench can import this manifest as a read-only training data index before any training or orchestration step.",
        }

    @staticmethod
    def _is_forbidden_path(path: Path) -> bool:
        parts = {part.lower() for part in path.parts}
        text = path.as_posix().lower()
        return bool(parts.intersection(FORBIDDEN_PATH_PARTS)) or any(part in text for part in ["/.env", "secret", "credential", "token", "oauth", "refresh"])

    def _rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.project_root).as_posix()
        except ValueError:
            return path.as_posix()


if __name__ == "__main__":
    result = AGOSReadOnlyTrainingDataManifest().build()
    print(json.dumps({"status": result["status"], "summary": result["trainingDataManifestSummary"]}, indent=2))
