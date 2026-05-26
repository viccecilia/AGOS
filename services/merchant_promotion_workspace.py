"""Merchant homepage promotion workspace for pluggable growth campaigns."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/merchant_promotion_workspace")


DEFAULT_MERCHANTS = [
    {
        "workspace_id": "jag_app_growth",
        "merchant_name": "Japan AI Guide App",
        "merchant_type": "travel_app",
        "homepage_url": "https://japan-ai-guide.example/pending-official-url",
        "homepage_status": "placeholder_needs_official_url",
        "industry_pack": "Travel Pack",
        "target_markets": ["Japan", "US", "Europe", "Korea", "Taiwan", "Southeast Asia", "China"],
        "target_platforms": ["Reddit", "TikTok", "Instagram", "X", "YouTube", "Threads", "SEO", "Xiaohongshu"],
        "core_value_props": [
            "Japan trip planning support",
            "transport and airport-transfer anxiety reduction",
            "family and luggage-heavy trip planning",
            "seasonal Japan travel guidance",
        ],
        "target_users": ["first-time Japan travelers", "family travelers", "luggage-heavy travelers", "late-arrival travelers"],
        "forbidden_claims": ["guaranteed booking", "official government guide", "automatic platform replies", "unverified discounts"],
        "promotion_goal": "Promote the social homepage by solving Japan travel mobility questions first, then softly guiding users to the homepage.",
        "tone_guardrails": ["helpful", "specific", "not hard-selling", "transparent sample-only evidence"],
    },
    {
        "workspace_id": "home_appliance_demo",
        "merchant_name": "Home Appliance Demo Store",
        "merchant_type": "home_appliance",
        "homepage_url": "pending_setup",
        "homepage_status": "placeholder_demo_isolated",
        "industry_pack": "Home Appliance Pack",
        "target_markets": ["Japan", "US"],
        "target_platforms": ["Reddit", "YouTube", "SEO"],
        "core_value_props": ["home appliance comparison", "buying guidance", "maintenance education"],
        "target_users": ["new homeowners", "small-apartment renters"],
        "forbidden_claims": ["medical benefit claims", "guaranteed savings", "fake reviews"],
        "promotion_goal": "Isolation sample only; must not receive JAG travel questions or answers.",
        "tone_guardrails": ["practical", "evidence-based", "not travel-oriented"],
    },
]


SAMPLE_SOCIAL_MATRIX = [
    {"platform": "TikTok", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
    {"platform": "Instagram", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
    {"platform": "X", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
    {"platform": "YouTube", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
    {"platform": "Reddit", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
    {"platform": "Threads", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
    {"platform": "SEO", "homepage_url": "pending_official_website", "status": "pending_setup", "write_permission": False},
    {"platform": "Xiaohongshu", "homepage_url": "needs_account_url", "status": "pending_setup", "write_permission": False},
]


SAMPLE_PROBLEMS = [
    {
        "problem_id": "PROMO-PROB-001",
        "workspace_id": "jag_app_growth",
        "platform": "Reddit",
        "market": "US",
        "language": "en",
        "user_problem": "We land at Haneda late with two kids and big luggage. Is train still realistic?",
        "pain_points": ["late arrival", "family luggage", "airport transfer anxiety"],
        "intent": "airport_transfer",
        "homepage_fit_score": 88,
        "source_type": "local_sample",
    },
    {
        "problem_id": "PROMO-PROB-002",
        "workspace_id": "jag_app_growth",
        "platform": "Xiaohongshu",
        "market": "China",
        "language": "zh-CN",
        "user_problem": "春节去东京一家四口行李很多，机场到酒店怎么安排比较稳？",
        "pain_points": ["Chinese New Year", "family luggage", "language support"],
        "intent": "family_airport_transfer",
        "homepage_fit_score": 91,
        "source_type": "local_sample",
    },
    {
        "problem_id": "PROMO-PROB-003",
        "workspace_id": "jag_app_growth",
        "platform": "TikTok",
        "market": "Taiwan",
        "language": "zh-TW",
        "user_problem": "京都賞楓帶長輩和行李，搭公車會不會太累？",
        "pain_points": ["autumn leaves", "elderly support", "crowded buses"],
        "intent": "private_charter",
        "homepage_fit_score": 84,
        "source_type": "local_sample",
    },
    {
        "problem_id": "PROMO-PROB-004",
        "workspace_id": "jag_app_growth",
        "platform": "YouTube",
        "market": "Europe",
        "language": "en",
        "user_problem": "Is a Mount Fuji day trip by public transport too rushed in autumn?",
        "pain_points": ["scattered sightseeing routes", "time pressure", "autumn route planning"],
        "intent": "sightseeing_route",
        "homepage_fit_score": 79,
        "source_type": "local_sample",
    },
    {
        "problem_id": "PROMO-PROB-005",
        "workspace_id": "home_appliance_demo",
        "platform": "Reddit",
        "market": "US",
        "language": "en",
        "user_problem": "Is an air fryer useful in a tiny apartment?",
        "pain_points": ["small kitchen", "product comparison"],
        "intent": "buying_guidance",
        "homepage_fit_score": 72,
        "source_type": "isolation_sample",
    },
]


class MerchantPromotionWorkspace:
    """Build local, human-gated merchant homepage promotion workflow data."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.profile_path = self.output_dir / "merchant_profiles.json"
        self.social_path = self.output_dir / "merchant_social_matrix.json"
        self.problem_path = self.output_dir / "homepage_problem_opportunities.json"
        self.strategy_path = self.output_dir / "answer_to_homepage_strategy.json"
        self.queue_path = self.output_dir / "promotion_review_queue.json"
        self.summary_path = self.output_dir / "merchant_promotion_summary.json"

    def build(self, merchants: list[dict[str, Any]] | None = None, problems: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        profiles = self._profiles(merchants or DEFAULT_MERCHANTS)
        social = self._social_matrix(profiles)
        opportunities = self._problem_opportunities(problems or SAMPLE_PROBLEMS, profiles)
        strategies = self._strategies(opportunities, profiles)
        review_queue = self._review_queue(strategies)
        summary = self._summary(profiles, social, opportunities, strategies, review_queue)
        payload = {
            "report_id": "MERCHANT_HOMEPAGE_PROMOTION_WORKSPACE",
            "created_at": utc_now_iso(),
            "status": "merchant_promotion_workspace_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_PLUGIN",
            "merchantProfiles": profiles,
            "merchantSocialMatrix": social,
            "homepageProblemOpportunities": opportunities,
            "answerToHomepageStrategy": strategies,
            "promotionReviewQueue": review_queue,
            "merchantPromotionSummary": summary,
            "safetyBoundary": "Merchant Promotion Workspace generates local, human-gated homepage promotion recommendations only. It does not scrape login-only data, auto-post, auto-reply, auto-DM, contact customers, impersonate users, create accounts, or call platform write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "MERCHANT_HOMEPAGE_PROMOTION_WORKSPACE",
                "status": "merchant_promotion_workspace_ready",
                "merchantProfiles": json.loads(self.profile_path.read_text(encoding="utf-8")) if self.profile_path.exists() else [],
                "merchantSocialMatrix": json.loads(self.social_path.read_text(encoding="utf-8")) if self.social_path.exists() else [],
                "homepageProblemOpportunities": json.loads(self.problem_path.read_text(encoding="utf-8")) if self.problem_path.exists() else [],
                "answerToHomepageStrategy": json.loads(self.strategy_path.read_text(encoding="utf-8")) if self.strategy_path.exists() else [],
                "promotionReviewQueue": json.loads(self.queue_path.read_text(encoding="utf-8")) if self.queue_path.exists() else [],
                "merchantPromotionSummary": json.loads(self.summary_path.read_text(encoding="utf-8")),
            }
        return self.build()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(json.dumps(payload["merchantProfiles"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.social_path.write_text(json.dumps(payload["merchantSocialMatrix"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.problem_path.write_text(json.dumps(payload["homepageProblemOpportunities"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.strategy_path.write_text(json.dumps(payload["answerToHomepageStrategy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.queue_path.write_text(json.dumps(payload["promotionReviewQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["merchantPromotionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _profiles(merchants: list[dict[str, Any]]) -> list[dict[str, Any]]:
        profiles = []
        for item in merchants:
            profile = dict(item)
            profile["plugin_status"] = "active" if item["workspace_id"] == "jag_app_growth" else "isolation_demo"
            profile["human_review_required"] = True
            profile["auto_post_enabled"] = False
            profile["auto_reply_enabled"] = False
            profile["auto_dm_enabled"] = False
            profile["write_api_enabled"] = False
            profile["workspace_isolation_required"] = True
            profile["updated_at"] = utc_now_iso()
            profiles.append(profile)
        return profiles

    @staticmethod
    def _social_matrix(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for profile in profiles:
            for item in SAMPLE_SOCIAL_MATRIX:
                if item["platform"] not in profile.get("target_platforms", []):
                    continue
                row = dict(item)
                row["workspace_id"] = profile["workspace_id"]
                row["merchant_name"] = profile["merchant_name"]
                row["today_task"] = "Find problems, draft answers, and softly guide to homepage after human review."
                row["review_status"] = "needs_human_review"
                row["risk_status"] = "low" if profile["workspace_id"] == "jag_app_growth" else "isolation_demo"
                row["auto_post_enabled"] = False
                row["auto_reply_enabled"] = False
                row["auto_dm_enabled"] = False
                rows.append(row)
        return rows

    @staticmethod
    def _problem_opportunities(problems: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_workspace = {item["workspace_id"]: item for item in profiles}
        opportunities = []
        for item in problems:
            profile = by_workspace[item["workspace_id"]]
            is_active = profile["workspace_id"] == "jag_app_growth"
            opportunities.append(
                {
                    **item,
                    "opportunity_id": item["problem_id"].replace("PROMO-PROB", "PROMO-OPP"),
                    "merchant_name": profile["merchant_name"],
                    "homepage_url": profile["homepage_url"],
                    "match_reason": f"Problem matches {profile['merchant_name']} value props: {', '.join(profile.get('core_value_props', [])[:2])}.",
                    "recommended_next_step": "draft_answer_branch" if is_active and item["homepage_fit_score"] >= 75 else "monitor_or_isolation_check",
                    "workspace_isolated": True,
                    "sample_data_only": True,
                    "needs_human_review": True,
                    "allowed_to_contact_user": False,
                    "allowed_to_auto_reply": False,
                    "allowed_to_auto_post": False,
                }
            )
        return opportunities

    @staticmethod
    def _strategies(opportunities: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_workspace = {item["workspace_id"]: item for item in profiles}
        strategies = []
        for index, item in enumerate(opportunities, start=1):
            profile = by_workspace[item["workspace_id"]]
            active = item["workspace_id"] == "jag_app_growth"
            soft_cta = "If you want a structured Japan plan, check the Japan AI Guide homepage." if active else "No CTA for isolation demo."
            reply = MerchantPromotionWorkspace._draft_reply(item, soft_cta, active)
            strategies.append(
                {
                    "strategy_id": f"HOME-PROMO-STRATEGY-{index:03d}",
                    "workspace_id": item["workspace_id"],
                    "merchant_name": item["merchant_name"],
                    "platform": item["platform"],
                    "market": item["market"],
                    "problem_id": item["problem_id"],
                    "promotion_angle": MerchantPromotionWorkspace._promotion_angle(item),
                    "reply_draft": reply,
                    "content_topic": MerchantPromotionWorkspace._content_topic(item),
                    "soft_cta": soft_cta,
                    "homepage_url": profile["homepage_url"],
                    "risk_level": "medium" if active else "isolation_demo",
                    "review_status": "needs_human_review",
                    "human_review_required": True,
                    "auto_post_enabled": False,
                    "auto_reply_enabled": False,
                    "auto_dm_enabled": False,
                    "write_api_enabled": False,
                    "why_this_promotes_homepage": "It solves the user's question first, then offers a soft homepage path without hard-selling.",
                }
            )
        return strategies

    @staticmethod
    def _review_queue(strategies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "review_id": f"HOME-PROMO-REVIEW-{index:03d}",
                "strategy_id": item["strategy_id"],
                "workspace_id": item["workspace_id"],
                "merchant_name": item["merchant_name"],
                "platform": item["platform"],
                "review_type": "homepage_promotion_reply_or_content",
                "review_status": "needs_human_review",
                "must_check": ["tone", "platform_rules", "soft_cta", "no_hard_sell", "workspace_isolation"],
                "auto_execution_allowed": False,
                "decision_options": ["approve", "reject", "modify", "postpone"],
            }
            for index, item in enumerate(strategies, start=1)
        ]

    @staticmethod
    def _summary(
        profiles: list[dict[str, Any]],
        social: list[dict[str, Any]],
        opportunities: list[dict[str, Any]],
        strategies: list[dict[str, Any]],
        review_queue: list[dict[str, Any]],
    ) -> dict[str, Any]:
        active = [item for item in opportunities if item["workspace_id"] == "jag_app_growth"]
        platform_counts = Counter(item["platform"] for item in active)
        market_counts = Counter(item["market"] for item in active)
        return {
            "workspace_plugin_ready": True,
            "merchant_profiles": len(profiles),
            "active_workspace": "jag_app_growth",
            "active_merchant": "Japan AI Guide App",
            "social_homepage_slots": len([item for item in social if item["workspace_id"] == "jag_app_growth"]),
            "problem_opportunities": len(opportunities),
            "active_workspace_opportunities": len(active),
            "promotion_strategies": len(strategies),
            "review_queue_items": len(review_queue),
            "top_platforms": platform_counts.most_common(),
            "top_markets": market_counts.most_common(),
            "all_actions_human_gated": True,
            "auto_post_enabled": False,
            "auto_reply_enabled": False,
            "auto_dm_enabled": False,
            "write_api_enabled": False,
            "workspace_isolation_checked": True,
            "home_appliance_demo_isolated": True,
        }

    @staticmethod
    def _draft_reply(item: dict[str, Any], soft_cta: str, active: bool) -> str:
        if not active:
            return "Isolation demo only. Do not mix this with Japan AI Guide promotion."
        return (
            f"For {item['intent']}, I would first reduce the transfer risk around: "
            f"{', '.join(item.get('pain_points', [])[:3])}. Compare train complexity, luggage load, arrival time, "
            f"and whether your group includes kids or elderly travelers. {soft_cta}"
        )

    @staticmethod
    def _content_topic(item: dict[str, Any]) -> str:
        return f"{item['platform']} topic: How to handle {item['intent']} in Japan when {', '.join(item.get('pain_points', [])[:2])} matters"

    @staticmethod
    def _promotion_angle(item: dict[str, Any]) -> str:
        return f"Solve {item['intent']} anxiety before mentioning the homepage."


if __name__ == "__main__":
    result = MerchantPromotionWorkspace().build()
    print(json.dumps({"status": result["status"], "summary": result["merchantPromotionSummary"]}, indent=2))
