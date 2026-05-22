from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.daily_question_import_engine import DailyQuestionImportEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "daily_question_import"
        engine = DailyQuestionImportEngine(root)

        json_path = Path(tmp) / "daily.json"
        json_path.write_text(
            json.dumps(
                [
                    {"source_type": "json", "source": "daily.json", "platform": "Reddit", "question_text": "How do I avoid Shinjuku station confusion?"},
                    {"source_type": "json", "source": "daily.json", "platform": "YouTube", "question_text": "What is a rainy day Tokyo plan?"},
                ]
            ),
            encoding="utf-8",
        )
        csv_path = Path(tmp) / "daily.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["source_type", "source", "platform", "question_text"])
            writer.writeheader()
            writer.writerow({"source_type": "csv", "source": "daily.csv", "platform": "TikTok", "question_text": "Tokyo subway transfer is stressful. What should I do?"})
            writer.writerow({"source_type": "csv", "source": "daily.csv", "platform": "Instagram", "question_text": "Where should I stay in Tokyo for simple trains?"})
        text_path = Path(tmp) / "daily.txt"
        text_path.write_text("How much cash do I need in Japan?\nWhat should I book before Japan?\n", encoding="utf-8")
        rss_path = Path(tmp) / "daily.xml"
        rss_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<rss><channel>
<item><title>Can I do Kyoto as a day trip from Tokyo?</title></item>
<item><title>Which Tokyo train app is easiest for tourists?</title></item>
</channel></rss>""",
            encoding="utf-8",
        )

        items = [
            {"source_type": "manual_import", "source": "operator", "platform": "Manual", "question_text": "Is Suica worth it for three days in Tokyo?"},
            {"source_type": "manual_import", "source": "operator", "platform": "Manual", "question_text": "How do I plan Tokyo with kids and less walking?"},
            *engine.load_json_source(json_path),
            *engine.load_csv_source(csv_path),
            *engine.load_text_source(text_path),
            *engine.load_rss_source(rss_path),
        ]
        report = engine.import_today(items, import_date="2026-05-22")

        assert report["report_id"] == "DAILY_QUESTION_IMPORT_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_import_only_no_external_scraping"
        assert report["dailyImportSummary"]["total_imported"] == 10
        assert set(report["supportedSources"]) == {"RSS", "manual_import", "CSV", "JSON", "local_text"}
        assert {"rss", "manual_import", "csv", "json", "local_text"}.issubset(set(report["dailyImportSummary"]["source_types"]))
        assert len(report["dailyQuestions"]) == 10
        assert all(item["question_id"].startswith("20260522-Q") for item in report["dailyQuestions"])
        assert all(item["status"] == "imported" for item in report["dailyQuestions"])
        assert all(item["review_status"] == "needs_human_review" for item in report["dailyQuestions"])
        assert any("Shinjuku" in item["question_text"] for item in report["dailyQuestions"])

        assert (root / "DAILY_QUESTION_IMPORT_REPORT.json").exists()
        assert (root / "daily_questions.json").exists()
        assert (root / "daily_import_batch.json").exists()
        saved = json.loads((root / "DAILY_QUESTION_IMPORT_REPORT.json").read_text(encoding="utf-8"))
        assert saved["dailyImportSummary"]["ready_for_review"] == 10

    print("daily question import smoke test passed")


if __name__ == "__main__":
    main()
