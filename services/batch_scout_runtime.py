"""Batch Scout Runtime for processing many questions at once."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


MIN_BATCH_SIZE = 50
MAX_BATCH_SIZE = 500

PLATFORM_SEQUENCE = ["Reddit", "TikTok", "YouTube", "X", "Threads"]
QUESTION_PATTERNS = [
    {
        "topic": "Tokyo transport anxiety",
        "text": "Tokyo subway confusing for first time Japan trip. How do I avoid getting lost?",
        "category": "transport_confusion",
        "emotion": "anxiety",
        "base_priority": 91,
    },
    {
        "topic": "Japan itinerary overwhelm",
        "text": "I have too many Japan itinerary options and do not know what to choose.",
        "category": "planning_overwhelm",
        "emotion": "uncertainty",
        "base_priority": 74,
    },
    {
        "topic": "Airport transfer confusion",
        "text": "Narita to Tokyo transfer looks stressful and I am worried about choosing wrong.",
        "category": "transport_confusion",
        "emotion": "anxiety",
        "base_priority": 88,
    },
    {
        "topic": "JR Pass decision pressure",
        "text": "Is JR Pass worth it after the price increase or should I use IC cards?",
        "category": "payment_decision",
        "emotion": "decision_pressure",
        "base_priority": 82,
    },
    {
        "topic": "Rainy day Tokyo plan",
        "text": "What should I do in Tokyo if heavy rain ruins my plan?",
        "category": "weather_fallback",
        "emotion": "frustration",
        "base_priority": 69,
    },
]


class BatchScoutRuntime:
    """Process 50-500 questions through Scout, Analyze, Classify, and Priority Ranking."""

    def __init__(self, root: str | Path = "runtime/batch_runtime") -> None:
        self.root = Path(root)
        self.report_path = self.root / "BATCH_SCOUT_RUNTIME_REPORT.json"
        self.questions_path = self.root / "batch_questions.json"
        self.analysis_path = self.root / "batch_analysis.json"
        self.ranking_path = self.root / "batch_priority_ranking.json"
        self.feed_path = self.root / "batch_scout_feed.json"

    def run(self, questions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        batch_questions = questions if questions is not None else self.generate_sample_questions(MIN_BATCH_SIZE)
        self._validate_batch_size(batch_questions)
        scouted = [self._scout_question(index, item) for index, item in enumerate(batch_questions, start=1)]
        analyzed = [self._analyze_question(item) for item in scouted]
        classified = [self._classify_question(item) for item in analyzed]
        ranking = sorted(classified, key=lambda item: item["priority_score"], reverse=True)
        for rank, item in enumerate(ranking, start=1):
            item["rank"] = rank
        report = {
            "report_id": "BATCH_SCOUT_RUNTIME_REPORT",
            "created_at": utc_now_iso(),
            "status": "batch_processed",
            "scope": "local_batch_scout_runtime",
            "batchLimits": {"min_questions": MIN_BATCH_SIZE, "max_questions": MAX_BATCH_SIZE},
            "batchQuestions": scouted,
            "batchAnalysis": classified,
            "batchPriorityRanking": ranking,
            "batchScoutFeed": self._feed(classified, ranking),
            "batchScoutSummary": self._summary(classified, ranking),
            "safetyBoundary": "Batch Scout Runtime processes local question text only. It does not post, reply, follow, DM, log in, register accounts, or call external write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.run()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.questions_path.write_text(json.dumps(report["batchQuestions"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.analysis_path.write_text(json.dumps(report["batchAnalysis"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.ranking_path.write_text(json.dumps(report["batchPriorityRanking"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["batchScoutFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def generate_sample_questions(count: int) -> list[dict[str, Any]]:
        if count < MIN_BATCH_SIZE or count > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size must be between {MIN_BATCH_SIZE} and {MAX_BATCH_SIZE}")
        questions = []
        for index in range(1, count + 1):
            pattern = QUESTION_PATTERNS[(index - 1) % len(QUESTION_PATTERNS)]
            platform = PLATFORM_SEQUENCE[(index - 1) % len(PLATFORM_SEQUENCE)]
            questions.append(
                {
                    "question_id": f"BATCH-Q-{index:04d}",
                    "workspace_id": "JAG-LAB",
                    "platform": platform,
                    "language": "en",
                    "market": "Japan",
                    "question_text": pattern["text"],
                    "source": "batch_runtime_sample",
                    "created_at": utc_now_iso(),
                }
            )
        return questions

    @staticmethod
    def _validate_batch_size(questions: list[dict[str, Any]]) -> None:
        count = len(questions)
        if count < MIN_BATCH_SIZE or count > MAX_BATCH_SIZE:
            raise ValueError(f"Batch Scout Runtime supports {MIN_BATCH_SIZE}-{MAX_BATCH_SIZE} questions, got {count}")

    @staticmethod
    def _scout_question(index: int, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "batch_item_id": f"BATCH-SCOUT-{index:04d}",
            "question_id": item.get("question_id", f"BATCH-Q-{index:04d}"),
            "workspace_id": item.get("workspace_id", "JAG-LAB"),
            "platform": item.get("platform", "Local"),
            "language": item.get("language", "unknown"),
            "market": item.get("market", "unknown"),
            "question_text": item.get("question_text", ""),
            "source": item.get("source", "batch_import"),
            "scout_status": "scouted",
            "created_at": item.get("created_at", utc_now_iso()),
        }

    @staticmethod
    def _analyze_question(item: dict[str, Any]) -> dict[str, Any]:
        text = item["question_text"].lower()
        pattern = BatchScoutRuntime._pattern_for_text(text)
        return {
            **item,
            "analysis_status": "analyzed",
            "detected_topic": pattern["topic"],
            "emotion": pattern["emotion"],
            "category_hint": pattern["category"],
            "base_priority": pattern["base_priority"],
            "why_important": BatchScoutRuntime._why_important(pattern, item["platform"]),
        }

    @staticmethod
    def _classify_question(item: dict[str, Any]) -> dict[str, Any]:
        platform_bonus = {"Reddit": 7, "TikTok": 6, "YouTube": 4, "X": 3, "Threads": 2}.get(item["platform"], 0)
        emotion_bonus = {"anxiety": 8, "decision_pressure": 6, "frustration": 5, "uncertainty": 3}.get(item["emotion"], 2)
        priority_score = min(100, int(item["base_priority"]) + platform_bonus + emotion_bonus)
        return {
            **item,
            "classification_status": "classified",
            "class": item["category_hint"],
            "priority_score": priority_score,
            "priority_band": BatchScoutRuntime._priority_band(priority_score),
            "recommended_runtime_action": BatchScoutRuntime._recommended_action(item["category_hint"], item["platform"]),
        }

    @staticmethod
    def _pattern_for_text(text: str) -> dict[str, Any]:
        if "subway" in text or "transfer" in text or "lost" in text or "narita" in text:
            return QUESTION_PATTERNS[0] if "narita" not in text else QUESTION_PATTERNS[2]
        if "jr pass" in text or "ic card" in text or "worth" in text:
            return QUESTION_PATTERNS[3]
        if "rain" in text:
            return QUESTION_PATTERNS[4]
        if "itinerary" in text or "options" in text:
            return QUESTION_PATTERNS[1]
        return {
            "topic": "General travel question",
            "category": "general_information_need",
            "emotion": "information_need",
            "base_priority": 50,
        }

    @staticmethod
    def _priority_band(score: int) -> str:
        if score >= 90:
            return "critical"
        if score >= 75:
            return "high"
        if score >= 60:
            return "medium"
        return "watch"

    @staticmethod
    def _why_important(pattern: dict[str, Any], platform: str) -> str:
        return f"{pattern['topic']} appears as a repeatable pain point on {platform} and can be routed into answer, content, or scout follow-up."

    @staticmethod
    def _recommended_action(category: str, platform: str) -> str:
        if category == "transport_confusion":
            return f"Create human-reviewed transport guidance branch for {platform}."
        if category == "payment_decision":
            return f"Prepare comparison answer draft for {platform}."
        if category == "weather_fallback":
            return f"Prepare weather-safe itinerary content for {platform}."
        if category == "planning_overwhelm":
            return f"Cluster itinerary questions before drafting content for {platform}."
        return f"Keep monitoring {platform} until pattern strengthens."

    @staticmethod
    def _summary(classified: list[dict[str, Any]], ranking: list[dict[str, Any]]) -> dict[str, Any]:
        categories = Counter(item["class"] for item in classified)
        platforms = Counter(item["platform"] for item in classified)
        bands = Counter(item["priority_band"] for item in classified)
        return {
            "questions_processed": len(classified),
            "supported_batch_min": MIN_BATCH_SIZE,
            "supported_batch_max": MAX_BATCH_SIZE,
            "scout_completed": len([item for item in classified if item["scout_status"] == "scouted"]),
            "analyze_completed": len([item for item in classified if item["analysis_status"] == "analyzed"]),
            "classify_completed": len([item for item in classified if item["classification_status"] == "classified"]),
            "priority_ranked": len(ranking),
            "top_priority_question": ranking[0]["question_id"] if ranking else "none",
            "top_priority_score": ranking[0]["priority_score"] if ranking else 0,
            "category_counts": dict(categories),
            "platform_counts": dict(platforms),
            "priority_band_counts": dict(bands),
            "batch_runtime_ready": len(classified) >= MIN_BATCH_SIZE,
        }

    @staticmethod
    def _feed(classified: list[dict[str, Any]], ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
        summary = BatchScoutRuntime._summary(classified, ranking)
        top_items = ranking[:10]
        feed = [
            {
                "time": utc_now_iso(),
                "event": "batch_scout_runtime_completed",
                "questions_processed": summary["questions_processed"],
                "scout_completed": summary["scout_completed"],
                "analyze_completed": summary["analyze_completed"],
                "classify_completed": summary["classify_completed"],
                "priority_ranked": summary["priority_ranked"],
                "status": "batch_processed",
            }
        ]
        for item in top_items:
            feed.append(
                {
                    "time": utc_now_iso(),
                    "event": "top_batch_question",
                    "rank": item["rank"],
                    "question_id": item["question_id"],
                    "platform": item["platform"],
                    "topic": item["detected_topic"],
                    "class": item["class"],
                    "priority_score": item["priority_score"],
                    "priority_band": item["priority_band"],
                    "why_important": item["why_important"],
                    "recommended_runtime_action": item["recommended_runtime_action"],
                }
            )
        return feed


if __name__ == "__main__":
    result = BatchScoutRuntime().run()
    print(json.dumps({"status": result["status"], "questions": result["batchScoutSummary"]["questions_processed"]}, indent=2))
