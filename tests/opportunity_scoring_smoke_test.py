from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.opportunity_scoring_engine import OpportunityScoringEngine


def main() -> None:
    engine = OpportunityScoringEngine()
    high = engine.score(
        {
            "question_id": "high",
            "market": "Japan",
            "platform": "reddit",
            "question_text": "I am lost and confused about Tokyo train station transfers. What should I check first?",
            "pain_points": ["transport anxiety"],
        }
    )
    low = engine.score({"question_id": "low", "question_text": "Nice weather today.", "pain_points": []})

    assert high.total_score > low.total_score
    assert high.verdict in {"high_value", "medium_value"}
    assert low.verdict == "low_value"
    assert high.reasons

    print("opportunity scoring smoke test passed")


if __name__ == "__main__":
    main()
