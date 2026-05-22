from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.platform_personality_engine import PlatformPersonalityEngine


def main() -> None:
    engine = PlatformPersonalityEngine()
    question = {"question_id": "q1", "question_text": "How do I avoid getting lost in Tokyo station?"}
    reddit = engine.generate_style_plan("reddit", question)
    tiktok = engine.generate_style_plan("tiktok", question)
    x_plan = engine.generate_style_plan("x", question)

    assert reddit["style"] != tiktok["style"]
    assert tiktok["length"] != reddit["length"]
    assert x_plan["style"] != reddit["style"]
    assert "深度" in reddit["style"]
    assert "Hook" in tiktok["style"]

    print("platform personality smoke test passed")


if __name__ == "__main__":
    main()
