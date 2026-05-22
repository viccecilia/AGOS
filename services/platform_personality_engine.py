"""Platform personality training rules integrated with Personality Layer."""

from __future__ import annotations

from services.personality_engine import PersonalityEngine


class PlatformPersonalityEngine:
    PROFILES = {
        "reddit": {
            "style": "深度、真实、长回复",
            "hook": "先承认具体问题，再给可执行步骤",
            "length": "long",
            "cta": "弱 CTA 或无 CTA",
            "avoid": ["标题党", "硬广", "过短回复"],
        },
        "tiktok": {
            "style": "Hook、情绪、短节奏",
            "hook": "用强场景开头，例如：第一次到东京站别先做这件事",
            "length": "short",
            "cta": "轻引导保存或评论",
            "avoid": ["长段解释", "学术语气", "恐吓式情绪"],
        },
        "x": {
            "style": "快速、观点、趋势",
            "hook": "一句观点先行，再给 2-3 个判断",
            "length": "short-thread",
            "cta": "引导讨论",
            "avoid": ["无观点罗列", "过度情绪"],
        },
        "instagram": {
            "style": "视觉、轻文案、氛围感",
            "hook": "以画面和情绪作为开头",
            "length": "caption",
            "cta": "保存清单",
            "avoid": ["密集技术说明", "硬广"],
        },
    }

    def __init__(self, personality: PersonalityEngine | None = None) -> None:
        self.personality = personality or PersonalityEngine()

    def profile(self, platform: str) -> dict:
        key = platform.lower()
        return {"platform": key, **self.PROFILES.get(key, self.PROFILES["reddit"])}

    def generate_style_plan(self, platform: str, question: dict) -> dict:
        profile = self.profile(platform)
        context = self.personality.build_context(
            workspace=question.get("workspace", "JAG-LAB"),
            platform=platform,
            market=question.get("market", "Japan"),
            tone=question.get("tone", "trusted_guide"),
        )
        return {
            **profile,
            "question_id": question.get("question_id"),
            "recommended_angle": f"{profile['hook']}；围绕 {question.get('question_text', '')[:50]}",
            "workspace_personality": context["workspacePersonality"],
            "market_personality": context["marketPersonality"],
            "tone_personality": context["tonePersonality"],
            "personality_instruction": (
                f"Use {context['workspacePersonality']['voice']} with "
                f"{context['marketPersonality']['tone']} market tone; avoid "
                f"{', '.join(context['workspacePersonality']['avoid'])}."
            ),
        }
