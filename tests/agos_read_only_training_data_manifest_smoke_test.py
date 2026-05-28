from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.agos_read_only_training_data_manifest import AGOSReadOnlyTrainingDataManifest


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "agos_read_only_training_data_manifest"
        manifest = AGOSReadOnlyTrainingDataManifest(root, PROJECT_ROOT).build()

        assert manifest["report_id"] == "AGOS_READ_ONLY_TRAINING_DATA_MANIFEST"
        assert manifest["round_id"] == "ROUND-WB-AGOS-003"
        assert manifest["status"] == "read_only_training_data_manifest_ready"
        principles = manifest["principles"]
        assert principles["sample_first"] is True
        assert principles["read_only"] is True
        assert principles["audit_first"] is True
        assert principles["human_gated"] is True
        assert principles["contains_credentials"] is False

        policy = manifest["trainingDataAccessPolicy"]
        assert policy["workbench_read_allowed"] is True
        assert policy["workbench_write_allowed"] is False
        assert policy["workbench_execute_allowed"] is False
        assert policy["secret_read_allowed"] is False
        assert policy["credential_value_export_allowed"] is False
        assert policy["platform_write_api_allowed"] is False

        datasets = manifest["trainingDatasetManifest"]
        assert len(datasets) >= 8
        assert all(item["read_only"] is True for item in datasets)
        assert all(item["audit_first"] is True for item in datasets)
        assert all(item["human_gated"] is True for item in datasets)
        assert all(item["write_allowed"] is False for item in datasets)
        assert all(item["workbench_execute_allowed"] is False for item in datasets)
        assert all(item["contains_credentials"] is False for item in datasets)
        assert any(item["data_origin"] == "local_sample" for item in datasets)
        assert any(item["path"] == "runtime/task_results" for item in datasets)
        assert not any("api_credentials" in item["path"] for item in datasets)
        assert not any("platform_credentials" in item["path"] for item in datasets)

        audit = manifest["trainingDataAuditReview"]
        assert audit["audit_first"] is True
        assert audit["human_gated"] is True
        assert audit["credential_scan_passed"] is True
        assert audit["external_execution_allowed"] is False
        assert audit["write_api_allowed"] is False

        summary = manifest["trainingDataManifestSummary"]
        assert summary["training_data_manifest_ready"] is True
        assert summary["sample_first"] is True
        assert summary["read_only"] is True
        assert summary["audit_first"] is True
        assert summary["human_gated"] is True
        assert summary["contains_credentials"] is False
        assert summary["workbench_may_read"] is True
        assert summary["workbench_may_write"] is False
        assert summary["workbench_may_execute"] is False

        for output_name in [
            "AGOS_READ_ONLY_TRAINING_DATA_MANIFEST.json",
            "training_dataset_manifest.json",
            "training_data_audit_review.json",
            "training_data_access_policy.json",
            "training_data_manifest_summary.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("agos_read_only_training_data_manifest_smoke_test passed")


if __name__ == "__main__":
    main()
