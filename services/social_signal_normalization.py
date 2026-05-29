"""Normalize privacy-filtered social samples into comparable AGOS signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


ROUND_ID = "ROUND-REALDATA-006_SOCIAL_SIGNAL_NORMALIZATION"
DEFAULT_OUTPUT_DIR = Path("runtime/real_data_samples")
DEFAULT_LINEAGE_PATH = DEFAULT_OUTPUT_DIR / "SAMPLE_LINEAGE_MANIFEST.json"

ENGAGEMENT_FIELDS = [
    "likes",
    "comments",
    "shares",
    "saves",
    "views",
    "author_thanks",
    "reply_depth",
    "reposts",
]

CONTENT_SIGNAL_FIELDS = [
    "question_type",
    "pain_category",
    "emotion_intensity",
    "urgency",
    "language",
    "region",
    "platform",
    "content_format",
]

QUALITY_SCORE_FIELDS = [
    "evidence_strength",
    "duplication_score",
    "engagement_strength",
    "relevance_score",
    "mobility_relevance",
    "risk_score",
    "confidence_score",
]

NOISE_FLAGS = [
    "spam",
    "ads",
    "bot_like_content",
    "off_topic_content",
    "unsafe_personal_data",
    "unverifiable_claims",
]


class SocialSignalNormalization:
    """Build replayable, auditable signal artifacts without training or promotion."""

    def __init__(
        self,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
        lineage_path: str | Path = DEFAULT_LINEAGE_PATH,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.lineage_path = Path(lineage_path)
        self.policy_path = self.output_dir / "SOCIAL_SIGNAL_NORMALIZATION_POLICY.json"
        self.sample_path = self.output_dir / "NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json"
        self.scoring_policy_path = self.output_dir / "SIGNAL_QUALITY_SCORING_POLICY.json"
        self.noise_report_path = self.output_dir / "SIGNAL_NOISE_FILTER_REPORT.json"
        self.evidence_path = self.output_dir / "SOCIAL_SIGNAL_NORMALIZATION_EVIDENCE.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        lineage_manifest = self._load_lineage_manifest()
        records = lineage_manifest.get("records", [])
        policy = self._normalization_policy(created_at)
        scoring_policy = self._quality_scoring_policy(created_at)
        normalized_records = [
            self._normalize_record(record, index + 1, created_at)
            for index, record in enumerate(records)
        ]
        sample = self._normalized_sample(normalized_records, lineage_manifest, created_at)
        noise_report = self._noise_report(normalized_records, created_at)
        evidence = self._evidence(policy, sample, scoring_policy, noise_report, created_at)
        result = {
            "socialSignalNormalizationPolicy": policy,
            "normalizedSocialSignalSample": sample,
            "signalQualityScoringPolicy": scoring_policy,
            "signalNoiseFilterReport": noise_report,
            "socialSignalNormalizationEvidence": evidence,
        }
        self.persist(result)
        return result

    def state(self) -> dict[str, Any]:
        if self.evidence_path.exists():
            return {
                "socialSignalNormalizationPolicy": json.loads(self.policy_path.read_text(encoding="utf-8")),
                "normalizedSocialSignalSample": json.loads(self.sample_path.read_text(encoding="utf-8")),
                "signalQualityScoringPolicy": json.loads(self.scoring_policy_path.read_text(encoding="utf-8")),
                "signalNoiseFilterReport": json.loads(self.noise_report_path.read_text(encoding="utf-8")),
                "socialSignalNormalizationEvidence": json.loads(self.evidence_path.read_text(encoding="utf-8")),
            }
        return self.build()

    def persist(self, result: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        write_map = {
            self.policy_path: result["socialSignalNormalizationPolicy"],
            self.sample_path: result["normalizedSocialSignalSample"],
            self.scoring_policy_path: result["signalQualityScoringPolicy"],
            self.noise_report_path: result["signalNoiseFilterReport"],
            self.evidence_path: result["socialSignalNormalizationEvidence"],
        }
        for path, payload in write_map.items():
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_lineage_manifest(self) -> dict[str, Any]:
        if not self.lineage_path.exists():
            raise FileNotFoundError(f"missing sample lineage manifest: {self.lineage_path}")
        return json.loads(self.lineage_path.read_text(encoding="utf-8"))

    @staticmethod
    def _normalization_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "SOCIAL_SIGNAL_NORMALIZATION_POLICY",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "input_contract": {
                "source_manifest": "runtime/real_data_samples/SAMPLE_LINEAGE_MANIFEST.json",
                "raw_content_required": False,
                "privacy_filtered_input_required": True,
                "small_sample_only": True,
            },
            "normalized_engagement_metrics": ENGAGEMENT_FIELDS,
            "normalized_content_signals": CONTENT_SIGNAL_FIELDS,
            "quality_scoring_fields": QUALITY_SCORE_FIELDS,
            "noise_and_unsafe_flags": NOISE_FLAGS,
            "safety_boundary": {
                "training_allowed": False,
                "promotion_allowed": False,
                "writeback_allowed": False,
                "contact_user_allowed": False,
                "platform_api_calls_allowed": False,
            },
            "audit_policy": {
                "replayable": True,
                "auditable": True,
                "lineage_required": True,
                "human_review_required": True,
            },
        }

    @staticmethod
    def _quality_scoring_policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "SIGNAL_QUALITY_SCORING_POLICY",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "score_range": "0-100",
            "fields": {
                "evidence_strength": "lineage completeness, public source type, and source reference quality",
                "duplication_score": "placeholder duplicate pressure score; higher means more duplicate-like",
                "engagement_strength": "normalized likes, comments, shares, saves, views, thanks, depth, and reposts",
                "relevance_score": "question type and pain category fit for AGOS mobility intelligence",
                "mobility_relevance": "airport, transfer, luggage, taxi, train, station, family, event, and route intent",
                "risk_score": "redaction, minors, unverifiable claims, ads, spam, and unsafe personal-data risk",
                "confidence_score": "combined evidence, relevance, engagement, and inverse risk",
            },
            "classification": {
                "usable_for_review": "confidence >= 55 and risk < 55",
                "monitor": "confidence >= 40 or risk < 70",
                "unsafe_review_required": "unsafe personal data, minors flag, or risk >= 70",
                "noise": "off-topic, ads, spam, or low evidence and low relevance",
            },
            "blocked_actions": {
                "training_allowed": False,
                "promotion_allowed": False,
                "writeback_allowed": False,
                "contact_user_allowed": False,
            },
        }

    def _normalize_record(self, record: dict[str, Any], sequence: int, created_at: str) -> dict[str, Any]:
        engagement = self._normalize_engagement(record.get("engagement_metrics", {}), record)
        question_type = self._question_type(record)
        pain_category = self._pain_category(record)
        emotion_intensity = self._emotion_intensity(record)
        urgency = self._urgency(record)
        content_format = self._content_format(record)
        noise_filter = self._noise_filter(record, pain_category)
        quality_scores = self._quality_scores(record, engagement, pain_category, noise_filter)
        return {
            "signal_id": f"SIGNAL-{sequence:03d}",
            "source_record_id": record.get("record_id", ""),
            "platform_id": record.get("platform_id", "unknown"),
            "platform": record.get("platform_id", "unknown"),
            "language": record.get("language", "unknown"),
            "region": record.get("region", "region unknown"),
            "content_format": content_format,
            "question_type": question_type,
            "pain_category": pain_category,
            "emotion_intensity": emotion_intensity,
            "urgency": urgency,
            "normalized_engagement": engagement,
            "quality_scores": quality_scores,
            "noise_filter": noise_filter,
            "lineage": {
                "query_id": record.get("query_id", ""),
                "source_type": record.get("source_type", ""),
                "source_reference": record.get("source_reference", ""),
                "collection_time": record.get("collection_time", ""),
                "record_hash": record.get("record_hash", ""),
                "privacy_review_status": record.get("privacy_review_status", ""),
                "sample_data_only": True,
                "source_url_allowed": bool(record.get("source_url_allowed", False)),
                "lineage_complete": bool(record.get("lineage_complete", False)),
            },
            "review_status": "needs_human_review",
            "training_allowed": False,
            "promotion_allowed": False,
            "writeback_allowed": False,
            "contact_user_allowed": False,
            "replayable": True,
            "auditable": True,
            "created_at": created_at,
        }

    @staticmethod
    def _normalize_engagement(metrics: dict[str, Any], record: dict[str, Any]) -> dict[str, int]:
        likes = int(metrics.get("likes", 0) or 0)
        comments = int(metrics.get("comments", metrics.get("replies", 0)) or 0)
        shares = int(metrics.get("shares", 0) or 0)
        saves = int(metrics.get("saves", 0) or 0)
        reposts = int(metrics.get("reposts", shares) or 0)
        reply_depth = min(comments, 5)
        author_thanks = 1 if "thank" in str(record.get("filtered_excerpt", "")).lower() else 0
        views = int(metrics.get("views", likes * 20 + comments * 10 + shares * 30 + saves * 15) or 0)
        return {
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "views": views,
            "author_thanks": author_thanks,
            "reply_depth": reply_depth,
            "reposts": reposts,
        }

    @staticmethod
    def _question_type(record: dict[str, Any]) -> str:
        content_type = str(record.get("content_type", "uncategorized"))
        mapping = {
            "help-seeking": "direct_help_question",
            "confusion/problem": "confusion_problem_question",
            "solution": "solution_post",
            "recommendation": "recommendation_request",
            "transport issue": "transport_disruption_question",
            "purchase/food/visit interest": "must_buy_must_eat_must_visit_discussion",
        }
        return mapping.get(content_type, "uncategorized")

    @staticmethod
    def _pain_category(record: dict[str, Any]) -> str:
        text = f"{record.get('query_id', '')} {record.get('content_type', '')} {record.get('filtered_excerpt', '')}".lower()
        if any(token in text for token in ["airport", "haneda", "narita", "kansai"]):
            return "airport_transfer_anxiety"
        if any(token in text for token in ["station", "train", "taxi", "transport", "transfer"]):
            return "public_transport_anxiety"
        if any(token in text for token in ["luggage", "suitcase", "family"]):
            return "luggage_or_family_trip_friction"
        if any(token in text for token in ["food", "eat", "visit", "must-eat", "must-visit"]):
            return "food_visit_recommendation_need"
        if record.get("minors_data_flagged"):
            return "minor_safety_sensitive_signal"
        return "uncategorized_pain"

    @staticmethod
    def _emotion_intensity(record: dict[str, Any]) -> str:
        content_type = record.get("content_type", "")
        replies = int(record.get("engagement_metrics", {}).get("replies", 0) or 0)
        if record.get("minors_data_flagged") or replies >= 10:
            return "high"
        if content_type in {"help-seeking", "confusion/problem", "transport issue"} or replies >= 3:
            return "medium"
        return "low"

    @staticmethod
    def _urgency(record: dict[str, Any]) -> str:
        text = f"{record.get('query_id', '')} {record.get('filtered_excerpt', '')}".lower()
        if any(token in text for token in ["midnight", "night", "airport", "narita", "haneda"]):
            return "high"
        if any(token in text for token in ["station", "transfer", "taxi", "train", "luggage"]):
            return "medium"
        return "low"

    @staticmethod
    def _content_format(record: dict[str, Any]) -> str:
        source_type = str(record.get("source_type", "unknown"))
        if "comment" in source_type:
            return "public_comment"
        if "post" in source_type:
            return "public_post"
        return "public_signal"

    @staticmethod
    def _noise_filter(record: dict[str, Any], pain_category: str) -> dict[str, Any]:
        text = str(record.get("filtered_excerpt", "")).lower()
        unsafe_personal_data = bool(record.get("redaction_count", 0) or record.get("minors_data_flagged"))
        spam = any(token in text for token in ["free money", "crypto", "casino"])
        ads = any(token in text for token in ["sponsored", "promo code", "buy now"])
        bot_like = text.count("http") > 2 or len(set(text.split())) < 4 if text else False
        off_topic = pain_category == "uncategorized_pain"
        unverifiable = "region unknown" in str(record.get("region", "")).lower() or not record.get("lineage_complete")
        if unsafe_personal_data:
            status = "unsafe_review_required"
        elif spam or ads or bot_like or off_topic:
            status = "noise"
        elif unverifiable:
            status = "monitor"
        else:
            status = "usable_for_review"
        return {
            "spam": spam,
            "ads": ads,
            "bot_like_content": bot_like,
            "off_topic_content": off_topic,
            "unsafe_personal_data": unsafe_personal_data,
            "unverifiable_claims": unverifiable,
            "noise_status": status,
            "filter_reason": SocialSignalNormalization._filter_reason(status, unsafe_personal_data, spam, ads, bot_like, off_topic, unverifiable),
        }

    @staticmethod
    def _filter_reason(
        status: str,
        unsafe_personal_data: bool,
        spam: bool,
        ads: bool,
        bot_like: bool,
        off_topic: bool,
        unverifiable: bool,
    ) -> str:
        if unsafe_personal_data:
            return "privacy redaction or minors flag requires human review before any downstream use"
        if spam:
            return "spam pattern detected"
        if ads:
            return "advertising pattern detected"
        if bot_like:
            return "bot-like content pattern detected"
        if off_topic:
            return "not enough mobility or travel pain relevance"
        if unverifiable:
            return "region or lineage confidence is incomplete"
        return "privacy-filtered signal is usable for review only"

    @staticmethod
    def _quality_scores(record: dict[str, Any], engagement: dict[str, int], pain_category: str, noise_filter: dict[str, Any]) -> dict[str, int]:
        evidence_strength = 80 if record.get("lineage_complete") else 35
        if "region unknown" in str(record.get("region", "")).lower():
            evidence_strength -= 15
        engagement_strength = min(100, engagement["likes"] + engagement["comments"] * 3 + engagement["shares"] * 5 + engagement["saves"] * 4 + engagement["author_thanks"] * 10)
        mobility_relevance = 85 if any(token in pain_category for token in ["airport", "transport", "luggage"]) else 45
        relevance_score = 80 if pain_category != "uncategorized_pain" else 25
        risk_score = 10
        if noise_filter["unsafe_personal_data"]:
            risk_score += 55
        if noise_filter["unverifiable_claims"]:
            risk_score += 15
        if noise_filter["spam"] or noise_filter["ads"] or noise_filter["bot_like_content"]:
            risk_score += 35
        if record.get("minors_data_flagged"):
            risk_score = max(risk_score, 90)
        duplication_score = 10 if record.get("query_id") else 25
        confidence = max(0, min(100, round((evidence_strength + engagement_strength + relevance_score + mobility_relevance) / 4 - risk_score * 0.25)))
        return {
            "evidence_strength": max(0, min(100, evidence_strength)),
            "duplication_score": duplication_score,
            "engagement_strength": engagement_strength,
            "relevance_score": relevance_score,
            "mobility_relevance": mobility_relevance,
            "risk_score": max(0, min(100, risk_score)),
            "confidence_score": confidence,
            "total_quality_score": max(0, min(100, round((confidence + relevance_score + mobility_relevance) / 3))),
        }

    @staticmethod
    def _normalized_sample(records: list[dict[str, Any]], lineage_manifest: dict[str, Any], created_at: str) -> dict[str, Any]:
        return {
            "sample_id": "NORMALIZED_SOCIAL_SIGNAL_SAMPLE",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "source_manifest_id": lineage_manifest.get("manifest_id", ""),
            "source_record_count": lineage_manifest.get("record_count", 0),
            "normalized_record_count": len(records),
            "sample_data_only": True,
            "training_allowed": False,
            "promotion_allowed": False,
            "writeback_allowed": False,
            "contact_user_allowed": False,
            "replayable": True,
            "auditable": True,
            "records": records,
        }

    @staticmethod
    def _noise_report(records: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
        counts = {flag: 0 for flag in NOISE_FLAGS}
        status_counts: dict[str, int] = {}
        unsafe_records: list[str] = []
        noise_records: list[str] = []
        for record in records:
            noise_filter = record["noise_filter"]
            for flag in NOISE_FLAGS:
                if noise_filter.get(flag):
                    counts[flag] += 1
            status = noise_filter["noise_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == "unsafe_review_required":
                unsafe_records.append(record["signal_id"])
            if status == "noise":
                noise_records.append(record["signal_id"])
        return {
            "report_id": "SIGNAL_NOISE_FILTER_REPORT",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "record_count": len(records),
            "flag_counts": counts,
            "status_counts": status_counts,
            "unsafe_record_ids": unsafe_records,
            "noise_record_ids": noise_records,
            "low_confidence_not_confirmed_demand": True,
            "unsafe_signals_blocked_from_training": True,
            "unsafe_signals_blocked_from_promotion": True,
            "writeback_allowed": False,
            "contact_user_allowed": False,
        }

    @staticmethod
    def _evidence(
        policy: dict[str, Any],
        sample: dict[str, Any],
        scoring_policy: dict[str, Any],
        noise_report: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        records = sample["records"]
        return {
            "evidence_id": "SOCIAL_SIGNAL_NORMALIZATION_EVIDENCE",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "normalization_policy_defined": policy["policy_id"] == "SOCIAL_SIGNAL_NORMALIZATION_POLICY",
            "quality_scoring_policy_defined": scoring_policy["policy_id"] == "SIGNAL_QUALITY_SCORING_POLICY",
            "noise_filter_report_generated": noise_report["report_id"] == "SIGNAL_NOISE_FILTER_REPORT",
            "normalized_record_count": len(records),
            "engagement_metrics_normalized": all(all(field in record["normalized_engagement"] for field in ENGAGEMENT_FIELDS) for record in records),
            "content_signals_normalized": all(all(field in record or field == "platform" for field in CONTENT_SIGNAL_FIELDS) for record in records),
            "quality_scores_generated": all(all(field in record["quality_scores"] for field in QUALITY_SCORE_FIELDS) for record in records),
            "unsafe_filtering_active": noise_report["flag_counts"]["unsafe_personal_data"] >= 1,
            "training_started": False,
            "promotion_started": False,
            "platform_writeback_called": False,
            "users_contacted": False,
            "all_records_replayable": all(record["replayable"] for record in records),
            "all_records_auditable": all(record["auditable"] for record in records),
            "all_records_human_review_required": all(record["review_status"] == "needs_human_review" for record in records),
            "next_gate": "ROUND-REALDATA-007_SIGNAL_QUALITY_AND_BIAS_REVIEW",
        }


def main() -> None:
    SocialSignalNormalization().build()
    print("social_signal_normalization artifacts generated")


if __name__ == "__main__":
    main()
