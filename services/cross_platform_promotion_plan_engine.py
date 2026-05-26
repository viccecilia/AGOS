"""Cross-platform promotion planning for human-gated homepage growth."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.answer_to_homepage_draft_engine import AnswerToHomepageDraftEngine
from services.runtime_persistence import utc_now_iso


DEFAULT_INPUT_PATH = Path("runtime/answer_to_homepage_drafts/answer_drafts.json")
DEFAULT_OUTPUT_DIR = Path("runtime/cross_platform_promotion_plan")

PLATFORM_PLAN_CONFIG = {
    "Reddit": {
        "content_format": "reply",
        "hook": "Practical tradeoff answer before any recommendation",
        "tone": "Specific, transparent, no hard sell",
        "priority": 92,
        "risk_level": "medium",
    },
    "TikTok": {
        "content_format": "short_video_hook",
        "hook": "Do not choose Japan transport by price alone",
        "tone": "Short, visual, emotionally clear",
        "priority": 80,
        "risk_level": "medium",
    },
    "Instagram": {
        "content_format": "carousel_idea",
        "hook": "Save this Japan arrival checklist",
        "tone": "Visual, concise, checklist-oriented",
        "priority": 72,
        "risk_level": "low",
    },
    "X": {
        "content_format": "short_post",
        "hook": "Japan travel mistake: station-to-station time is not door-to-door time",
        "tone": "Compact, opinionated, practical",
        "priority": 70,
        "risk_level": "medium",
    },
    "YouTube": {
        "content_format": "short_topic",
        "hook": "Airport-to-hotel planning mistakes in Japan",
        "tone": "Structured, educational, route-focused",
        "priority": 76,
        "risk_level": "low",
    },
    "Threads": {
        "content_format": "conversation_post",
        "hook": "A simple way to decide train vs transfer in Japan",
        "tone": "Warm, conversational, quick to scan",
        "priority": 68,
        "risk_level": "low",
    },
    "SEO": {
        "content_format": "article_idea",
        "hook": "Japan airport transfer vs train: how to decide",
        "tone": "Evergreen, search-friendly, detailed",
        "priority": 84,
        "risk_level": "low",
    },
    "Xiaohongshu": {
        "content_format": "note_angle",
        "hook": "日本机场到酒店别只看交通费",
        "tone": "Lifestyle checklist, practical, not exaggerated",
        "priority": 82,
        "risk_level": "medium",
    },
}


class CrossPlatformPromotionPlanEngine:
    """Turn answer drafts into cross-platform, human-gated promotion plans."""

    def __init__(
        self,
        input_path: str | Path = DEFAULT_INPUT_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.plans_path = self.output_dir / "promotion_plans.json"
        self.calendar_path = self.output_dir / "content_calendar_draft.json"
        self.priority_path = self.output_dir / "platform_priority.json"
        self.queue_path = self.output_dir / "promotion_plan_review_queue.json"
        self.summary_path = self.output_dir / "cross_platform_promotion_summary.json"

    def build(self) -> dict[str, Any]:
        drafts = self._load_drafts()
        plans = self._plans(drafts)
        content_calendar = self._content_calendar(plans)
        platform_priority = self._platform_priority(plans)
        review_queue = self._review_queue(plans)
        summary = self._summary(plans, content_calendar, platform_priority, review_queue)
        payload = {
            "report_id": "CROSS_PLATFORM_PROMOTION_PLAN_ENGINE",
            "created_at": utc_now_iso(),
            "status": "cross_platform_promotion_plan_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "promotionPlans": plans,
            "contentCalendarDraft": content_calendar,
            "platformPriority": platform_priority,
            "promotionPlanReviewQueue": review_queue,
            "crossPlatformPromotionSummary": summary,
            "safetyBoundary": "Cross-platform promotion plans are local planning artifacts only. They require human review and cannot auto-publish, schedule, DM, operate real accounts, or call platform write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "CROSS_PLATFORM_PROMOTION_PLAN_ENGINE",
                "status": "cross_platform_promotion_plan_ready",
                "promotionPlans": json.loads(self.plans_path.read_text(encoding="utf-8")) if self.plans_path.exists() else [],
                "contentCalendarDraft": json.loads(self.calendar_path.read_text(encoding="utf-8")) if self.calendar_path.exists() else [],
                "platformPriority": json.loads(self.priority_path.read_text(encoding="utf-8")) if self.priority_path.exists() else [],
                "promotionPlanReviewQueue": json.loads(self.queue_path.read_text(encoding="utf-8")) if self.queue_path.exists() else [],
                "crossPlatformPromotionSummary": json.loads(self.summary_path.read_text(encoding="utf-8")),
            }
        return self.build()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plans_path.write_text(json.dumps(payload["promotionPlans"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.calendar_path.write_text(json.dumps(payload["contentCalendarDraft"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.priority_path.write_text(json.dumps(payload["platformPriority"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.queue_path.write_text(json.dumps(payload["promotionPlanReviewQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["crossPlatformPromotionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_drafts(self) -> list[dict[str, Any]]:
        if not self.input_path.exists():
            AnswerToHomepageDraftEngine().build()
        data = json.loads(self.input_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("answer_drafts.json must contain a list")
        return data

    def _plans(self, drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        plans = []
        for draft in drafts:
            for platform, config in PLATFORM_PLAN_CONFIG.items():
                plans.append(
                    {
                        "plan_id": f"PROMO-PLAN-{len(plans) + 1:03d}",
                        "draft_id": draft.get("draft_id", ""),
                        "platform": platform,
                        "content_format": config["content_format"],
                        "hook": self._hook(config["hook"], draft),
                        "core_message": self._core_message(platform, draft),
                        "soft_cta": draft.get("soft_cta", ""),
                        "homepage_reference": draft.get("homepage_reference", "pending_official_homepage"),
                        "platform_tone": config["tone"],
                        "risk_level": self._risk_level(config["risk_level"], draft),
                        "review_status": "needs_human_review",
                        "auto_publish_allowed": False,
                        "auto_schedule_allowed": False,
                        "auto_reply_allowed": False,
                        "real_platform_write_api_called": False,
                        "market": draft.get("market", ""),
                        "merchant_name": draft.get("merchant_name", ""),
                        "workspace_id": draft.get("workspace_id", ""),
                        "why_platform_fit": self._why_platform_fit(platform, draft),
                    }
                )
        return plans

    @staticmethod
    def _hook(base_hook: str, draft: dict[str, Any]) -> str:
        if draft.get("market") == "China" and "Xiaohongshu" in draft.get("platform", ""):
            return "日本交通别只看便宜，先看行李和换乘"
        return base_hook

    @staticmethod
    def _core_message(platform: str, draft: dict[str, Any]) -> str:
        answer = draft.get("direct_answer", "")
        steps = draft.get("helpful_steps", [])[:3]
        if platform == "TikTok":
            return f"Show the mistake visually: {answer} Then show 3 quick checks: {'; '.join(steps)}."
        if platform == "Instagram":
            return f"Carousel structure: problem, route risk, luggage check, fallback option, soft homepage reference. Core answer: {answer}"
        if platform == "SEO":
            return f"Article angle: answer the travel question with door-to-door criteria, luggage risk, and fallback planning. Core answer: {answer}"
        return f"{answer} Key steps: {'; '.join(steps)}."

    @staticmethod
    def _risk_level(base_risk: str, draft: dict[str, Any]) -> str:
        if draft.get("hard_sell_risk") == "medium":
            return "medium"
        if draft.get("forbidden_claim_check", {}).get("status") != "passed":
            return "high"
        return base_risk

    @staticmethod
    def _why_platform_fit(platform: str, draft: dict[str, Any]) -> str:
        mapping = {
            "Reddit": "The source problem can be answered with practical tradeoffs and transparent caveats.",
            "TikTok": "The pain point can become a short before/after planning mistake hook.",
            "Instagram": "The steps can be turned into a saveable checklist carousel.",
            "X": "The core insight can be compressed into one practical warning.",
            "YouTube": "The answer can become an educational short topic.",
            "Threads": "The question can start a lightweight conversational planning thread.",
            "SEO": "The answer targets recurring search intent and evergreen planning questions.",
            "Xiaohongshu": "The checklist format fits travel planning notes and soft lifestyle guidance.",
        }
        return mapping.get(platform, "Platform fit requires human review.")

    @staticmethod
    def _content_calendar(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        calendar = []
        day_slot = 1
        for plan in plans:
            if plan["platform"] not in {"Reddit", "TikTok", "Instagram", "SEO", "Xiaohongshu"}:
                continue
            calendar.append(
                {
                    "calendar_id": f"CAL-{len(calendar) + 1:03d}",
                    "day_slot": f"draft_day_{day_slot}",
                    "platform": plan["platform"],
                    "plan_id": plan["plan_id"],
                    "content_format": plan["content_format"],
                    "hook": plan["hook"],
                    "review_status": "needs_human_review",
                    "auto_publish_allowed": False,
                }
            )
            day_slot = 1 + (day_slot % 7)
        return calendar

    @staticmethod
    def _platform_priority(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts = Counter(plan["platform"] for plan in plans)
        rows = []
        for platform, config in PLATFORM_PLAN_CONFIG.items():
            rows.append(
                {
                    "platform": platform,
                    "plan_count": counts.get(platform, 0),
                    "priority_score": config["priority"],
                    "priority_reason": config["hook"],
                    "review_status": "needs_human_review",
                    "auto_publish_allowed": False,
                }
            )
        return sorted(rows, key=lambda row: (-row["priority_score"], row["platform"]))

    @staticmethod
    def _review_queue(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "review_id": f"PROMO-REVIEW-{index:03d}",
                "plan_id": plan["plan_id"],
                "draft_id": plan["draft_id"],
                "platform": plan["platform"],
                "content_format": plan["content_format"],
                "risk_level": plan["risk_level"],
                "review_status": "needs_human_review",
                "decision_options": ["approve", "reject", "modify", "postpone"],
                "auto_publish_allowed": False,
            }
            for index, plan in enumerate(plans, start=1)
        ]

    @staticmethod
    def _summary(
        plans: list[dict[str, Any]],
        content_calendar: list[dict[str, Any]],
        platform_priority: list[dict[str, Any]],
        review_queue: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "cross_platform_promotion_ready": True,
            "plan_count": len(plans),
            "platform_count": len({plan["platform"] for plan in plans}),
            "content_calendar_items": len(content_calendar),
            "review_queue_count": len(review_queue),
            "top_platforms": [row["platform"] for row in platform_priority[:5]],
            "all_plans_need_human_review": all(plan["review_status"] == "needs_human_review" for plan in plans),
            "auto_publish_allowed": any(plan["auto_publish_allowed"] for plan in plans),
            "write_api_called": any(plan["real_platform_write_api_called"] for plan in plans),
            "recommended_next_round": "ROUND-GROWTH-PLUGIN-006 Promotion Review Queue UI",
        }


if __name__ == "__main__":
    result = CrossPlatformPromotionPlanEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["crossPlatformPromotionSummary"]}, indent=2))
