"""Platform pain intelligence for global pain clusters."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.runtime_persistence import utc_now_iso


DEFAULT_CLUSTERS_PATH = Path("runtime/global_pain_clusters/global_pain_clusters.json")
DEFAULT_RECORDS_PATH = Path("runtime/global_batch_intelligence_collection/global_intelligence_records.json")
DEFAULT_OUTPUT_DIR = Path("runtime/platform_pain_intelligence")

SUPPORTED_PLATFORMS = [
    "Reddit",
    "TikTok",
    "Instagram",
    "YouTube",
    "X",
    "Threads",
    "SEO / Search",
    "Xiaohongshu",
]

PLATFORM_STYLE_RULES = {
    "Reddit": {
        "common_language_style": "long-form, specific, skeptical, experience-based",
        "question_format": "How do I solve this without getting trapped by tourist logistics?",
        "content_format_fit": "detailed reply, checklist, comparison, transparent caveat",
        "reply_risk": "medium",
        "promotion_risk": "high",
        "safe_cta_style": "answer first, disclose context, mention homepage only as optional reference after value",
    },
    "TikTok": {
        "common_language_style": "short rhythm, emotional hook, compressed pain language",
        "question_format": "POV: you land late and transport gets stressful",
        "content_format_fit": "short hook, fast scenario, visual before-after, comment prompt",
        "reply_risk": "medium",
        "promotion_risk": "medium",
        "safe_cta_style": "soft profile reference after a useful tip, no hard sell",
    },
    "Instagram": {
        "common_language_style": "visual, lifestyle, calm, aspirational but practical",
        "question_format": "What should I prepare before this trip moment?",
        "content_format_fit": "carousel, story checklist, saveable mini guide",
        "reply_risk": "low",
        "promotion_risk": "medium",
        "safe_cta_style": "saveable guide CTA with homepage as planning reference",
    },
    "YouTube": {
        "common_language_style": "explainer, step-by-step, practical narrative",
        "question_format": "What is the safest plan for this route or season?",
        "content_format_fit": "short explainer, route guide, problem walkthrough",
        "reply_risk": "low",
        "promotion_risk": "medium",
        "safe_cta_style": "link as supporting resource after explaining the decision logic",
    },
    "X": {
        "common_language_style": "concise, opinionated, trend-aware, fast signal",
        "question_format": "What is changing and what should travelers watch?",
        "content_format_fit": "short post, thread, trend observation, quick warning",
        "reply_risk": "medium",
        "promotion_risk": "medium",
        "safe_cta_style": "one-line resource reference only when directly relevant",
    },
    "Threads": {
        "common_language_style": "conversational, light, community-style, less formal",
        "question_format": "Has anyone else run into this trip planning problem?",
        "content_format_fit": "short conversational post, soft discussion starter",
        "reply_risk": "low",
        "promotion_risk": "medium",
        "safe_cta_style": "community-friendly optional reference, avoid repeated CTA",
    },
    "SEO / Search": {
        "common_language_style": "search intent, direct query answer, structured headings",
        "question_format": "best way to handle airport transfer / luggage / seasonal crowd problem",
        "content_format_fit": "search article, FAQ, route guide, comparison page",
        "reply_risk": "low",
        "promotion_risk": "low",
        "safe_cta_style": "contextual internal link after satisfying search intent",
    },
    "Xiaohongshu": {
        "common_language_style": "experience note, practical warning, visual lifestyle detail",
        "question_format": "避坑: this trip moment is harder than it looks",
        "content_format_fit": "note angle, checklist, route screenshot plan, saveable tips",
        "reply_risk": "medium",
        "promotion_risk": "medium",
        "safe_cta_style": "soft note-style reference after practical steps, no exaggerated claims",
    },
}


class PlatformPainIntelligence:
    """Explain how pain clusters behave differently on each platform."""

    def __init__(
        self,
        clusters_path: str | Path = DEFAULT_CLUSTERS_PATH,
        records_path: str | Path = DEFAULT_RECORDS_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.clusters_path = Path(clusters_path)
        self.records_path = Path(records_path)
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "PLATFORM_PAIN_INTELLIGENCE_REPORT.json"
        self.profiles_path = self.output_dir / "platform_pain_profiles.json"
        self.matrix_path = self.output_dir / "platform_pain_matrix.json"
        self.risk_path = self.output_dir / "platform_pain_risk_review.json"
        self.summary_path = self.output_dir / "platform_pain_summary.json"

    def build(
        self,
        clusters: list[dict[str, Any]] | None = None,
        records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        source_clusters = clusters if clusters is not None else self._load_clusters()
        source_records = records if records is not None else self._load_records()
        profiles = [self._profile(platform, source_records, source_clusters) for platform in SUPPORTED_PLATFORMS]
        matrix = self._matrix(profiles)
        risk_review = self._risk_review(profiles)
        summary = self._summary(profiles)
        report = {
            "report_id": "PLATFORM_PAIN_INTELLIGENCE_REPORT",
            "round_id": "ROUND-GLOBAL-003",
            "created_at": utc_now_iso(),
            "status": "platform_pain_intelligence_ready",
            "phase": "GLOBAL_INTELLIGENCE_COLLECTION",
            "platformPainProfiles": profiles,
            "platformPainMatrix": matrix,
            "platformPainRiskReview": risk_review,
            "platformPainSummary": summary,
            "safetyBoundary": "Platform Pain Intelligence explains platform-specific pain expression and risk only. It does not publish, reply, generate outbound promotion, contact users, or call platform write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.profiles_path.write_text(json.dumps(report["platformPainProfiles"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(json.dumps(report["platformPainMatrix"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_path.write_text(json.dumps(report["platformPainRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["platformPainSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_clusters(self) -> list[dict[str, Any]]:
        if not self.clusters_path.exists():
            GlobalPainClusterEngine().build()
        payload = json.loads(self.clusters_path.read_text(encoding="utf-8")) if self.clusters_path.exists() else []
        return payload if isinstance(payload, list) else []

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.records_path.exists():
            GlobalBatchIntelligenceCollection().collect()
        payload = json.loads(self.records_path.read_text(encoding="utf-8")) if self.records_path.exists() else []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _profile(platform: str, records: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> dict[str, Any]:
        platform_records = [item for item in records if item.get("source_platform") == platform]
        topic_counts = Counter(item.get("topic", "unknown") for item in platform_records)
        cluster_by_key = {item.get("cluster_key"): item for item in clusters}
        dominant_topics = [topic for topic, _ in topic_counts.most_common(5)]
        dominant_pain_points = []
        common_emotion = []
        for topic in dominant_topics:
            cluster = cluster_by_key.get(topic, {})
            dominant_pain_points.extend(cluster.get("pain_points", [topic])[:2])
            common_emotion.extend(cluster.get("emotion_tags", [])[:2])
        style = PLATFORM_STYLE_RULES[platform]
        promotion_risk = style["promotion_risk"]
        reply_risk = style["reply_risk"]
        return {
            "platform": platform,
            "record_count": len(platform_records),
            "dominant_pain_points": list(dict.fromkeys(dominant_pain_points))[:6],
            "dominant_topics": dominant_topics,
            "common_language_style": style["common_language_style"],
            "common_emotion": list(dict.fromkeys(common_emotion))[:6],
            "question_format": style["question_format"],
            "content_format_fit": style["content_format_fit"],
            "reply_risk": reply_risk,
            "promotion_risk": promotion_risk,
            "safe_cta_style": style["safe_cta_style"],
            "human_review_required": True,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
        }

    @staticmethod
    def _matrix(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "platform": item["platform"],
                "top_pain": (item["dominant_pain_points"] or ["needs_review"])[0],
                "language_style": item["common_language_style"],
                "content_format_fit": item["content_format_fit"],
                "reply_risk": item["reply_risk"],
                "promotion_risk": item["promotion_risk"],
                "safe_cta_style": item["safe_cta_style"],
                "human_review_required": item["human_review_required"],
            }
            for item in profiles
        ]

    @staticmethod
    def _risk_review(profiles: list[dict[str, Any]]) -> dict[str, Any]:
        high_promotion = [item["platform"] for item in profiles if item["promotion_risk"] == "high"]
        medium_reply = [item["platform"] for item in profiles if item["reply_risk"] == "medium"]
        return {
            "human_review_required": True,
            "all_platforms_human_review_required": all(item["human_review_required"] for item in profiles),
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "high_promotion_risk_platforms": high_promotion,
            "medium_reply_risk_platforms": medium_reply,
            "reddit_strong_marketing_allowed": False,
            "risk_note": "Platform guidance is analysis-only. High-risk platforms require softer CTA and explicit human review.",
        }

    @staticmethod
    def _summary(profiles: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "platform_pain_intelligence_ready": True,
            "platform_count": len(profiles),
            "supported_platforms": [item["platform"] for item in profiles],
            "all_platforms_human_review_required": all(item["human_review_required"] for item in profiles),
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "write_api_allowed": False,
            "reddit_strong_marketing_allowed": False,
            "tiktok_short_rhythm_ready": any(item["platform"] == "TikTok" and "short rhythm" in item["common_language_style"] for item in profiles),
            "seo_search_intent_ready": any(item["platform"] == "SEO / Search" and "search intent" in item["common_language_style"] for item in profiles),
            "next_recommendation": "Use platform pain profiles for Market Intelligence Matrix and later review-gated content strategy.",
        }


if __name__ == "__main__":
    result = PlatformPainIntelligence().build()
    print(json.dumps({"status": result["status"], "summary": result["platformPainSummary"]}, indent=2))
