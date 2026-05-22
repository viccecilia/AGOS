"""Daily question import for AGOS Real Operations."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.keyword_expansion_engine import KeywordExpansionEngine
from services.runtime_persistence import utc_now_iso


class DailyQuestionImportEngine:
    """Import 10-30 daily questions from local/manual sources into AGOS."""

    DEFAULT_DAILY_ITEMS: list[dict[str, Any]] = [
        {
            "source_type": "rss",
            "source": "travel_rss_local_seed",
            "platform": "RSS",
            "language": "en",
            "market": "Japan",
            "question_text": "How do I avoid getting lost at Shinjuku station on my first Tokyo trip?",
        },
        {
            "source_type": "manual_import",
            "source": "operator_daily_note",
            "platform": "Manual",
            "language": "en",
            "market": "Japan",
            "question_text": "Is it worth buying a Suica card if I only stay in Tokyo for three days?",
        },
        {
            "source_type": "json",
            "source": "daily_questions.json",
            "platform": "Reddit",
            "language": "en",
            "market": "Japan",
            "question_text": "What should I do in Tokyo when it rains all day and my outdoor plan is ruined?",
        },
        {
            "source_type": "csv",
            "source": "daily_questions.csv",
            "platform": "TikTok",
            "language": "en",
            "market": "Japan",
            "question_text": "Why is Tokyo subway transfer so stressful for first-time visitors?",
        },
        {
            "source_type": "local_text",
            "source": "daily_notes.txt",
            "platform": "LocalText",
            "language": "en",
            "market": "Japan",
            "question_text": "Where should I stay in Tokyo if I want easy airport access and simple train routes?",
        },
        {
            "source_type": "manual_import",
            "source": "operator_daily_note",
            "platform": "Manual",
            "language": "en",
            "market": "Japan",
            "question_text": "How can I plan a Tokyo day without walking too much with kids?",
        },
        {
            "source_type": "json",
            "source": "daily_questions.json",
            "platform": "YouTube",
            "language": "en",
            "market": "Japan",
            "question_text": "Can I visit Kyoto as a day trip from Tokyo or is it too tiring?",
        },
        {
            "source_type": "csv",
            "source": "daily_questions.csv",
            "platform": "Instagram",
            "language": "en",
            "market": "Japan",
            "question_text": "What is a calm Tokyo itinerary for someone who hates crowded tourist spots?",
        },
        {
            "source_type": "rss",
            "source": "travel_rss_local_seed",
            "platform": "RSS",
            "language": "en",
            "market": "Japan",
            "question_text": "Which Tokyo train app is easiest for tourists who do not speak Japanese?",
        },
        {
            "source_type": "manual_import",
            "source": "operator_daily_note",
            "platform": "Manual",
            "language": "en",
            "market": "Japan",
            "question_text": "How do I choose between Shibuya, Shinjuku, and Ueno for a first hotel?",
        },
        {
            "source_type": "local_text",
            "source": "daily_notes.txt",
            "platform": "LocalText",
            "language": "en",
            "market": "Japan",
            "question_text": "What should I book in advance for Japan and what can wait until I arrive?",
        },
        {
            "source_type": "json",
            "source": "daily_questions.json",
            "platform": "Threads",
            "language": "en",
            "market": "Japan",
            "question_text": "How much cash do I really need for a one-week Japan trip?",
        },
    ]

    def __init__(self, root: str | Path = "runtime/daily_question_import") -> None:
        self.root = Path(root)
        self.report_path = self.root / "DAILY_QUESTION_IMPORT_REPORT.json"
        self.questions_path = self.root / "daily_questions.json"
        self.batch_path = self.root / "daily_import_batch.json"
        self.keyword_engine = KeywordExpansionEngine()

    def import_today(self, items: list[dict[str, Any]] | None = None, import_date: str | None = None) -> dict[str, Any]:
        import_date = import_date or datetime.now(timezone.utc).date().isoformat()
        raw_items = items or self.DEFAULT_DAILY_ITEMS
        normalized = [self._normalize_item(item, index, import_date) for index, item in enumerate(raw_items[:30], start=1)]
        if len(normalized) < 10:
            raise ValueError("Daily question import requires at least 10 questions.")
        report = {
            "report_id": "DAILY_QUESTION_IMPORT_REPORT",
            "created_at": utc_now_iso(),
            "import_date": import_date,
            "status": "active",
            "scope": "local_import_only_no_external_scraping",
            "supportedSources": ["RSS", "manual_import", "CSV", "JSON", "local_text"],
            "dailyQuestions": normalized,
            "dailyImportSummary": {
                "total_imported": len(normalized),
                "source_types": sorted({item["source_type"] for item in normalized}),
                "platforms": sorted({item["platform"] for item in normalized}),
                "markets": sorted({item["market"] for item in normalized}),
                "languages": sorted({item["language"] for item in normalized}),
                "ready_for_review": len([item for item in normalized if item["status"] == "imported"]),
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.import_today()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.questions_path.write_text(json.dumps(report["dailyQuestions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.batch_path.write_text(
            json.dumps(
                {
                    "created_at": report["created_at"],
                    "import_date": report["import_date"],
                    "total_imported": report["dailyImportSummary"]["total_imported"],
                    "question_ids": [item["question_id"] for item in report["dailyQuestions"]],
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def load_json_source(self, path: str | Path) -> list[dict[str, Any]]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def load_csv_source(self, path: str | Path) -> list[dict[str, Any]]:
        with Path(path).open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def load_text_source(self, path: str | Path) -> list[dict[str, Any]]:
        return [
            {
                "source_type": "local_text",
                "source": str(path),
                "platform": "LocalText",
                "language": "en",
                "market": "unknown",
                "question_text": line.strip(),
            }
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def load_rss_source(self, path: str | Path) -> list[dict[str, Any]]:
        root = ET.fromstring(Path(path).read_text(encoding="utf-8"))
        items = []
        for node in root.findall(".//item"):
            title = node.findtext("title") or ""
            description = node.findtext("description") or ""
            text = title.strip() or description.strip()
            if text:
                items.append(
                    {
                        "source_type": "rss",
                        "source": str(path),
                        "platform": "RSS",
                        "language": "en",
                        "market": "unknown",
                        "question_text": text,
                    }
                )
        return items

    def _normalize_item(self, item: dict[str, Any], index: int, import_date: str) -> dict[str, Any]:
        text = str(item.get("question_text") or item.get("text") or item.get("title") or "").strip()
        if not text:
            raise ValueError(f"Daily question item {index} is missing question text.")
        canonical = self.keyword_engine.normalize_phrase(text)
        return {
            "question_id": item.get("question_id", f"{import_date.replace('-', '')}-Q{index:03d}"),
            "import_date": import_date,
            "imported_at": item.get("imported_at", utc_now_iso()),
            "workspace_id": item.get("workspace_id", "JAG-LAB"),
            "source_type": item.get("source_type", "manual_import"),
            "source": item.get("source", "unknown"),
            "platform": item.get("platform", "Manual"),
            "language": item.get("language", "en"),
            "market": item.get("market", "Japan"),
            "question_text": text,
            "canonical_pain_point": item.get("canonical_pain_point", canonical),
            "status": item.get("status", "imported"),
            "review_status": item.get("review_status", "needs_human_review"),
            "safety_boundary": "local_import_no_auto_reply",
        }


if __name__ == "__main__":
    result = DailyQuestionImportEngine().import_today()
    print(json.dumps({"status": result["status"], "imported": result["dailyImportSummary"]["total_imported"]}, indent=2))
