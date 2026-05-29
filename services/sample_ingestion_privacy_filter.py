"""Small controlled sample ingestion with privacy and lineage filters."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/real_data_samples")
ROUND_ID = "ROUND-REALDATA-005_SAMPLE_INGESTION_PRIVACY_FILTER"
PLATFORM_CAP = 3
LANGUAGE_CAP = 3
QUERY_CAP = 2
TOTAL_SAMPLE_CAP = 8

CLASSIFICATION_KEYWORDS = {
    "help-seeking": ["help", "how", "where can", "can anyone"],
    "confusion/problem": ["confused", "confusing", "lost", "not sure"],
    "solution": ["worked", "solved", "answer", "tip"],
    "recommendation": ["recommend", "best", "worth it"],
    "transport issue": ["train", "station", "airport", "taxi", "luggage", "transfer"],
    "purchase/food/visit interest": ["buy", "eat", "visit", "must-try", "restaurant"],
}


class SampleIngestionPrivacyFilter:
    """Build small-sample privacy artifacts without continuous ingestion or training."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.policy_path = self.output_dir / "SAMPLE_INGESTION_POLICY.json"
        self.privacy_policy_path = self.output_dir / "PRIVACY_FILTER_POLICY.json"
        self.lineage_path = self.output_dir / "SAMPLE_LINEAGE_MANIFEST.json"
        self.privacy_report_path = self.output_dir / "PRIVACY_FILTER_REPORT.json"
        self.evidence_path = self.output_dir / "SAMPLE_INGESTION_EVIDENCE.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        ingestion_policy = self._ingestion_policy(created_at)
        privacy_policy = self._privacy_policy(created_at)
        controlled_records = self._controlled_sample_payloads()
        capped_records, limit_events = self._apply_limits(controlled_records)
        filtered_records, privacy_events = self._filter_records(capped_records, created_at)
        lineage_manifest = self._lineage_manifest(filtered_records, created_at)
        privacy_report = self._privacy_report(filtered_records, privacy_events, limit_events, created_at)
        evidence = self._evidence(ingestion_policy, privacy_report, lineage_manifest, created_at)
        result = {
            "sampleIngestionPolicy": ingestion_policy,
            "privacyFilterPolicy": privacy_policy,
            "sampleLineageManifest": lineage_manifest,
            "privacyFilterReport": privacy_report,
            "sampleIngestionEvidence": evidence,
        }
        self.persist(result)
        return result

    def state(self) -> dict[str, Any]:
        if self.evidence_path.exists():
            return {
                "sampleIngestionPolicy": json.loads(self.policy_path.read_text(encoding="utf-8")),
                "privacyFilterPolicy": json.loads(self.privacy_policy_path.read_text(encoding="utf-8")),
                "sampleLineageManifest": json.loads(self.lineage_path.read_text(encoding="utf-8")),
                "privacyFilterReport": json.loads(self.privacy_report_path.read_text(encoding="utf-8")),
                "sampleIngestionEvidence": json.loads(self.evidence_path.read_text(encoding="utf-8")),
            }
        return self.build()

    def persist(self, result: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.policy_path.write_text(json.dumps(result["sampleIngestionPolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.privacy_policy_path.write_text(json.dumps(result["privacyFilterPolicy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.lineage_path.write_text(json.dumps(result["sampleLineageManifest"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.privacy_report_path.write_text(json.dumps(result["privacyFilterReport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.evidence_path.write_text(json.dumps(result["sampleIngestionEvidence"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _ingestion_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "SAMPLE_INGESTION_POLICY",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "sample_limits": {
                "small_batch_only": True,
                "total_sample_cap": TOTAL_SAMPLE_CAP,
                "per_platform_cap": PLATFORM_CAP,
                "per_language_cap": LANGUAGE_CAP,
                "per_query_cap": QUERY_CAP,
                "continuous_ingestion_allowed": False,
            },
            "allowed_source_modes": ["manual_controlled_sample", "operator_provided_public_reference", "mock_read_only_export"],
            "forbidden_source_modes": ["private_messages", "login_scraping", "continuous_api_collection", "write_api_response"],
            "storage_policy": {
                "store_raw_content": False,
                "store_filtered_excerpt_only": True,
                "store_large_real_dataset": False,
                "training_allowed": False,
                "automatic_promotion_allowed": False,
            },
        }

    @staticmethod
    def _privacy_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "PRIVACY_FILTER_POLICY",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "filters": [
                "remove private identifiers",
                "remove contact information",
                "remove precise personal location",
                "remove sensitive personal information",
                "flag minors' data",
                "exclude private messages",
            ],
            "redaction_tokens": {
                "private_identifier": "[REDACTED_IDENTIFIER]",
                "contact_information": "[REDACTED_CONTACT]",
                "precise_personal_location": "[REDACTED_LOCATION]",
                "sensitive_personal_information": "[REDACTED_SENSITIVE]",
            },
            "exclusion_policy": {
                "private_messages_excluded": True,
                "minors_data_flagged_for_exclusion": True,
                "sensitive_pii_training_allowed": False,
            },
        }

    @staticmethod
    def _controlled_sample_payloads() -> list[dict[str, Any]]:
        return [
            {
                "platform_id": "youtube",
                "source_type": "public_comment",
                "query_id": "japan_airport_transfer",
                "language": "English",
                "region": "region inferred: US",
                "content_type_hint": "help-seeking",
                "text": "Can anyone help with Haneda airport transfer after midnight? I have 2 suitcases, passport note, and emailed me at traveler@example.com.",
                "engagement_metrics": {"likes": 18, "replies": 4, "shares": 1},
                "source_ref": "yt_public_ref_001",
            },
            {
                "platform_id": "tiktok",
                "source_type": "public_post",
                "query_id": "tokyo_transport_confusion",
                "language": "English",
                "region": "region unknown",
                "content_type_hint": "confusion/problem",
                "text": "Tokyo station transfer is confusing. Not sure if taxi or train is better with luggage.",
                "engagement_metrics": {"likes": 42, "replies": 12, "shares": 7},
                "source_ref": "tt_public_ref_002",
            },
            {
                "platform_id": "instagram",
                "source_type": "public_comment",
                "query_id": "kyoto_visit_food",
                "language": "Chinese",
                "region": "region inferred: Taiwan",
                "content_type_hint": "purchase/food/visit interest",
                "text": "京都紅葉季有什麼 must-eat 和 must-visit？我住在 3-2-1 Sample Street, Kyoto。",
                "engagement_metrics": {"likes": 9, "replies": 2, "shares": 0},
                "source_ref": "ig_public_ref_003",
            },
            {
                "platform_id": "youtube",
                "source_type": "public_comment",
                "query_id": "family_trip_transfer",
                "language": "Korean",
                "region": "region inferred: Korea",
                "content_type_hint": "transport issue",
                "text": "가족 여행인데 Narita에서 호텔까지 아이와 짐이 많아서 이동 방법 추천 부탁해요.",
                "engagement_metrics": {"likes": 6, "replies": 1, "shares": 0},
                "source_ref": "yt_public_ref_004",
            },
            {
                "platform_id": "tiktok",
                "source_type": "public_comment",
                "query_id": "osaka_food_visit",
                "language": "Southeast Asia languages",
                "region": "region inferred: Southeast Asia",
                "content_type_hint": "recommendation",
                "text": "Best Osaka food street and airport train tip? My phone is +1-555-0199 if guide can contact.",
                "engagement_metrics": {"likes": 25, "replies": 8, "shares": 3},
                "source_ref": "tt_public_ref_005",
            },
            {
                "platform_id": "instagram",
                "source_type": "private_message",
                "query_id": "private_dm_excluded",
                "language": "English",
                "region": "region explicit: Japan",
                "content_type_hint": "help-seeking",
                "text": "Private DM with passport details and hotel room number.",
                "engagement_metrics": {"likes": 0, "replies": 0, "shares": 0},
                "source_ref": "private_dm_ref_006",
            },
            {
                "platform_id": "youtube",
                "source_type": "public_comment",
                "query_id": "minor_school_trip",
                "language": "Japanese",
                "region": "region explicit: Japan",
                "content_type_hint": "transport issue",
                "text": "中学生だけで夜に新宿からホテルまで移動する安全な方法は？",
                "engagement_metrics": {"likes": 3, "replies": 1, "shares": 0},
                "source_ref": "yt_public_ref_007",
            },
            {
                "platform_id": "instagram",
                "source_type": "public_post",
                "query_id": "solution_airport_transfer",
                "language": "English",
                "region": "region inferred: Europe",
                "content_type_hint": "solution",
                "text": "Solved airport transfer: pre-booking helped when arriving late with luggage.",
                "engagement_metrics": {"likes": 15, "replies": 3, "shares": 2},
                "source_ref": "ig_public_ref_008",
            },
        ]

    @staticmethod
    def _apply_limits(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        kept: list[dict[str, Any]] = []
        limit_events: list[dict[str, Any]] = []
        platform_counts: dict[str, int] = {}
        language_counts: dict[str, int] = {}
        query_counts: dict[str, int] = {}
        for record in records:
            platform = record["platform_id"]
            language = record["language"]
            query = record["query_id"]
            blocked_reasons = []
            if len(kept) >= TOTAL_SAMPLE_CAP:
                blocked_reasons.append("total_sample_cap")
            if platform_counts.get(platform, 0) >= PLATFORM_CAP:
                blocked_reasons.append("per_platform_cap")
            if language_counts.get(language, 0) >= LANGUAGE_CAP:
                blocked_reasons.append("per_language_cap")
            if query_counts.get(query, 0) >= QUERY_CAP:
                blocked_reasons.append("per_query_cap")
            if blocked_reasons:
                limit_events.append({"source_ref": record["source_ref"], "blocked_reasons": blocked_reasons})
                continue
            kept.append(record)
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            language_counts[language] = language_counts.get(language, 0) + 1
            query_counts[query] = query_counts.get(query, 0) + 1
        return kept, limit_events

    def _filter_records(self, records: list[dict[str, Any]], created_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        filtered: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        for index, record in enumerate(records, start=1):
            record_id = f"SAMPLE-{index:03d}"
            source_type = record["source_type"]
            if source_type == "private_message":
                events.append({"record_id": record_id, "event": "excluded_private_message", "source_ref": record["source_ref"]})
                continue
            text = record["text"]
            redacted_text, redactions = self._redact(text)
            minors_flagged = self._has_minor_signal(text)
            if minors_flagged:
                events.append({"record_id": record_id, "event": "flagged_minors_data", "source_ref": record["source_ref"]})
            classification = self._classify(text, record.get("content_type_hint"))
            filtered.append(
                {
                    "record_id": record_id,
                    "record_hash": hashlib.sha256(f"{record['source_ref']}:{record['query_id']}".encode("utf-8")).hexdigest()[:16],
                    "platform_id": record["platform_id"],
                    "source_type": source_type,
                    "query_id": record["query_id"],
                    "collection_time": created_at,
                    "language": record["language"],
                    "region": record["region"],
                    "content_type": classification,
                    "engagement_metrics": record["engagement_metrics"],
                    "source_reference": record["source_ref"],
                    "source_url_allowed": False,
                    "filtered_excerpt": redacted_text,
                    "redaction_count": len(redactions),
                    "redaction_types": redactions,
                    "minors_data_flagged": minors_flagged,
                    "privacy_review_status": "excluded_from_training" if minors_flagged else "privacy_filtered",
                    "lineage_complete": True,
                    "training_allowed": False,
                    "automatic_promotion_allowed": False,
                }
            )
        return filtered, events

    @staticmethod
    def _redact(text: str) -> tuple[str, list[str]]:
        redactions: list[str] = []
        patterns = [
            ("contact_information", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
            ("contact_information", re.compile(r"\+?\d[\d\s().-]{7,}\d")),
            ("precise_personal_location", re.compile(r"\b\d{1,5}[-\s]\d{1,5}[-\s]\d{1,5}\s+[A-Za-z ]+")),
            ("sensitive_personal_information", re.compile(r"\b(passport|hotel room number|room number)\b", re.IGNORECASE)),
            ("private_identifier", re.compile(r"@\w+")),
        ]
        filtered = text
        for redaction_type, pattern in patterns:
            filtered, count = pattern.subn(f"[REDACTED_{redaction_type.upper()}]", filtered)
            if count:
                redactions.extend([redaction_type] * count)
        return filtered, redactions

    @staticmethod
    def _has_minor_signal(text: str) -> bool:
        minor_terms = ["minor", "middle school", "中学生", "child alone", "under 18"]
        lowered = text.lower()
        return any(term.lower() in lowered for term in minor_terms)

    @staticmethod
    def _classify(text: str, hint: str | None) -> str:
        if hint in {
            "help-seeking",
            "confusion/problem",
            "solution",
            "recommendation",
            "transport issue",
            "purchase/food/visit interest",
            "uncategorized",
        }:
            return hint
        lowered = text.lower()
        for category, keywords in CLASSIFICATION_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return "uncategorized"

    @staticmethod
    def _lineage_manifest(records: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
        return {
            "manifest_id": "SAMPLE_LINEAGE_MANIFEST",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "record_count": len(records),
            "records": records,
            "lineage_fields": [
                "platform_id",
                "source_type",
                "query_id",
                "collection_time",
                "language",
                "region",
                "content_type",
                "engagement_metrics",
                "source_reference",
            ],
            "raw_content_stored": False,
            "all_records_training_blocked": all(item["training_allowed"] is False for item in records),
        }

    @staticmethod
    def _privacy_report(
        records: list[dict[str, Any]],
        privacy_events: list[dict[str, Any]],
        limit_events: list[dict[str, Any]],
        created_at: str,
    ) -> dict[str, Any]:
        redaction_total = sum(item["redaction_count"] for item in records)
        minor_count = sum(1 for item in records if item["minors_data_flagged"])
        return {
            "report_id": "PRIVACY_FILTER_REPORT",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "input_record_count": len(records) + len([event for event in privacy_events if event["event"] == "excluded_private_message"]),
            "filtered_record_count": len(records),
            "excluded_private_message_count": len([event for event in privacy_events if event["event"] == "excluded_private_message"]),
            "minors_data_flagged_count": minor_count,
            "redaction_total": redaction_total,
            "redaction_types": sorted({redaction for item in records for redaction in item["redaction_types"]}),
            "limit_events": limit_events,
            "privacy_events": privacy_events,
            "raw_content_stored": False,
            "sensitive_pii_training_allowed": False,
            "large_scale_ingestion_allowed": False,
            "automatic_promotion_allowed": False,
        }

    @staticmethod
    def _evidence(ingestion_policy: dict[str, Any], privacy_report: dict[str, Any], lineage_manifest: dict[str, Any], created_at: str) -> dict[str, Any]:
        sample_limits = ingestion_policy["sample_limits"]
        storage_policy = ingestion_policy["storage_policy"]
        return {
            "evidence_id": "SAMPLE_INGESTION_EVIDENCE",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "evidence_status": "small_sample_privacy_filtered_no_training",
            "small_batch_only": sample_limits["small_batch_only"],
            "total_sample_cap": sample_limits["total_sample_cap"],
            "per_platform_cap": sample_limits["per_platform_cap"],
            "per_language_cap": sample_limits["per_language_cap"],
            "per_query_cap": sample_limits["per_query_cap"],
            "continuous_ingestion_allowed": sample_limits["continuous_ingestion_allowed"],
            "filtered_record_count": lineage_manifest["record_count"],
            "raw_content_stored": storage_policy["store_raw_content"],
            "private_messages_excluded": privacy_report["excluded_private_message_count"] > 0,
            "contact_information_redacted": "contact_information" in privacy_report["redaction_types"],
            "precise_personal_location_redacted": "precise_personal_location" in privacy_report["redaction_types"],
            "sensitive_personal_information_redacted": "sensitive_personal_information" in privacy_report["redaction_types"],
            "minors_data_flagged": privacy_report["minors_data_flagged_count"] > 0,
            "lineage_manifest_complete": lineage_manifest["record_count"] > 0 and all(item["lineage_complete"] for item in lineage_manifest["records"]),
            "training_allowed": storage_policy["training_allowed"],
            "automatic_promotion_allowed": storage_policy["automatic_promotion_allowed"],
            "large_scale_ingestion_allowed": storage_policy["store_large_real_dataset"],
            "next_gate_required": "ROUND-REALDATA-006_SAMPLE_QUALITY_AND_BIAS_REVIEW",
        }


if __name__ == "__main__":
    report = SampleIngestionPrivacyFilter().build()
    print(json.dumps(report["sampleIngestionEvidence"], ensure_ascii=True, indent=2, sort_keys=True))
