from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection
from services.global_pain_cluster_engine import GlobalPainClusterEngine
from services.platform_pain_intelligence import PlatformPainIntelligence


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        batch_dir = root / "global_batch_intelligence_collection"
        cluster_dir = root / "global_pain_clusters"
        platform_dir = root / "platform_pain_intelligence"

        batch = GlobalBatchIntelligenceCollection(batch_dir).collect()
        clusters = GlobalPainClusterEngine(
            input_path=batch_dir / "global_intelligence_records.json",
            output_dir=cluster_dir,
        ).build()
        report = PlatformPainIntelligence(
            clusters_path=cluster_dir / "global_pain_clusters.json",
            records_path=batch_dir / "global_intelligence_records.json",
            output_dir=platform_dir,
        ).build(clusters["globalPainClusters"], batch["globalIntelligenceRecords"])

        assert report["report_id"] == "PLATFORM_PAIN_INTELLIGENCE_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-003"
        assert report["status"] == "platform_pain_intelligence_ready"
        profiles = report["platformPainProfiles"]
        assert len(profiles) >= 6

        required_fields = {
            "platform",
            "dominant_pain_points",
            "common_language_style",
            "common_emotion",
            "question_format",
            "content_format_fit",
            "reply_risk",
            "promotion_risk",
            "safe_cta_style",
            "human_review_required",
        }
        by_platform = {item["platform"]: item for item in profiles}
        for profile in profiles:
            assert required_fields.issubset(profile)
            assert profile["human_review_required"] is True
            assert profile["auto_publish_allowed"] is False
            assert profile["auto_reply_allowed"] is False
            assert profile["write_api_allowed"] is False
            assert profile["dominant_pain_points"], profile["platform"]

        assert by_platform["Reddit"]["promotion_risk"] == "high"
        assert "answer first" in by_platform["Reddit"]["safe_cta_style"]
        assert "short rhythm" in by_platform["TikTok"]["common_language_style"]
        assert "short hook" in by_platform["TikTok"]["content_format_fit"]
        assert "search intent" in by_platform["SEO / Search"]["common_language_style"]
        assert "FAQ" in by_platform["SEO / Search"]["content_format_fit"]

        risk = report["platformPainRiskReview"]
        assert risk["reddit_strong_marketing_allowed"] is False
        assert risk["auto_publish_allowed"] is False
        assert risk["auto_reply_allowed"] is False
        assert risk["write_api_allowed"] is False

        summary = report["platformPainSummary"]
        assert summary["platform_pain_intelligence_ready"] is True
        assert summary["platform_count"] >= 6
        assert summary["all_platforms_human_review_required"] is True
        assert summary["auto_publish_allowed"] is False
        assert summary["auto_reply_allowed"] is False
        assert summary["write_api_allowed"] is False
        assert summary["reddit_strong_marketing_allowed"] is False
        assert summary["tiktok_short_rhythm_ready"] is True
        assert summary["seo_search_intent_ready"] is True

        for output_name in [
            "PLATFORM_PAIN_INTELLIGENCE_REPORT.json",
            "platform_pain_profiles.json",
            "platform_pain_matrix.json",
            "platform_pain_risk_review.json",
            "platform_pain_summary.json",
        ]:
            path = platform_dir / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("platform_pain_intelligence_smoke_test passed")


if __name__ == "__main__":
    main()
