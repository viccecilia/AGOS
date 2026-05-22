"""Platform-specific strategy personality planning for AGOS Runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class RuntimeStrategyPersonalityEngine:
    """Convert platform personality into concrete operating strategy."""

    STRATEGIES: dict[str, dict[str, Any]] = {
        "reddit": {
            "platform": "reddit",
            "operating_philosophy": "Earn trust through depth, specificity, and community-first answers.",
            "strategy_goal": "Turn high-intent travel questions into helpful expert replies.",
            "content_shape": "Long-form answer with context, tradeoffs, and practical steps.",
            "interaction_style": "Transparent, non-promotional, experience-based, and ready for follow-up discussion.",
            "cadence": "Low frequency, high relevance, reply only when the question is a real pain point.",
            "success_signal": "Replies, saves, follow-up questions, and positive community acceptance.",
            "avoid": ["hard sell", "generic tips", "copy-paste reply", "fake personal experience"],
            "recommended_actions": [
                "Find detailed pain questions before replying.",
                "Answer the concrete situation first, then softly mention JAG if relevant.",
                "Store follow-up objections as learning events.",
            ],
        },
        "tiktok": {
            "platform": "tiktok",
            "operating_philosophy": "Win attention quickly, then convert anxiety into a simple visual action.",
            "strategy_goal": "Transform travel confusion into short hooks and save-worthy clips.",
            "content_shape": "Short hook, one visible pain scene, one practical payoff, one soft save CTA.",
            "interaction_style": "Fast, emotional, visual, and concrete without becoming clickbait.",
            "cadence": "Higher frequency experiments with tight hook variation and fast feedback.",
            "success_signal": "Watch retention, saves, shares, comment questions, and repeated hook performance.",
            "avoid": ["overdramatic fear", "long explanation", "platform-inappropriate depth", "spammy CTA"],
            "recommended_actions": [
                "Turn one pain point into three hook variants.",
                "Prioritize first three seconds and visual proof.",
                "Reject hooks that exaggerate risk beyond the real travel pain.",
            ],
        },
        "x": {
            "platform": "x",
            "operating_philosophy": "Use sharp observations to join live conversations and expose hidden travel friction.",
            "strategy_goal": "Create concise opinions, micro-threads, and trend reactions that earn discussion.",
            "content_shape": "One strong claim, two supporting details, one practical takeaway or thread.",
            "interaction_style": "Fast, opinionated, useful, and conversational.",
            "cadence": "Timely posting around trend windows and question bursts.",
            "success_signal": "Replies, reposts, quote posts, profile clicks, and thread completion.",
            "avoid": ["empty hot take", "slow generic advice", "excessive hashtags", "brand-like announcement"],
            "recommended_actions": [
                "Connect travel pain to a current conversation.",
                "Keep the first line opinionated but useful.",
                "Use replies to test which pain framing deserves deeper content.",
            ],
        },
        "youtube": {
            "platform": "youtube",
            "operating_philosophy": "Build durable trust through searchable explanations and proof-rich travel guidance.",
            "strategy_goal": "Convert repeated travel anxiety into evergreen videos and Shorts funnels.",
            "content_shape": "Searchable title, structured chapters, visual walkthrough, recap, and next-step CTA.",
            "interaction_style": "Calm, expert, demonstrative, and credibility-led.",
            "cadence": "Lower frequency evergreen videos supported by Shorts extracted from high-friction moments.",
            "success_signal": "Search impressions, retention, comments with use cases, saves, and returning viewers.",
            "avoid": ["thin Shorts-only strategy", "vague travel inspiration", "unsupported claims", "overly salesy demo"],
            "recommended_actions": [
                "Promote high-repeat questions into evergreen explainers.",
                "Use Shorts to test hooks before long-form production.",
                "Deposit comments into the Question Inbox for future scripts.",
            ],
        },
    }

    def __init__(self, root: str | Path = "runtime/strategy_personality") -> None:
        self.root = Path(root)
        self.state_path = self.root / "strategy_personality_state.json"
        self.matrix_path = self.root / "strategy_personality_matrix.json"

    def build_strategy(self, platform: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        key = platform.lower()
        if key not in self.STRATEGIES:
            raise ValueError(f"Unsupported strategy personality platform: {platform}")
        context = context or {}
        profile = self.STRATEGIES[key]
        pain_point = context.get("pain_point", "Tokyo transport anxiety")
        workspace = context.get("workspace", "JAG-LAB")
        strategy = {
            **profile,
            "strategy_id": f"strategy_personality_{key}",
            "workspace": workspace,
            "industry_pack": context.get("industry_pack", "Travel Pack / Lab"),
            "market": context.get("market", "Japan"),
            "current_pain_point": pain_point,
            "sample_strategy": self._sample_strategy(key, pain_point),
            "human_review_status": "needs_human_review",
            "created_at": utc_now_iso(),
        }
        return strategy

    def build_all(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        strategies = [self.build_strategy(platform, context) for platform in self.STRATEGIES]
        payload = {
            "updated_at": utc_now_iso(),
            "workspace": (context or {}).get("workspace", "JAG-LAB"),
            "strategyPersonalityMatrix": strategies,
            "platformOperatingPhilosophies": {
                item["platform"]: item["operating_philosophy"] for item in strategies
            },
            "strategyPersonalityFeed": [
                {
                    "platform": item["platform"],
                    "status": "ready_for_review",
                    "philosophy": item["operating_philosophy"],
                    "goal": item["strategy_goal"],
                    "action": item["sample_strategy"],
                    "success_signal": item["success_signal"],
                }
                for item in strategies
            ],
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return self.build_all()

    def persist(self, payload: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        self.state_path.write_text(text, encoding="utf-8")
        self.matrix_path.write_text(
            json.dumps(payload["strategyPersonalityMatrix"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _sample_strategy(platform: str, pain_point: str) -> str:
        samples = {
            "reddit": f"Write a detailed, non-promotional answer that solves '{pain_point}' with route steps and caveats.",
            "tiktok": f"Create a short hook showing '{pain_point}' as a visual moment and ask viewers to save the fix.",
            "x": f"Post a concise observation about '{pain_point}' and invite replies with similar travel friction.",
            "youtube": f"Plan an evergreen walkthrough video that demonstrates how to avoid '{pain_point}' in real context.",
        }
        return samples[platform]
