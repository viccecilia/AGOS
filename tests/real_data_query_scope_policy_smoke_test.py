from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.real_data_query_scope_policy import RealDataQueryScopePolicy


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "real_data_access"
        report = RealDataQueryScopePolicy(output_dir).build()

        assert report["policy_id"] == "QUERY_SCOPE_POLICY"
        assert report["round_id"] == "ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY"
        assert report["status"] == "query_scope_defined_no_api_access"

        for source in [
            "Google Trends search guidance",
            "platform search results",
            "public posts",
            "public comments",
            "public engagement metrics",
            "manual import samples",
        ]:
            assert source in report["querySourceHierarchy"]

        for content_type in [
            "help-seeking posts",
            "confusion/problem posts",
            "solution posts",
            "itinerary questions",
            "transport disruption questions",
            "must-buy/must-eat/must-visit discussions",
            "high-like posts",
            "high-share posts",
            "author-thanked answers",
        ]:
            assert content_type in report["targetContentTypes"]

        fuzzy = report["fuzzyClassificationStrategy"]
        assert fuzzy["do_not_hard_code_exact_regional_needs_too_early"] is True
        assert fuzzy["classify_discovered_needs_into_broad_categories"] is True
        assert fuzzy["uncategorized_bucket_for_new_demand_types"] is True
        assert fuzzy["cross_language_overlap_as_shared_pain"] is True
        assert fuzzy["language_specific_pain_as_individual_market_pain"] is True

        for tag in ["English", "Japanese", "Chinese", "Korean", "Southeast Asia languages"]:
            assert tag in report["languageTags"]
        for tag in ["region inferred", "region explicit", "region unknown"]:
            assert tag in report["regionTags"]

        for exclusion in [
            "private messages",
            "sensitive personal data",
            "doxxing content",
            "minors' sensitive data",
            "non-authorized account data",
            "platform-forbidden scraping",
        ]:
            assert exclusion in report["queryExclusions"]

        source_policy = report["sourcePolicy"]
        assert len(source_policy["sourceHierarchy"]) == 6
        assert all(item["read_only"] is True for item in source_policy["sourceHierarchy"])
        assert all(item["human_review_required"] is True for item in source_policy["sourceHierarchy"])
        assert all(item["api_call_allowed_now"] is False for item in source_policy["sourceHierarchy"])
        assert all(item["scraping_allowed"] is False for item in source_policy["sourceHierarchy"])
        assert source_policy["publicOnlyPolicy"]["private_messages_allowed"] is False
        assert source_policy["publicOnlyPolicy"]["platform_forbidden_scraping_allowed"] is False

        language_policy = report["languageRegionTaggingPolicy"]
        assert language_policy["overlapPolicy"]["cross_language_overlap_as_shared_pain"] is True
        assert language_policy["overlapPolicy"]["language_specific_pain_as_individual_market_pain"] is True
        assert language_policy["overlapPolicy"]["region_unknown_allowed"] is True

        content_policy = report["contentTypePolicy"]
        assert content_policy["fuzzyClassificationStrategy"]["hard_code_exact_region_needs_now"] is False
        assert content_policy["fuzzyClassificationStrategy"]["broad_category_first"] is True
        assert content_policy["fuzzyClassificationStrategy"]["uncategorized_bucket_enabled"] is True
        assert all(item["review_required"] is True for item in content_policy["targetContentTypes"])
        assert all(item["auto_reply_allowed"] is False for item in content_policy["targetContentTypes"])
        assert all(item["training_allowed_now"] is False for item in content_policy["targetContentTypes"])

        gate = report["readOnlyAndReviewGate"]
        assert gate["read_only"] is True
        assert gate["human_review_required"] is True
        assert gate["real_api_call_allowed"] is False
        assert gate["platform_scraping_allowed"] is False
        assert gate["real_data_ingestion_allowed"] is False
        assert gate["training_allowed"] is False
        assert gate["write_api_allowed"] is False

        evidence = report["queryScopeEvidence"]
        assert evidence["query_scope_policy_defined"] is True
        assert evidence["all_sources_read_only"] is True
        assert evidence["all_sources_review_gated"] is True
        assert evidence["all_content_types_review_required"] is True
        assert evidence["private_messages_excluded"] is True
        assert evidence["sensitive_personal_data_excluded"] is True
        assert evidence["doxxing_content_excluded"] is True
        assert evidence["minors_sensitive_data_excluded"] is True
        assert evidence["non_authorized_account_data_excluded"] is True
        assert evidence["platform_forbidden_scraping_excluded"] is True
        assert evidence["real_api_call_allowed"] is False
        assert evidence["platform_scraping_allowed"] is False
        assert evidence["real_data_ingestion_allowed"] is False
        assert evidence["training_allowed"] is False
        assert evidence["write_api_allowed"] is False

        for output_name in [
            "QUERY_SCOPE_POLICY.json",
            "SOURCE_POLICY.json",
            "LANGUAGE_REGION_TAGGING_POLICY.json",
            "CONTENT_TYPE_POLICY.json",
            "QUERY_SCOPE_EVIDENCE.json",
        ]:
            path = output_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("real_data_query_scope_policy_smoke_test passed")


if __name__ == "__main__":
    main()
