from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_sample(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / name).read_text(encoding="utf-8"))


def assess_risk(text: str, blocked_phrases: list[str]) -> tuple[str, list[str]]:
    reasons = [phrase for phrase in blocked_phrases if phrase.lower() in text.lower()]
    return ("blocked" if reasons else "normal", reasons)


def main() -> None:
    pain_library = load_sample("korea_taiwan_pain_points.json")
    replies = load_sample("korea_taiwan_reply_workflow_rules.json")
    pain_ids = {pain["pain_point_id"] for pain in pain_library["pain_points"]}

    assert replies["source_pain_library_id"] == pain_library["pain_library_id"]
    assert replies["publishing_policy"] == "no automatic replies"
    blocked_phrases = replies["risk_rules"]["blocked_phrases"]

    languages = set()
    for template in replies["reply_templates"]:
        assert template["pain_point_id"] in pain_ids
        assert template["language"] in {"ko", "zh-Hant"}
        assert template["review_status"] == "needs_review"
        assert template["risk_level"] == "normal"
        assert template["draft_reply"]
        assert not assess_risk(template["draft_reply"], blocked_phrases)[1]
        languages.add(template["language"])

    assert languages == {"ko", "zh-Hant"}
    kr_risk, kr_reasons = assess_risk("지금 구매하면 100% 보장됩니다", blocked_phrases)
    tw_risk, tw_reasons = assess_risk("立即購買，保證有效，點我的連結", blocked_phrases)
    assert kr_risk == "blocked"
    assert tw_risk == "blocked"
    assert kr_reasons
    assert tw_reasons

    print("korea/taiwan reply workflow smoke test passed")


if __name__ == "__main__":
    main()
