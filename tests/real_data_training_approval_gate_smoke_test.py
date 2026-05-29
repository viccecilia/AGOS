from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.real_data_training_approval_gate import RealDataTrainingApprovalGate
from services.sample_ingestion_privacy_filter import SampleIngestionPrivacyFilter
from services.social_signal_normalization import SocialSignalNormalization
from services.training_dataset_candidate_builder import TrainingDatasetCandidateBuilder


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sample_dir = Path(tmp) / "real_data_samples"
        training_dir = Path(tmp) / "training_candidates"
        SampleIngestionPrivacyFilter(sample_dir).build()
        SocialSignalNormalization(output_dir=sample_dir, lineage_path=sample_dir / "SAMPLE_LINEAGE_MANIFEST.json").build()
        TrainingDatasetCandidateBuilder(
            input_path=sample_dir / "NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json",
            output_dir=training_dir,
        ).build()
        result = RealDataTrainingApprovalGate(training_dir=training_dir, sample_dir=sample_dir).run()

        checklist = result["realDataTrainingApprovalChecklist"]
        assert checklist["checklist_id"] == "REAL_DATA_TRAINING_APPROVAL_CHECKLIST"
        assert len(checklist["checks"]) == 8
        assert checklist["candidate_record_count"] >= 1
        assert checklist["minimum_candidates_for_review"] == 5
        assert checklist["training_allowed"] is False
        assert checklist["provider_execution_allowed"] is False
        assert checklist["model_promotion_allowed"] is False
        assert any(item["check_id"] == "controlled_training_approval_decision_inputs" for item in checklist["checks"])

        privacy = result["datasetPrivacyValidationReport"]
        assert privacy["report_id"] == "DATASET_PRIVACY_VALIDATION_REPORT"
        assert privacy["privacy_filter_report_present"] is True
        assert privacy["privacy_filter_passed"] is True
        assert privacy["sensitive_pii_present"] is False
        assert privacy["private_messages_present"] is False
        assert privacy["raw_content_stored"] is False
        assert privacy["sensitive_pii_training_allowed"] is False
        assert privacy["excluded_private_message_count"] >= 1
        assert privacy["unsafe_signals_blocked_from_training"] is True
        assert privacy["training_allowed"] is False

        replay = result["datasetReplayValidationReport"]
        assert replay["report_id"] == "DATASET_REPLAY_VALIDATION_REPORT"
        assert replay["replay_manifest_present"] is True
        assert replay["replay_manifest_valid"] is True
        assert replay["source_lineage_count"] == replay["candidate_record_count"]
        assert replay["missing_lineage_candidates"] == []
        assert replay["non_replayable_candidates"] == []
        assert replay["non_auditable_candidates"] == []
        assert replay["training_allowed"] is False
        assert replay["provider_execution_allowed"] is False

        decision = result["realDataTrainingGateDecision"]
        assert decision["decision_id"] == "REAL_DATA_TRAINING_GATE_DECISION"
        assert decision["gate_decision"] == "keep_collecting"
        assert decision["controlled_training_pilot_review_allowed"] is False
        assert decision["automatic_training_allowed"] is False
        assert decision["provider_execution_allowed"] is False
        assert decision["model_promotion_allowed"] is False
        assert decision["agos_core_overwrite_allowed"] is False
        assert decision["human_approval_required"] is True
        assert decision["dataset_too_small"] is True
        assert "dataset_too_small" in decision["collection_blockers"]
        assert "automatic training" in decision["blocked_actions"]
        assert "provider execution" in decision["blocked_actions"]

        evidence = result["realDataTrainingApprovalEvidence"]
        assert evidence["evidence_id"] == "REAL_DATA_TRAINING_APPROVAL_EVIDENCE"
        assert evidence["schema_defined"] is True
        assert evidence["checklist_generated"] is True
        assert evidence["privacy_validation_generated"] is True
        assert evidence["replay_validation_generated"] is True
        assert evidence["gate_decision_generated"] is True
        assert evidence["lineage_complete"] is True
        assert evidence["privacy_filter_passed"] is True
        assert evidence["sensitive_pii_present"] is False
        assert evidence["private_messages_present"] is False
        assert evidence["controlled_training_pilot_review_allowed"] is False
        assert evidence["human_approval_required"] is True
        assert evidence["training_started"] is False
        assert evidence["provider_execution_started"] is False
        assert evidence["model_promoted"] is False
        assert evidence["agos_core_overwritten"] is False

        for output_name in [
            "REAL_DATA_TRAINING_APPROVAL_CHECKLIST.json",
            "DATASET_PRIVACY_VALIDATION_REPORT.json",
            "DATASET_REPLAY_VALIDATION_REPORT.json",
            "REAL_DATA_TRAINING_GATE_DECISION.json",
            "REAL_DATA_TRAINING_APPROVAL_EVIDENCE.json",
        ]:
            path = training_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("real_data_training_approval_gate_smoke_test passed")


if __name__ == "__main__":
    main()
