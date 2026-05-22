from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.best_answer_learning_engine import BestAnswerLearningEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        events = [
            {
                "feedback_id": "feedback_001",
                "reply_attempt_id": "reply_red_001",
                "question_id": "Q001",
                "platform": "Reddit",
                "question_text": "How do I avoid getting lost at Shinjuku station?",
                "reply_text": "Use one main gate, one route, and one backup.",
                "liked": True,
                "replied": True,
                "saved": True,
                "shared": False,
                "ignored": False,
            },
            {
                "feedback_id": "feedback_002",
                "reply_attempt_id": "reply_tt_001",
                "question_id": "Q002",
                "platform": "TikTok",
                "question_text": "Is Suica worth it?",
                "reply_text": "Get Suica if you want faster payment.",
                "liked": True,
                "replied": False,
                "saved": False,
                "shared": False,
                "ignored": False,
            },
            {
                "feedback_id": "feedback_003",
                "reply_attempt_id": "reply_x_001",
                "question_id": "Q003",
                "platform": "X",
                "question_text": "Tokyo rainy day?",
                "reply_text": "Try indoor places.",
                "liked": False,
                "replied": False,
                "saved": False,
                "shared": False,
                "ignored": True,
            },
        ]
        engine = BestAnswerLearningEngine(Path(tmp) / "best_answer_learning")
        report = engine.learn(events)

        assert report["report_id"] == "BEST_ANSWER_LEARNING_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_learning_from_feedback_only"
        assert report["learningInputs"]["feedback_events"] == 3
        assert report["learningInputs"]["positive_events"] == 2
        assert report["learningInputs"]["failed_events"] == 1

        memory = report["bestAnswerLearning"]
        assert memory["bestAnswer"]["reply_attempt_id"] == "reply_red_001"
        assert memory["bestHook"] == "reduce transit uncertainty first"
        assert memory["bestTone"] == "detailed, calm, non-promotional"
        assert memory["bestPlatformStyle"] == "longer practical explanation"
        assert len(memory["failedAnswers"]) == 1
        assert memory["failedHooks"]
        assert memory["failedStrategies"]
        assert report["answerLearningTimeline"]

        assert (Path(tmp) / "best_answer_learning" / "BEST_ANSWER_LEARNING_REPORT.json").exists()
        assert (Path(tmp) / "best_answer_learning" / "best_answer_memory.json").exists()
        assert (Path(tmp) / "best_answer_learning" / "answer_learning_timeline.json").exists()
        saved = json.loads((Path(tmp) / "best_answer_learning" / "BEST_ANSWER_LEARNING_REPORT.json").read_text(encoding="utf-8"))
        assert saved["learningSummary"]["best_answer_id"] == "reply_red_001"

    print("best answer learning smoke test passed")


if __name__ == "__main__":
    main()
