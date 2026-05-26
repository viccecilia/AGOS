from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.live_data_normalization_pipeline import LiveDataNormalizationPipeline


def main() -> None:
    live_items = [
        {
            "collection_id": "LIVE-COLLECT-0001",
            "platform": "Reddit",
            "query": "Tokyo transport anxiety",
            "keyword": "Tokyo subway confusing",
            "hashtag": "japantravel",
            "public_metric": {"mentions": 42, "comments": 18, "score": 78},
            "public_signal_text": "Travelers are asking how to choose the right Tokyo transport pass.",
            "collection_score": 100,
            "read_status": "collected",
            "write_status": "blocked",
        },
        {
            "collection_id": "LIVE-COLLECT-0002",
            "platform": "TikTok",
            "query": "Tokyo first trip mistakes",
            "keyword": "airport transfer confusion",
            "hashtag": "tokyotravel",
            "public_metric": {"mentions": 54, "comments": 21, "score": 84},
            "public_signal_text": "First-time travelers react strongly to airport transfer complexity.",
            "collection_score": 100,
            "read_status": "collected",
            "write_status": "blocked",
        },
        {
            "collection_id": "LIVE-COLLECT-0003",
            "platform": "YouTube",
            "query": "Japan travel planning",
            "keyword": "IC card vs rail pass",
            "hashtag": "japantrip",
            "public_metric": {"mentions": 31, "comments": 9, "score": 61},
            "public_signal_text": "Short videos compare Suica, Pasmo, and JR Pass choices.",
            "collection_score": 80,
            "read_status": "collected",
            "write_status": "blocked",
        },
        {
            "collection_id": "LIVE-COLLECT-0004",
            "platform": "X",
            "query": "Japan train pass",
            "keyword": "JR Pass worth it",
            "hashtag": "JapanTravel",
            "public_metric": {"mentions": 27, "comments": 7, "score": 55},
            "public_signal_text": "Users debate whether JR Pass still saves money after price changes.",
            "collection_score": 71,
            "read_status": "collected",
            "write_status": "blocked",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        pipeline = LiveDataNormalizationPipeline(Path(tmp) / "normalized_live_data")
        report = pipeline.normalize(live_items)
        items = report["normalizedLiveData"]
        summary = report["liveDataNormalizationSummary"]

        assert report["report_id"] == "LIVE_DATA_NORMALIZATION_REPORT"
        assert report["status"] == "live_data_normalized"
        assert summary["pipeline_ready"] is True
        assert summary["items_normalized"] == 4
        assert set(summary["platforms"]) == {"Reddit", "TikTok", "YouTube", "X"}
        assert "Japan" in summary["markets"]
        assert "transport_confusion" in summary["pain_points"]
        assert "airport_transfer_confusion" in summary["pain_points"]
        assert "anxiety" in summary["emotion_tags"]
        assert summary["highest_training_value"] > 0
        assert summary["average_source_confidence"] > 0
        assert summary["write_operations_enabled"] is False

        required = {
            "platform",
            "source_url",
            "language",
            "market",
            "pain_points",
            "emotion_tags",
            "trend_strength",
            "training_value_score",
            "source_confidence",
        }
        for item in items:
            assert required.issubset(item.keys())
            assert item["source_url"].startswith("local://live_collection/")
            assert item["language"] == "en"
            assert item["market"] == "Japan"
            assert item["pain_points"]
            assert item["emotion_tags"]
            assert 0 <= item["trend_strength"] <= 100
            assert 0 <= item["training_value_score"] <= 100
            assert 0 <= item["source_confidence"] <= 1
            assert item["write_status"] == "blocked"

        root = Path(tmp) / "normalized_live_data"
        assert (root / "LIVE_DATA_NORMALIZATION_REPORT.json").exists()
        assert (root / "normalized_live_data.json").exists()
        assert (root / "normalized_live_data_feed.json").exists()
        assert (root / "normalization_summary.json").exists()

    print("live_data_normalization_pipeline_smoke_test passed")


if __name__ == "__main__":
    main()
