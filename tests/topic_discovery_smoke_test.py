from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.topic_discovery_engine import TopicDiscoveryEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "discovered_topics"
        engine = TopicDiscoveryEngine(root)

        json_path = Path(tmp) / "questions.json"
        json_path.write_text(
            json.dumps(
                [
                    {
                        "source_type": "json",
                        "source": "questions.json",
                        "text": "Tokyo subway confusing and I am anxious.",
                        "platform": "Reddit",
                        "emotion_score": 0.84,
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        csv_path = Path(tmp) / "questions.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["source_type", "source", "text", "platform", "emotion_score"])
            writer.writeheader()
            writer.writerow(
                {
                    "source_type": "csv",
                    "source": "questions.csv",
                    "text": "Air fryer cleaning is frustrating.",
                    "platform": "TikTok",
                    "emotion_score": "0.8",
                }
            )
        text_path = Path(tmp) / "notes.txt"
        text_path.write_text("Vacuum lost suction and dust is still there.\n", encoding="utf-8")

        items = [
            {
                "source_type": "rss",
                "source": "rss",
                "text": "东京地铁复杂，第一次去日本很怕换乘错。",
                "platform": "RSS",
                "emotion_score": 0.9,
            },
            {
                "source_type": "manual_import",
                "source": "manual",
                "text": "Tokyo train transfer at Shinjuku is a station maze.",
                "platform": "Threads",
                "emotion_score": 0.82,
            },
            *engine.load_json_source(json_path),
            *engine.load_csv_source(csv_path),
            *engine.load_text_source(text_path),
        ]
        report = engine.discover(items)

        assert report["report_id"] == "DISCOVERED_TOPICS_REPORT"
        assert set(report["supportedSources"]) == {"RSS", "manual_import", "JSON", "CSV", "local_text"}
        assert report["topicSummary"]["total_source_items"] == 5
        assert report["discoveredTopics"], "Topics must be discovered"

        topics = {topic["canonical_pain_point"]: topic for topic in report["discoveredTopics"]}
        assert "Tokyo transport anxiety" in topics
        assert "Air fryer cleaning friction" in topics
        assert "Vacuum performance anxiety" in topics

        tokyo = topics["Tokyo transport anxiety"]
        assert tokyo["frequency"] >= 3
        assert tokyo["repeated"] is True
        assert tokyo["high_emotion"] is True
        assert {"rss", "manual_import", "json"}.issubset(set(tokyo["source_types"]))

        air_fryer = topics["Air fryer cleaning friction"]
        assert air_fryer["emerging"] is True
        assert air_fryer["high_emotion"] is True

        assert engine.report_path.exists()
        assert engine.topics_path.exists()
        assert engine.sources_path.exists()
        saved = json.loads(engine.report_path.read_text(encoding="utf-8"))
        assert saved["topicSummary"]["total_topics"] >= 3

    print("topic discovery smoke test passed")


if __name__ == "__main__":
    main()
