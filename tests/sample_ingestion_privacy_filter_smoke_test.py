from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.sample_ingestion_privacy_filter import SampleIngestionPrivacyFilter


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_samples"
        report = SampleIngestionPrivacyFilter(output_dir).build()

        ingestion_policy = report["sampleIngestionPolicy"]
        limits = ingestion_policy["sample_limits"]
        assert ingestion_policy["policy_id"] == "SAMPLE_INGESTION_POLICY"
        assert limits["small_batch_only"] is True
        assert limits["total_sample_cap"] == 8
        assert limits["per_platform_cap"] == 3
        assert limits["per_language_cap"] == 3
        assert limits["per_query_cap"] == 2
        assert limits["continuous_ingestion_allowed"] is False
        assert ingestion_policy["storage_policy"]["store_raw_content"] is False
        assert ingestion_policy["storage_policy"]["training_allowed"] is False
        assert ingestion_policy["storage_policy"]["automatic_promotion_allowed"] is False

        privacy_policy = report["privacyFilterPolicy"]
        for required_filter in [
            "remove private identifiers",
            "remove contact information",
            "remove precise personal location",
            "remove sensitive personal information",
            "flag minors' data",
            "exclude private messages",
        ]:
            assert required_filter in privacy_policy["filters"]
        assert privacy_policy["exclusion_policy"]["private_messages_excluded"] is True
        assert privacy_policy["exclusion_policy"]["sensitive_pii_training_allowed"] is False

        manifest = report["sampleLineageManifest"]
        assert manifest["manifest_id"] == "SAMPLE_LINEAGE_MANIFEST"
        assert manifest["raw_content_stored"] is False
        assert manifest["all_records_training_blocked"] is True
        assert 1 <= manifest["record_count"] <= limits["total_sample_cap"]
        for field in [
            "platform_id",
            "source_type",
            "query_id",
            "collection_time",
            "language",
            "region",
            "content_type",
            "engagement_metrics",
            "source_reference",
        ]:
            assert field in manifest["lineage_fields"]

        allowed_classes = {
            "help-seeking",
            "confusion/problem",
            "solution",
            "recommendation",
            "transport issue",
            "purchase/food/visit interest",
            "uncategorized",
        }
        for record in manifest["records"]:
            assert record["content_type"] in allowed_classes
            assert record["lineage_complete"] is True
            assert record["training_allowed"] is False
            assert record["automatic_promotion_allowed"] is False
            assert "traveler@example.com" not in record["filtered_excerpt"]
            assert "+1-555-0199" not in record["filtered_excerpt"]
            assert "3-2-1 Sample Street" not in record["filtered_excerpt"]
            assert "passport" not in record["filtered_excerpt"].lower()
            assert record["source_type"] != "private_message"

        privacy_report = report["privacyFilterReport"]
        assert privacy_report["filtered_record_count"] == manifest["record_count"]
        assert privacy_report["excluded_private_message_count"] >= 1
        assert privacy_report["minors_data_flagged_count"] >= 1
        assert privacy_report["redaction_total"] >= 3
        assert "contact_information" in privacy_report["redaction_types"]
        assert "precise_personal_location" in privacy_report["redaction_types"]
        assert privacy_report["raw_content_stored"] is False
        assert privacy_report["sensitive_pii_training_allowed"] is False
        assert privacy_report["large_scale_ingestion_allowed"] is False
        assert privacy_report["automatic_promotion_allowed"] is False

        evidence = report["sampleIngestionEvidence"]
        assert evidence["small_batch_only"] is True
        assert evidence["continuous_ingestion_allowed"] is False
        assert evidence["private_messages_excluded"] is True
        assert evidence["contact_information_redacted"] is True
        assert evidence["precise_personal_location_redacted"] is True
        assert evidence["minors_data_flagged"] is True
        assert evidence["lineage_manifest_complete"] is True
        assert evidence["training_allowed"] is False
        assert evidence["automatic_promotion_allowed"] is False
        assert evidence["large_scale_ingestion_allowed"] is False

        for output_name in [
            "SAMPLE_INGESTION_POLICY.json",
            "PRIVACY_FILTER_POLICY.json",
            "SAMPLE_LINEAGE_MANIFEST.json",
            "PRIVACY_FILTER_REPORT.json",
            "SAMPLE_INGESTION_EVIDENCE.json",
        ]:
            path = output_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("sample_ingestion_privacy_filter_smoke_test passed")


if __name__ == "__main__":
    main()
