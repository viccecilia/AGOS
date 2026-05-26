from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_collection_review_and_correction import APICollectionReviewAndCorrection
from services.live_data_import_to_memory import LiveDataImportToMemory


def main() -> None:
    normalized_items = [
        {
            "normalized_id": "LIVE-NORM-0001",
            "source_type": "Reddit topic",
            "platform": "Reddit",
            "source_url": "local://live_collection/LIVE-COLLECT-0001",
            "language": "en",
            "market": "Japan",
            "pain_points": ["transport_confusion"],
            "emotion_tags": ["anxiety"],
            "trend_strength": 92,
            "training_value_score": 94,
            "source_confidence": 0.86,
            "topic": "Tokyo transport anxiety",
            "normalized_text": "Travelers ask how to choose a Tokyo transport pass.",
        },
        {
            "normalized_id": "LIVE-NORM-0002",
            "source_type": "TikTok trend",
            "platform": "TikTok",
            "source_url": "local://live_collection/LIVE-COLLECT-0002",
            "language": "en",
            "market": "Japan",
            "pain_points": ["general_information_need"],
            "emotion_tags": ["neutral_information_need"],
            "trend_strength": 40,
            "training_value_score": 42,
            "source_confidence": 0.49,
            "topic": "random chatter",
            "normalized_text": "This is weak travel chatter.",
        },
        {
            "normalized_id": "LIVE-NORM-0003",
            "source_type": "YouTube search",
            "platform": "YouTube",
            "source_url": "local://live_collection/LIVE-COLLECT-0003",
            "language": "en",
            "market": "Japan",
            "pain_points": ["payment_and_pass_decision"],
            "emotion_tags": ["comparison_pressure"],
            "trend_strength": 74,
            "training_value_score": 76,
            "source_confidence": 0.68,
            "topic": "IC card vs rail pass",
            "normalized_text": "Travelers compare Suica, Pasmo, and JR Pass.",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp:
        memory_report = LiveDataImportToMemory(Path(tmp) / "live_memory_import").import_data(
            "JAG-LAB",
            normalized_items,
        )
        decisions = [
            {
                "review_id": "API-COLLECT-REVIEW-0001",
                "action": "mark_high_value",
                "corrections": {
                    "pain_points": ["transport_anxiety"],
                    "emotion_tags": ["planning_anxiety"],
                    "trend_strength": 96,
                    "source_confidence": 0.91,
                },
                "reason": "Pain point and emotion labels need stronger travel-specific wording.",
                "decided_by": "human_operator",
            },
            {
                "review_id": "API-COLLECT-REVIEW-0002",
                "action": "reject",
                "corrections": {
                    "source_confidence": 0.2,
                },
                "reason": "This is weak chatter, not useful intelligence.",
                "decided_by": "human_operator",
            },
            {
                "review_id": "API-COLLECT-REVIEW-0003",
                "action": "classify",
                "corrections": {
                    "trend_strength": 82,
                },
                "reason": "Trend strength should be raised after review.",
                "decided_by": "human_operator",
            },
        ]
        root = Path(tmp) / "api_collection_review"
        report = APICollectionReviewAndCorrection(root).review(memory_report, decisions)
        summary = report["collectionReviewSummary"]

        assert report["report_id"] == "API_COLLECTION_REVIEW_AND_CORRECTION_REPORT"
        assert report["status"] == "api_collection_review_ready"
        assert {"approve", "reject", "classify", "mark_low_value", "mark_high_value"}.issubset(
            set(report["supportedActions"])
        )
        assert {"pain_points", "emotion_tags", "trend_strength", "source_confidence"}.issubset(
            set(report["correctionFields"])
        )
        assert len(report["collectionReviewQueue"]) == 3
        assert len(report["collectionReviewDecisions"]) == 3
        assert len(report["correctedCollectionIntelligence"]) == 3
        assert len(report["collectionCorrectionFeed"]) == 3

        first = report["correctedCollectionIntelligence"][0]
        second = report["correctedCollectionIntelligence"][1]
        assert first["pain_points"] == ["transport_anxiety"]
        assert first["emotion_tags"] == ["planning_anxiety"]
        assert first["trend_strength"] == 96
        assert first["source_confidence"] == 0.91
        assert first["training_route"] == "approved_training_memory"
        assert second["training_route"] == "blocked_from_training"
        assert second["source_confidence"] == 0.2

        assert summary["review_ready"] is True
        assert summary["review_items"] == 3
        assert summary["rejected"] == 1
        assert summary["classified"] == 1
        assert summary["marked_high_value"] == 1
        assert summary["corrected_records"] == 3
        assert summary["pain_point_corrections"] == 1
        assert summary["emotion_corrections"] == 1
        assert summary["trend_corrections"] == 2
        assert summary["source_confidence_corrections"] == 2
        assert summary["write_operations_enabled"] is False

        assert (root / "API_COLLECTION_REVIEW_AND_CORRECTION_REPORT.json").exists()
        assert (root / "collection_review_queue.json").exists()
        assert (root / "collection_review_decisions.json").exists()
        assert (root / "corrected_collection_intelligence.json").exists()
        assert (root / "collection_correction_feed.json").exists()
        assert (root / "collection_review_summary.json").exists()

    print("api_collection_review_and_correction_smoke_test passed")


if __name__ == "__main__":
    main()
