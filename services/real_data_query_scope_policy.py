"""Real-data query scope and source policy before API dry-run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/real_data_access")

QUERY_SOURCE_HIERARCHY = [
    "Google Trends search guidance",
    "platform search results",
    "public posts",
    "public comments",
    "public engagement metrics",
    "manual import samples",
]
TARGET_CONTENT_TYPES = [
    "help-seeking posts",
    "confusion/problem posts",
    "solution posts",
    "itinerary questions",
    "transport disruption questions",
    "must-buy/must-eat/must-visit discussions",
    "high-like posts",
    "high-share posts",
    "author-thanked answers",
]
LANGUAGE_TAGS = [
    "English",
    "Japanese",
    "Chinese",
    "Korean",
    "Southeast Asia languages",
]
REGION_TAGS = [
    "region inferred",
    "region explicit",
    "region unknown",
]
QUERY_EXCLUSIONS = [
    "private messages",
    "sensitive personal data",
    "doxxing content",
    "minors' sensitive data",
    "non-authorized account data",
    "platform-forbidden scraping",
]


class RealDataQueryScopePolicy:
    """Create query/source policy artifacts without accessing platforms."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.query_scope_path = self.output_dir / "QUERY_SCOPE_POLICY.json"
        self.source_policy_path = self.output_dir / "SOURCE_POLICY.json"
        self.language_region_path = self.output_dir / "LANGUAGE_REGION_TAGGING_POLICY.json"
        self.content_type_path = self.output_dir / "CONTENT_TYPE_POLICY.json"
        self.evidence_path = self.output_dir / "QUERY_SCOPE_EVIDENCE.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        source_policy = self._source_policy(created_at)
        language_region_policy = self._language_region_policy(created_at)
        content_type_policy = self._content_type_policy(created_at)
        query_scope_policy = {
            "policy_id": "QUERY_SCOPE_POLICY",
            "round_id": "ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY",
            "phase": "AGOS_REAL_DATA_CONTROLLED_ACCESS",
            "created_at": created_at,
            "status": "query_scope_defined_no_api_access",
            "querySourceHierarchy": QUERY_SOURCE_HIERARCHY,
            "targetContentTypes": TARGET_CONTENT_TYPES,
            "fuzzyClassificationStrategy": {
                "do_not_hard_code_exact_regional_needs_too_early": True,
                "classify_discovered_needs_into_broad_categories": True,
                "uncategorized_bucket_for_new_demand_types": True,
                "cross_language_overlap_as_shared_pain": True,
                "language_specific_pain_as_individual_market_pain": True,
                "review_required_before_new_category_promotion": True,
            },
            "languageTags": LANGUAGE_TAGS,
            "regionTags": REGION_TAGS,
            "queryExclusions": QUERY_EXCLUSIONS,
            "readOnlyAndReviewGate": {
                "read_only": True,
                "human_review_required": True,
                "real_api_call_allowed": False,
                "platform_scraping_allowed": False,
                "real_data_ingestion_allowed": False,
                "training_allowed": False,
                "write_api_allowed": False,
            },
            "sourcePolicy": source_policy,
            "languageRegionTaggingPolicy": language_region_policy,
            "contentTypePolicy": content_type_policy,
        }
        evidence = self._evidence(query_scope_policy, source_policy, language_region_policy, content_type_policy, created_at)
        query_scope_policy["queryScopeEvidence"] = evidence
        self.persist(query_scope_policy)
        return query_scope_policy

    def state(self) -> dict[str, Any]:
        if self.query_scope_path.exists():
            return json.loads(self.query_scope_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.query_scope_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.source_policy_path.write_text(json.dumps(report["sourcePolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.language_region_path.write_text(json.dumps(report["languageRegionTaggingPolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.content_type_path.write_text(json.dumps(report["contentTypePolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.evidence_path.write_text(json.dumps(report["queryScopeEvidence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _source_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "SOURCE_POLICY",
            "round_id": "ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY",
            "created_at": created_at,
            "sourceHierarchy": [
                {
                    "rank": index,
                    "source_type": source,
                    "read_only": True,
                    "human_review_required": True,
                    "credential_required_before_live_access": source != "manual import samples",
                    "allowed_before_api_dry_run": source in {"Google Trends search guidance", "manual import samples"},
                    "api_call_allowed_now": False,
                    "scraping_allowed": False,
                    "write_action_allowed": False,
                }
                for index, source in enumerate(QUERY_SOURCE_HIERARCHY, start=1)
            ],
            "publicOnlyPolicy": {
                "public_posts_allowed_after_authorization": True,
                "public_comments_allowed_after_authorization": True,
                "public_engagement_metrics_allowed_after_authorization": True,
                "private_messages_allowed": False,
                "non_authorized_account_data_allowed": False,
                "platform_forbidden_scraping_allowed": False,
            },
            "reviewGate": {
                "all_sources_review_gated": True,
                "new_source_requires_policy_review": True,
                "source_evidence_required": True,
            },
        }

    @staticmethod
    def _language_region_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "LANGUAGE_REGION_TAGGING_POLICY",
            "round_id": "ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY",
            "created_at": created_at,
            "languageTags": LANGUAGE_TAGS,
            "regionTags": REGION_TAGS,
            "languageRegionRules": [
                {
                    "language": "English",
                    "default_region_tag": "region unknown",
                    "possible_markets": ["US", "Europe", "Global English", "Southeast Asia"],
                    "requires_region_evidence": True,
                },
                {
                    "language": "Japanese",
                    "default_region_tag": "region inferred",
                    "possible_markets": ["Japan"],
                    "requires_region_evidence": True,
                },
                {
                    "language": "Chinese",
                    "default_region_tag": "region inferred",
                    "possible_markets": ["China outbound", "Taiwan", "Southeast Asia"],
                    "requires_region_evidence": True,
                },
                {
                    "language": "Korean",
                    "default_region_tag": "region inferred",
                    "possible_markets": ["Korea"],
                    "requires_region_evidence": True,
                },
                {
                    "language": "Southeast Asia languages",
                    "default_region_tag": "region inferred",
                    "possible_markets": ["Southeast Asia"],
                    "requires_region_evidence": True,
                },
            ],
            "overlapPolicy": {
                "cross_language_overlap_as_shared_pain": True,
                "language_specific_pain_as_individual_market_pain": True,
                "unclear_language_goes_to_review": True,
                "region_unknown_allowed": True,
            },
        }

    @staticmethod
    def _content_type_policy(created_at: str) -> dict[str, Any]:
        broad_categories = [
            "travel planning confusion",
            "transport anxiety",
            "itinerary uncertainty",
            "place recommendation demand",
            "shopping/food discussion demand",
            "solution validation",
            "viral engagement signal",
            "uncategorized_new_demand_type",
        ]
        return {
            "policy_id": "CONTENT_TYPE_POLICY",
            "round_id": "ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY",
            "created_at": created_at,
            "targetContentTypes": [
                {
                    "content_type": item,
                    "broad_category": RealDataQueryScopePolicy._broad_category(item),
                    "review_required": True,
                    "auto_reply_allowed": False,
                    "training_allowed_now": False,
                }
                for item in TARGET_CONTENT_TYPES
            ],
            "broadCategories": broad_categories,
            "fuzzyClassificationStrategy": {
                "hard_code_exact_region_needs_now": False,
                "broad_category_first": True,
                "uncategorized_bucket_enabled": True,
                "new_demand_type_review_required": True,
                "shared_pain_cross_language_detection": True,
                "individual_market_pain_detection": True,
            },
        }

    @staticmethod
    def _broad_category(content_type: str) -> str:
        if content_type in {"help-seeking posts", "confusion/problem posts"}:
            return "travel planning confusion"
        if content_type in {"itinerary questions"}:
            return "itinerary uncertainty"
        if content_type in {"transport disruption questions"}:
            return "transport anxiety"
        if content_type in {"must-buy/must-eat/must-visit discussions"}:
            return "place recommendation demand"
        if content_type in {"solution posts", "author-thanked answers"}:
            return "solution validation"
        if content_type in {"high-like posts", "high-share posts"}:
            return "viral engagement signal"
        return "uncategorized_new_demand_type"

    @staticmethod
    def _evidence(
        query_scope_policy: dict[str, Any],
        source_policy: dict[str, Any],
        language_region_policy: dict[str, Any],
        content_type_policy: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        read_gate = query_scope_policy["readOnlyAndReviewGate"]
        return {
            "evidence_id": "QUERY_SCOPE_EVIDENCE",
            "round_id": "ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY",
            "created_at": created_at,
            "evidence_status": "query_scope_defined_no_api_no_scrape_no_training",
            "query_scope_policy_defined": True,
            "source_policy_defined": True,
            "language_region_tagging_policy_defined": True,
            "content_type_policy_defined": True,
            "query_source_count": len(query_scope_policy["querySourceHierarchy"]),
            "target_content_type_count": len(query_scope_policy["targetContentTypes"]),
            "language_tag_count": len(language_region_policy["languageTags"]),
            "region_tag_count": len(language_region_policy["regionTags"]),
            "query_exclusion_count": len(query_scope_policy["queryExclusions"]),
            "all_sources_read_only": all(item["read_only"] for item in source_policy["sourceHierarchy"]),
            "all_sources_review_gated": source_policy["reviewGate"]["all_sources_review_gated"],
            "all_content_types_review_required": all(item["review_required"] for item in content_type_policy["targetContentTypes"]),
            "uncategorized_bucket_enabled": content_type_policy["fuzzyClassificationStrategy"]["uncategorized_bucket_enabled"],
            "cross_language_overlap_as_shared_pain": language_region_policy["overlapPolicy"]["cross_language_overlap_as_shared_pain"],
            "language_specific_pain_as_individual_market_pain": language_region_policy["overlapPolicy"]["language_specific_pain_as_individual_market_pain"],
            "private_messages_excluded": "private messages" in query_scope_policy["queryExclusions"],
            "sensitive_personal_data_excluded": "sensitive personal data" in query_scope_policy["queryExclusions"],
            "doxxing_content_excluded": "doxxing content" in query_scope_policy["queryExclusions"],
            "minors_sensitive_data_excluded": "minors' sensitive data" in query_scope_policy["queryExclusions"],
            "non_authorized_account_data_excluded": "non-authorized account data" in query_scope_policy["queryExclusions"],
            "platform_forbidden_scraping_excluded": "platform-forbidden scraping" in query_scope_policy["queryExclusions"],
            "real_api_call_allowed": read_gate["real_api_call_allowed"],
            "platform_scraping_allowed": read_gate["platform_scraping_allowed"],
            "real_data_ingestion_allowed": read_gate["real_data_ingestion_allowed"],
            "training_allowed": read_gate["training_allowed"],
            "write_api_allowed": read_gate["write_api_allowed"],
            "next_gate_required": "ROUND-REALDATA-004_API_DRY_RUN_PLAN",
        }


if __name__ == "__main__":
    report = RealDataQueryScopePolicy().build()
    print(json.dumps(report["queryScopeEvidence"], ensure_ascii=True, indent=2, sort_keys=True))
