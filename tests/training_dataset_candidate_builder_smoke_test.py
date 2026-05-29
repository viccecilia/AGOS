from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.sample_ingestion_privacy_filter import SampleIngestionPrivacyFilter
from services.social_signal_normalization import SocialSignalNormalization
from services.training_dataset_candidate_builder import TrainingDatasetCandidateBuilder


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_samples"
        candidate_dir = Path(tmp) / "training_candidates"
        SampleIngestionPrivacyFilter(output_dir).build()
        SocialSignalNormalization(output_dir=output_dir, lineage_path=output_dir / "SAMPLE_LINEAGE_MANIFEST.json").build()
        result = TrainingDatasetCandidateBuilder(
            input_path=output_dir / "NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json",
            output_dir=candidate_dir,
        ).build()

        policy = result["trainingDatasetCandidatePolicy"]
        assert policy["policy_id"] == "TRAINING_DATASET_CANDIDATE_POLICY"
        for dimension in [
            "language",
            "region",
            "platform",
            "content_type",
            "pain_category",
            "use_case_category",
            "mobility_relevance",
            "confidence_tier",
        ]:
            assert dimension in policy["grouping_dimensions"]
        assert "exact duplicate" in policy["duplication_logic"]
        assert "semantic duplicate" in policy["duplication_logic"]
        assert "same question different language" in policy["duplication_logic"]
        assert "same pain different platform" in policy["duplication_logic"]
        assert "repeated demand cluster" in policy["duplication_logic"]
        assert "novelty score" in policy["duplication_logic"]
        assert policy["safety_boundary"]["dataset_candidate_only"] is True
        assert policy["safety_boundary"]["training_allowed"] is False
        assert policy["safety_boundary"]["provider_execution_allowed"] is False
        assert policy["safety_boundary"]["memory_writeback_allowed"] is False
        assert policy["safety_boundary"]["sensitive_pii_allowed"] is False
        assert policy["safety_boundary"]["private_messages_allowed"] is False

        manifest = result["trainingDatasetCandidateManifest"]
        assert manifest["manifest_id"] == "TRAINING_DATASET_CANDIDATE_MANIFEST"
        assert manifest["dataset_candidate_only"] is True
        assert manifest["training_allowed"] is False
        assert manifest["provider_execution_allowed"] is False
        assert manifest["memory_writeback_allowed"] is False
        assert manifest["replayable"] is True
        assert manifest["auditable"] is True
        assert manifest["source_record_count"] >= 4
        assert manifest["candidate_record_count"] >= 1
        assert manifest["excluded_record_count"] >= 1
        assert manifest["candidate_record_count"] + manifest["excluded_record_count"] == manifest["source_record_count"]
        for dimension in policy["grouping_dimensions"]:
            assert dimension in manifest["groups"]

        for record in manifest["candidate_records"]:
            assert record["candidate_data_only"] is True
            assert record["human_review_required"] is True
            assert record["training_allowed"] is False
            assert record["provider_execution_allowed"] is False
            assert record["memory_writeback_allowed"] is False
            assert record["promotion_allowed"] is False
            assert record["writeback_allowed"] is False
            assert record["contact_user_allowed"] is False
            assert record["replayable"] is True
            assert record["auditable"] is True
            assert record["lineage"]["sample_data_only"] is True
            assert record["lineage"]["lineage_complete"] is True
            assert record["confidence_tier"] in {"high_confidence", "medium_confidence", "low_confidence"}
            assert record["mobility_relevance"] in {
                "high_mobility_relevance",
                "medium_mobility_relevance",
                "low_mobility_relevance",
            }

        excluded_reasons = [reason for record in manifest["excluded_records"] for reason in record["excluded_data_reason"]]
        assert any("unsafe personal data" in reason for reason in excluded_reasons)
        assert all(record["training_allowed"] is False for record in manifest["excluded_records"])

        duplication = result["duplicationAndNoveltyReport"]
        assert duplication["report_id"] == "DUPLICATION_AND_NOVELTY_REPORT"
        assert duplication["candidate_count"] == manifest["candidate_record_count"]
        assert "exact_duplicates" in duplication
        assert "semantic_duplicates" in duplication
        assert "same_question_different_language" in duplication
        assert "same_pain_different_platform" in duplication
        assert "repeated_demand_clusters" in duplication
        assert len(duplication["novelty_scores"]) == manifest["candidate_record_count"]
        assert 0 <= duplication["repeated_content_ratio"] <= 1
        assert 0 <= duplication["new_demand_ratio"] <= 1
        assert duplication["training_allowed"] is False

        stage = manifest["stage_transition_signal"]
        for required in [
            "repeated_content_ratio",
            "new_demand_ratio",
            "high_value_pain_cluster_count",
            "unresolved_category_count",
            "confidence_threshold_met",
            "sample_coverage_threshold_met",
            "training_ready",
            "stage_transition_allowed",
        ]:
            assert required in stage
        assert stage["training_ready"] is False
        assert stage["stage_transition_allowed"] is False

        replay = result["datasetReplayManifest"]
        assert replay["manifest_id"] == "DATASET_REPLAY_MANIFEST"
        assert replay["filter_version"]
        assert replay["normalization_version"]
        assert replay["dataset_version"]
        assert replay["training_allowed"] is False
        assert replay["provider_execution_allowed"] is False
        assert replay["memory_writeback_allowed"] is False
        assert replay["replayable"] is True
        assert replay["auditable"] is True
        assert len(replay["source_lineage"]) == manifest["candidate_record_count"]
        assert len(replay["excluded_data_reasons"]) == manifest["excluded_record_count"]
        assert any("Do not start training" in item for item in replay["replay_instructions"])

        evidence = result["trainingDatasetCandidateEvidence"]
        assert evidence["schema_defined"] is True
        assert evidence["policy_defined"] is True
        assert evidence["manifest_generated"] is True
        assert evidence["duplication_report_generated"] is True
        assert evidence["replay_manifest_generated"] is True
        assert evidence["all_candidate_records_have_lineage"] is True
        assert evidence["all_candidate_records_replayable"] is True
        assert evidence["all_candidate_records_auditable"] is True
        assert evidence["sensitive_pii_included"] is False
        assert evidence["private_messages_included"] is False
        assert evidence["training_started"] is False
        assert evidence["provider_execution_started"] is False
        assert evidence["memory_writeback_started"] is False
        assert evidence["dataset_candidate_only"] is True
        assert evidence["training_allowed"] is False

        for output_name in [
            "TRAINING_DATASET_CANDIDATE_POLICY.json",
            "TRAINING_DATASET_CANDIDATE_MANIFEST.json",
            "DUPLICATION_AND_NOVELTY_REPORT.json",
            "DATASET_REPLAY_MANIFEST.json",
            "TRAINING_DATASET_CANDIDATE_EVIDENCE.json",
        ]:
            path = candidate_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("training_dataset_candidate_builder_smoke_test passed")


if __name__ == "__main__":
    main()
