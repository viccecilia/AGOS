from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_to_scout_pipeline import APIToScoutPipeline


def main() -> None:
    signals = [
        {
            "signal_id": "API-SIGNAL-TEST-001",
            "source_signal_type": "reddit_hot_topics",
            "platform": "Reddit",
            "language": "en",
            "market": "Japan",
            "emotion": "anxiety",
            "topic": "Tokyo transport anxiety",
            "keyword": "Tokyo subway confusing",
            "hashtag": "japantravel",
            "normalized_text": "Travelers are asking how to choose the right Tokyo transport pass.",
            "trend_strength": 83,
            "engagement_potential": "high",
            "content_potential": "high",
            "reply_potential": "high",
            "normalized_at": "2026-05-23T10:00:00+00:00",
        },
        {
            "signal_id": "API-SIGNAL-TEST-002",
            "source_signal_type": "tiktok_trends",
            "platform": "TikTok",
            "language": "en",
            "market": "Japan",
            "emotion": "frustration",
            "topic": "Tokyo first trip mistakes",
            "keyword": "airport transfer confusion",
            "hashtag": "tokyotravel",
            "normalized_text": "First-time travelers react strongly to airport transfer confusion.",
            "trend_strength": 89,
            "engagement_potential": "high",
            "content_potential": "high",
            "reply_potential": "medium",
            "normalized_at": "2026-05-23T10:01:00+00:00",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "api_scout_pipeline"
        report = APIToScoutPipeline(root).run(signals)

        assert report["report_id"] == "API_TO_SCOUT_PIPELINE_REPORT"
        assert report["status"] == "api_trends_entered_scout_intelligence"
        assert report["scope"] == "read_only_api_to_scout_pipeline"
        assert report["apiScoutPipelineSummary"]["source_signals"] == 2
        assert report["apiScoutPipelineSummary"]["api_trends_entered_scout"] is True
        assert report["apiScoutPipelineSummary"]["write_operations_enabled"] is False
        assert len(report["pipelineStages"]) == 7

        stages = [item["stage"] for item in report["apiScoutTrace"]]
        assert stages == [
            "API Signal Normalization",
            "Patrol Groups",
            "Keyword Expansion",
            "Topic Discovery",
            "Trend Clustering",
            "Heat Detection",
            "Strategic Interpretation",
        ]
        assert report["apiScoutPipelineSummary"]["patrol_groups"] >= 5
        assert report["apiScoutPipelineSummary"]["keyword_expansions"] >= 1
        assert report["apiScoutPipelineSummary"]["discovered_topics"] >= 1
        assert report["apiScoutPipelineSummary"]["trend_clusters"] >= 1
        assert report["apiScoutPipelineSummary"]["heat_signals"] >= 1
        assert report["apiScoutPipelineSummary"]["strategic_interpretations"] >= 1

        feed_text = " ".join(item["result"] for item in report["apiScoutFeed"])
        assert "API trends entered discovered Scout topics" in feed_text
        assert "Trend clusters are scored" in feed_text
        assert "why API trends matter" in feed_text

        assert (root / "API_TO_SCOUT_PIPELINE_REPORT.json").exists()
        assert (root / "api_scout_feed.json").exists()
        assert (root / "api_scout_trace.json").exists()

    print("api to scout pipeline smoke test passed")


if __name__ == "__main__":
    main()
