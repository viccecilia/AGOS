from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.skill_engine import SkillMarketplace, SkillPermissionError


def main() -> None:
    market = SkillMarketplace()
    starter = {skill.skill_id for skill in market.available_for_plan("starter")}
    growth = {skill.skill_id for skill in market.available_for_plan("growth")}
    premium = {skill.skill_id for skill in market.available_for_plan("premium")}

    assert "seo_skill" in starter
    assert "tiktok_skill" not in starter
    assert "tiktok_skill" in growth
    assert "premium_ai_pack" in premium

    assert market.require_enabled("growth", "tiktok_skill", {"tiktok_skill"}).name == "TikTok Skill"

    try:
        market.require_enabled("starter", "tiktok_skill", {"tiktok_skill"})
        raise AssertionError("Starter plan enabled growth skill")
    except SkillPermissionError:
        pass

    try:
        market.require_enabled("growth", "reddit_skill", set())
        raise AssertionError("Disabled skill was allowed")
    except SkillPermissionError:
        pass

    print("skill smoke test passed")


if __name__ == "__main__":
    main()
