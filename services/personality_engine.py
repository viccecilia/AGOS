"""Personality Layer foundation for AGOS Runtime training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class PersonalityEngine:
    def __init__(self, root: str | Path = "runtime/personality") -> None:
        self.root = Path(root)
        self.state_path = self.root / "personality_state.json"

    def workspace_personality(self, workspace: str = "JAG-LAB") -> dict[str, Any]:
        profiles = {
            "JAG-LAB": {
                "workspace": "JAG-LAB",
                "personality": ["真实", "可信", "专业", "像导游", "不营销"],
                "voice": "calm guide",
                "avoid": ["硬广", "标题党", "过度情绪", "虚假承诺"],
            },
            "jag_app_growth": {
                "workspace": "jag_app_growth",
                "personality": ["真实", "可信", "专业", "像导游", "不营销"],
                "voice": "trusted travel guide",
                "avoid": ["spam", "fake urgency", "account-like self promotion"],
            },
        }
        return profiles.get(workspace, profiles["JAG-LAB"])

    def platform_personality(self, platform: str) -> dict[str, Any]:
        key = platform.lower()
        profiles = {
            "reddit": {"platform": "reddit", "style": ["深度", "真实", "不硬广"], "tone": "helpful expert", "pace": "long-form"},
            "tiktok": {"platform": "tiktok", "style": ["Hook", "节奏", "情绪"], "tone": "quick rescue", "pace": "short"},
            "x": {"platform": "x", "style": ["快速", "观点", "趋势"], "tone": "sharp but useful", "pace": "thread"},
            "instagram": {"platform": "instagram", "style": ["视觉感", "轻文案", "氛围感"], "tone": "warm visual guide", "pace": "caption"},
        }
        return profiles.get(key, profiles["reddit"])

    def market_personality(self, market: str) -> dict[str, Any]:
        key = market.lower()
        profiles = {
            "europe/us": {"market": "Europe / US", "style": ["信息密度高", "真实"], "tone": "direct helpful"},
            "us": {"market": "Europe / US", "style": ["信息密度高", "真实"], "tone": "direct helpful"},
            "korea": {"market": "Korea", "style": ["视觉感", "氛围感"], "tone": "clean visual"},
            "taiwan": {"market": "Taiwan", "style": ["生活感", "慢节奏"], "tone": "warm daily-life"},
            "japan": {"market": "Japan", "style": ["细节", "可信", "安静专业"], "tone": "precise guide"},
        }
        return profiles.get(key, profiles["japan"])

    def tone_personality(self, tone: str = "trusted_guide") -> dict[str, Any]:
        tones = {
            "trusted_guide": {"tone": "trusted_guide", "traits": ["专业", "克制", "可执行"], "avoid": ["夸张", "催促"]},
            "quick_hook": {"tone": "quick_hook", "traits": ["短", "强场景", "易保存"], "avoid": ["恐吓", "误导"]},
            "community_helper": {"tone": "community_helper", "traits": ["真实", "耐心", "不居高临下"], "avoid": ["硬广", "模板感"]},
        }
        return tones.get(tone, tones["trusted_guide"])

    def build_context(
        self,
        workspace: str = "JAG-LAB",
        platform: str = "reddit",
        market: str = "Japan",
        tone: str = "trusted_guide",
    ) -> dict[str, Any]:
        state = {
            "workspacePersonality": self.workspace_personality(workspace),
            "platformPersonality": self.platform_personality(platform),
            "marketPersonality": self.market_personality(market),
            "tonePersonality": self.tone_personality(tone),
            "updated_at": utc_now_iso(),
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return state

    def current_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self.build_context()
        return json.loads(self.state_path.read_text(encoding="utf-8"))
