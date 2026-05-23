from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_signal_normalization import APISignalNormalization


def main() -> None:
    platform_trends = [
        {
            "trend_id": "TREND-TT-001",
            "platform": "TikTok",
            "query": "Tokyo first trip mistakes",
            "keyword": "airport transfer confusion",
            "hashtag": "tokyotravel",
            "trend_text": "First-time travelers react strongly to airport transfer confusion.",
            "public_metric": {"mentions": 54, "comments": 21, "score": 84},
            "heat_score": 100,
            "read_status": "read",
        },
        {
            "trend_id": "TREND-RD-001",
            "platform": "Reddit",
            "query": "Tokyo transport anxiety",
            "keyword": "Tokyo subway confusing",
            "hashtag": "japantravel",
            "trend_text": "Travelers are asking how to choose the right Tokyo transport pass.",
            "public_metric": {"mentions": 42, "comments": 18, "score": 78},
            "heat_score": 96,
            "read_status": "read",
        },
        {
            "trend_id": "TREND-YT-001",
            "platform": "YouTube",
            "query": "Japan travel planning",
            "keyword": "IC card vs rail pass",
            "hashtag": "japantrip",
            "trend_text": "Short videos compare Suica, Pasmo, and JR Pass choices.",
            "public_metric": {"mentions": 31, "comments": 9, "score": 61},
            "heat_score": 70,
            "read_status": "read",
        },
        {
            "trend_id": "TREND-X-001",
            "platform": "X",
            "query": "Japan train pass",
            "keyword": "JR Pass worth it",
            "hashtag": "JapanTravel",
            "trend_text": "Users debate whether JR Pass still saves money after price changes.",
            "public_metric": {"mentions": 27, "comments": 7, "score": 55},
            "heat_score": 62,
            "read_status": "read",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "api_normalized_signals"
        report = APISignalNormalization(root).normalize(platform_trends)

        assert report["report_id"] == "API_SIGNAL_NORMALIZATION_REPORT"
        assert report["status"] == "signals_normalized"
        assert report["scope"] == "read_only_api_signal_normalization"
        assert report["normalizationSummary"]["signals_normalized"] == 4
        assert report["normalizationSummary"]["platforms"] == 4
        assert report["normalizationSummary"]["write_operations_enabled"] is False

        signals = report["normalizedSignals"]
        signal_types = {item["source_signal_type"] for item in signals}
        assert {"tiktok_trends", "reddit_hot_topics", "youtube_search", "x_trend_data"}.issubset(signal_types)

        for item in signals:
            assert item["language"] == "en"
            assert item["market"] == "Japan"
            assert item["platform"] in {"TikTok", "Reddit", "YouTube", "X"}
            assert item["emotion"] in {"anxiety", "frustration", "decision_pressure", "comparison_pressure"}
            assert 0 <= item["trend_strength"] <= 100
            assert item["engagement_potential"] in {"low", "medium", "high"}
            assert item["content_potential"] in {"medium", "high"}
            assert item["reply_potential"] in {"low", "medium", "high"}
            assert item["write_status"] == "blocked"
            assert item["why_unified"]

        assert report["apiNormalizedSignalFeed"], "normalized signal feed is required"
        assert (root / "API_SIGNAL_NORMALIZATION_REPORT.json").exists()
        assert (root / "normalized_signals.json").exists()
        assert (root / "api_normalized_signal_feed.json").exists()

    print("api signal normalization smoke test passed")


if __name__ == "__main__":
    main()
