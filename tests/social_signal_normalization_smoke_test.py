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


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_samples"
        sample_report = SampleIngestionPrivacyFilter(output_dir).build()
        lineage_path = output_dir / "SAMPLE_LINEAGE_MANIFEST.json"
        result = SocialSignalNormalization(output_dir=output_dir, lineage_path=lineage_path).build()

        policy = result["socialSignalNormalizationPolicy"]
        assert policy["policy_id"] == "SOCIAL_SIGNAL_NORMALIZATION_POLICY"
        assert policy["input_contract"]["privacy_filtered_input_required"] is True
        assert policy["input_contract"]["small_sample_only"] is True
        assert policy["safety_boundary"]["training_allowed"] is False
        assert policy["safety_boundary"]["promotion_allowed"] is False
        assert policy["safety_boundary"]["writeback_allowed"] is False
        assert policy["safety_boundary"]["contact_user_allowed"] is False
        assert policy["audit_policy"]["replayable"] is True
        assert policy["audit_policy"]["auditable"] is True
        assert policy["audit_policy"]["human_review_required"] is True

        normalized_sample = result["normalizedSocialSignalSample"]
        assert normalized_sample["sample_id"] == "NORMALIZED_SOCIAL_SIGNAL_SAMPLE"
        assert normalized_sample["sample_data_only"] is True
        assert normalized_sample["source_record_count"] == sample_report["sampleLineageManifest"]["record_count"]
        assert normalized_sample["normalized_record_count"] == sample_report["sampleLineageManifest"]["record_count"]
        assert normalized_sample["normalized_record_count"] >= 4
        assert normalized_sample["training_allowed"] is False
        assert normalized_sample["promotion_allowed"] is False
        assert normalized_sample["writeback_allowed"] is False
        assert normalized_sample["contact_user_allowed"] is False
        assert normalized_sample["replayable"] is True
        assert normalized_sample["auditable"] is True

        engagement_fields = {"likes", "comments", "shares", "saves", "views", "author_thanks", "reply_depth", "reposts"}
        content_fields = {"question_type", "pain_category", "emotion_intensity", "urgency", "language", "region", "platform", "content_format"}
        score_fields = {"evidence_strength", "duplication_score", "engagement_strength", "relevance_score", "mobility_relevance", "risk_score", "confidence_score"}
        noise_flags = {"spam", "ads", "bot_like_content", "off_topic_content", "unsafe_personal_data", "unverifiable_claims"}

        unsafe_seen = False
        usable_or_monitor_seen = False
        for record in normalized_sample["records"]:
            assert engagement_fields.issubset(record["normalized_engagement"])
            assert content_fields.issubset(record)
            assert score_fields.issubset(record["quality_scores"])
            assert noise_flags.issubset(record["noise_filter"])
            assert record["lineage"]["sample_data_only"] is True
            assert record["review_status"] == "needs_human_review"
            assert record["training_allowed"] is False
            assert record["promotion_allowed"] is False
            assert record["writeback_allowed"] is False
            assert record["contact_user_allowed"] is False
            assert record["replayable"] is True
            assert record["auditable"] is True
            assert 0 <= record["quality_scores"]["confidence_score"] <= 100
            if record["noise_filter"]["unsafe_personal_data"]:
                unsafe_seen = True
            if record["noise_filter"]["noise_status"] in {"usable_for_review", "monitor"}:
                usable_or_monitor_seen = True

        assert unsafe_seen is True
        assert usable_or_monitor_seen is True

        scoring_policy = result["signalQualityScoringPolicy"]
        assert scoring_policy["policy_id"] == "SIGNAL_QUALITY_SCORING_POLICY"
        for field in score_fields:
            assert field in scoring_policy["fields"]
        assert scoring_policy["blocked_actions"]["training_allowed"] is False
        assert scoring_policy["blocked_actions"]["promotion_allowed"] is False
        assert scoring_policy["blocked_actions"]["writeback_allowed"] is False
        assert scoring_policy["blocked_actions"]["contact_user_allowed"] is False

        noise_report = result["signalNoiseFilterReport"]
        assert noise_report["report_id"] == "SIGNAL_NOISE_FILTER_REPORT"
        assert noise_report["record_count"] == normalized_sample["normalized_record_count"]
        assert noise_report["flag_counts"]["unsafe_personal_data"] >= 1
        assert noise_report["unsafe_signals_blocked_from_training"] is True
        assert noise_report["unsafe_signals_blocked_from_promotion"] is True
        assert noise_report["writeback_allowed"] is False
        assert noise_report["contact_user_allowed"] is False

        evidence = result["socialSignalNormalizationEvidence"]
        assert evidence["normalization_policy_defined"] is True
        assert evidence["quality_scoring_policy_defined"] is True
        assert evidence["noise_filter_report_generated"] is True
        assert evidence["engagement_metrics_normalized"] is True
        assert evidence["content_signals_normalized"] is True
        assert evidence["quality_scores_generated"] is True
        assert evidence["unsafe_filtering_active"] is True
        assert evidence["training_started"] is False
        assert evidence["promotion_started"] is False
        assert evidence["platform_writeback_called"] is False
        assert evidence["users_contacted"] is False
        assert evidence["all_records_replayable"] is True
        assert evidence["all_records_auditable"] is True
        assert evidence["all_records_human_review_required"] is True

        for output_name in [
            "SOCIAL_SIGNAL_NORMALIZATION_POLICY.json",
            "NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json",
            "SIGNAL_QUALITY_SCORING_POLICY.json",
            "SIGNAL_NOISE_FILTER_REPORT.json",
            "SOCIAL_SIGNAL_NORMALIZATION_EVIDENCE.json",
        ]:
            path = output_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("social_signal_normalization_smoke_test passed")


if __name__ == "__main__":
    main()
