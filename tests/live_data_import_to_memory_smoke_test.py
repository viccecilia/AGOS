from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.live_data_import_to_memory import LiveDataImportToMemory


def main() -> None:
    normalized_items = [
        {
            "normalized_id": "LIVE-NORM-0001",
            "source_collection_id": "LIVE-COLLECT-0001",
            "source_type": "Reddit topic",
            "platform": "Reddit",
            "source_url": "local://live_collection/LIVE-COLLECT-0001",
            "language": "en",
            "market": "Japan",
            "pain_points": ["transport_confusion"],
            "emotion_tags": ["anxiety", "information_need"],
            "trend_strength": 100,
            "training_value_score": 96,
            "source_confidence": 0.82,
            "topic": "Tokyo transport anxiety",
            "keyword": "Tokyo subway confusing",
            "normalized_text": "Travelers are asking how to choose the right Tokyo transport pass.",
            "write_status": "blocked",
        },
        {
            "normalized_id": "LIVE-NORM-0002",
            "source_collection_id": "LIVE-COLLECT-0002",
            "source_type": "TikTok trend",
            "platform": "TikTok",
            "source_url": "local://live_collection/LIVE-COLLECT-0002",
            "language": "en",
            "market": "Japan",
            "pain_points": ["airport_transfer_confusion", "first_trip_uncertainty"],
            "emotion_tags": ["frustration", "surprise"],
            "trend_strength": 100,
            "training_value_score": 94,
            "source_confidence": 0.84,
            "topic": "Tokyo first trip mistakes",
            "keyword": "airport transfer confusion",
            "normalized_text": "First-time travelers react strongly to airport transfer complexity.",
            "write_status": "blocked",
        },
        {
            "normalized_id": "LIVE-NORM-0003",
            "source_collection_id": "LIVE-COLLECT-0003",
            "source_type": "YouTube search",
            "platform": "YouTube",
            "source_url": "local://live_collection/LIVE-COLLECT-0003",
            "language": "en",
            "market": "Japan",
            "pain_points": ["payment_and_pass_decision"],
            "emotion_tags": ["comparison_pressure"],
            "trend_strength": 80,
            "training_value_score": 78,
            "source_confidence": 0.71,
            "topic": "Japan travel planning",
            "keyword": "IC card vs rail pass",
            "normalized_text": "Short videos compare Suica, Pasmo, and JR Pass choices.",
            "write_status": "blocked",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "live_memory_import"
        importer = LiveDataImportToMemory(root)
        report = importer.import_data("JAG-LAB", normalized_items)
        summary = report["memoryImportSummary"]

        assert report["report_id"] == "LIVE_DATA_IMPORT_TO_MEMORY_REPORT"
        assert report["status"] == "live_intelligence_imported_to_memory"
        assert set(report["memoryTargets"]) == {
            "Question Inbox",
            "Pain Point Library",
            "Pattern Memory",
            "Trend Cluster",
            "Scout Intelligence",
        }
        assert len(report["questionInboxMemory"]) == 3
        assert len(report["painPointLibraryMemory"]) >= 3
        assert len(report["patternMemoryImport"]) == 3
        assert len(report["trendClusterMemory"]) >= 3
        assert len(report["scoutIntelligenceMemory"]) == 3
        assert len(report["memoryImportFeed"]) == 5

        assert summary["import_ready"] is True
        assert summary["normalized_items_imported"] == 3
        assert summary["question_inbox_items"] == 3
        assert summary["pain_points_imported"] >= 3
        assert summary["patterns_imported"] == 3
        assert summary["trend_clusters_imported"] >= 3
        assert summary["scout_intelligence_items"] == 3
        assert summary["pattern_learning_triggered"] is True
        assert summary["replay_training_triggered"] is True
        assert summary["intelligence_ranking_triggered"] is True
        assert summary["write_operations_enabled"] is False

        pattern_summary = report["triggeredPatternLearning"]["patternLearningSummary"]
        replay_summary = report["triggeredReplayTraining"]["replayTrainingSummary"]
        ranking_summary = report["triggeredIntelligenceRanking"]["heatSummary"]
        assert pattern_summary["pattern_memory_ready"] is True
        assert replay_summary["replay_training_ready"] is True
        assert ranking_summary["total_signals"] >= 1
        assert report["triggeredIntelligenceRanking"]["opportunityRanking"]

        assert (root / "LIVE_DATA_IMPORT_TO_MEMORY_REPORT.json").exists()
        assert (root / "question_inbox_memory.json").exists()
        assert (root / "pain_point_library_memory.json").exists()
        assert (root / "pattern_memory_import.json").exists()
        assert (root / "trend_cluster_memory.json").exists()
        assert (root / "scout_intelligence_memory.json").exists()
        assert (root / "memory_import_feed.json").exists()
        assert (root / "memory_import_summary.json").exists()

    print("live_data_import_to_memory_smoke_test passed")


if __name__ == "__main__":
    main()
