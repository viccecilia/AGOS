from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.personality_drift_engine import PersonalityDriftEngine


def main() -> None:
    root = Path("runtime/test_personality_drift")
    if root.exists():
        shutil.rmtree(root)

    engine = PersonalityDriftEngine(root)
    alerts = engine.detect(
        {
            "platform": "reddit",
            "reply": "Buy now. You won't believe this secret trick. Same hook repeated.",
            "style": "reddit short hook with generic reply and panic framing",
            "personality": "平台人格错乱, 模板化, 过度情绪",
        }
    )
    issues = {item["issue"] for item in alerts}
    assert "过度营销" in issues
    assert "过度情绪化" in issues
    assert "平台人格错乱" in issues
    assert "clickbait" in issues
    assert "机械回复" in issues
    assert "内容重复" in issues
    assert all(item["reason"] for item in alerts)
    assert engine.summary()["personalityDriftStatus"] == "needs_human_review"
    assert (root / "personality_drift_alerts.json").exists()

    shutil.rmtree(root)
    print("personality_drift_smoke_test passed")


if __name__ == "__main__":
    main()
