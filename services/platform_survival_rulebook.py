"""Platform survival rules for human-gated promotion actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.external_action_sandbox import ExternalActionSandbox
from services.promotion_review_center import PromotionReviewCenter
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/platform_survival_rulebook")
SUPPORTED_PLATFORMS = ["Reddit", "X", "TikTok", "Instagram", "YouTube", "Threads"]


class PlatformSurvivalRulebook:
    """Downgrade risky promotion actions before they become external recommendations."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.rules_path = self.output_dir / "platform_survival_rules.json"
        self.review_path = self.output_dir / "governed_promotion_review_items.json"
        self.sandbox_path = self.output_dir / "governed_external_action_queue.json"
        self.risk_path = self.output_dir / "platform_survival_risk_review.json"
        self.report_path = self.output_dir / "PLATFORM_SURVIVAL_RULEBOOK_REPORT.json"

    def build(
        self,
        review_items: list[dict[str, Any]] | None = None,
        external_actions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        rules = self.rules()
        if review_items is None:
            review_items = PromotionReviewCenter().state().get("promotionReviewItems", [])
        if external_actions is None:
            external_actions = ExternalActionSandbox().state().get("externalActionQueue", [])
        governed_reviews = [self._govern_review_item(item, rules) for item in review_items]
        governed_actions = [self._govern_external_action(item, rules) for item in external_actions]
        risk_review = self._risk_review(governed_reviews, governed_actions)
        report = {
            "report_id": "PLATFORM_SURVIVAL_RULEBOOK_REPORT",
            "created_at": utc_now_iso(),
            "status": "platform_survival_rulebook_ready",
            "phase": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "platformSurvivalRules": rules,
            "governedPromotionReviewItems": governed_reviews,
            "governedExternalActionQueue": governed_actions,
            "platformSurvivalRiskReview": risk_review,
            "platformSurvivalRulebookSummary": self._summary(governed_reviews, governed_actions, risk_review),
            "safetyBoundary": "Rulebook only downgrades, rejects, or requires review for risky actions. It does not publish, reply, DM, follow, like, log in, crawl, or call platform write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return {
                "report_id": "PLATFORM_SURVIVAL_RULEBOOK_REPORT",
                "status": "platform_survival_rulebook_ready",
                "platformSurvivalRules": self._read_json(self.rules_path, {}),
                "governedPromotionReviewItems": self._read_json(self.review_path, []),
                "governedExternalActionQueue": self._read_json(self.sandbox_path, []),
                "platformSurvivalRiskReview": self._read_json(self.risk_path, {}),
                "platformSurvivalRulebookSummary": self._read_json(self.report_path, {}).get("platformSurvivalRulebookSummary", {}),
            }
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rules_path.write_text(json.dumps(report["platformSurvivalRules"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_path.write_text(json.dumps(report["governedPromotionReviewItems"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.sandbox_path.write_text(json.dumps(report["governedExternalActionQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_path.write_text(json.dumps(report["platformSurvivalRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def rules() -> dict[str, Any]:
        return {
            "Reddit": {
                "community_risk": "high",
                "posting_cadence": "low_frequency_answer_first",
                "forbidden_patterns": ["buy now", "limited offer", "guaranteed", "official partner", "dm me", "promo code"],
                "safe_cta": ["optional reference", "if useful", "check the profile only after answering the question"],
                "default_action": "review_required",
                "strong_marketing_allowed_by_default": False,
            },
            "X": {
                "community_risk": "medium",
                "posting_cadence": "moderate_observation_first",
                "forbidden_patterns": ["guaranteed", "mass reply", "auto dm", "follow for follow"],
                "safe_cta": ["short optional link", "transparent source note"],
                "default_action": "review_required",
                "strong_marketing_allowed_by_default": False,
            },
            "TikTok": {
                "community_risk": "medium",
                "posting_cadence": "creative_hook_no_spam",
                "forbidden_patterns": ["clickbait", "fake urgency", "guaranteed result", "spam comments"],
                "safe_cta": ["save this", "profile reference after useful tip"],
                "default_action": "review_required",
                "strong_marketing_allowed_by_default": False,
            },
            "Instagram": {
                "community_risk": "medium",
                "posting_cadence": "visual_value_first",
                "forbidden_patterns": ["fake scarcity", "auto dm", "mass tagging", "guaranteed"],
                "safe_cta": ["profile has checklist", "soft reference in caption"],
                "default_action": "review_required",
                "strong_marketing_allowed_by_default": False,
            },
            "YouTube": {
                "community_risk": "medium",
                "posting_cadence": "evergreen_helpful",
                "forbidden_patterns": ["misleading title", "guaranteed", "comment spam", "fake authority"],
                "safe_cta": ["description reference", "optional guide link"],
                "default_action": "review_required",
                "strong_marketing_allowed_by_default": False,
            },
            "Threads": {
                "community_risk": "medium",
                "posting_cadence": "conversation_first",
                "forbidden_patterns": ["mass reply", "hard sell", "guaranteed", "auto follow"],
                "safe_cta": ["optional profile reference", "non-promotional thread reply"],
                "default_action": "review_required",
                "strong_marketing_allowed_by_default": False,
            },
        }

    def _govern_review_item(self, item: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
        platform = self._platform(item.get("platform", ""))
        rule = rules.get(platform, self._fallback_rule())
        text = self._text(item, ["item_summary", "soft_cta", "core_message", "suggested_action"])
        forbidden_hits = self._forbidden_hits(text, rule)
        community_only_risk = platform == "Reddit" and self._looks_promotional(text)
        governance_status = self._status(forbidden_hits, community_only_risk, item.get("risk_level", "medium"))
        return {
            **item,
            "platform_survival_platform": platform,
            "platform_survival_status": governance_status,
            "survival_review_required": governance_status in {"review_required", "rejected"},
            "survival_rejected": governance_status == "rejected",
            "forbidden_pattern_hits": forbidden_hits,
            "safe_cta_recommendation": rule["safe_cta"][0],
            "posting_cadence": rule["posting_cadence"],
            "community_risk": rule["community_risk"],
            "strong_marketing_allowed_by_default": rule["strong_marketing_allowed_by_default"],
            "default_strong_marketing_blocked": community_only_risk,
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "external_execution_allowed": False,
            "write_api_called": False,
            "governance_reason": self._reason(forbidden_hits, community_only_risk, rule),
        }

    def _govern_external_action(self, item: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
        platform = self._platform(item.get("target_platform", ""))
        rule = rules.get(platform, self._fallback_rule())
        text = self._text(item, ["suggested_action", "why_suggested", "blocked_reason"])
        forbidden_hits = self._forbidden_hits(text, rule)
        community_only_risk = platform == "Reddit" and self._looks_promotional(text)
        governance_status = self._status(forbidden_hits, community_only_risk, item.get("risk_level", "medium"))
        status = "rejected" if governance_status == "rejected" else "waiting_human_approval"
        return {
            **item,
            "status": status,
            "platform_survival_platform": platform,
            "platform_survival_status": governance_status,
            "survival_review_required": True,
            "survival_rejected": governance_status == "rejected",
            "forbidden_pattern_hits": forbidden_hits,
            "safe_cta_recommendation": rule["safe_cta"][0],
            "posting_cadence": rule["posting_cadence"],
            "community_risk": rule["community_risk"],
            "strong_marketing_allowed_by_default": rule["strong_marketing_allowed_by_default"],
            "default_strong_marketing_blocked": community_only_risk,
            "human_gate_status": "required",
            "external_execution_allowed": False,
            "write_api_call_allowed": False,
            "write_api_call_attempted": False,
            "governance_reason": self._reason(forbidden_hits, community_only_risk, rule),
        }

    @staticmethod
    def _platform(value: str) -> str:
        normalized = (value or "").strip().lower()
        mapping = {
            "reddit": "Reddit",
            "x": "X",
            "twitter": "X",
            "tiktok": "TikTok",
            "instagram": "Instagram",
            "youtube": "YouTube",
            "threads": "Threads",
        }
        return mapping.get(normalized, value or "unknown")

    @staticmethod
    def _fallback_rule() -> dict[str, Any]:
        return {
            "community_risk": "medium",
            "posting_cadence": "review_first",
            "forbidden_patterns": ["guaranteed", "buy now", "spam", "auto dm"],
            "safe_cta": ["optional reference after useful answer"],
            "default_action": "review_required",
            "strong_marketing_allowed_by_default": False,
        }

    @staticmethod
    def _text(item: dict[str, Any], fields: list[str]) -> str:
        return " ".join(str(item.get(field, "")) for field in fields).lower()

    @staticmethod
    def _forbidden_hits(text: str, rule: dict[str, Any]) -> list[str]:
        return [pattern for pattern in rule["forbidden_patterns"] if pattern in text]

    @staticmethod
    def _looks_promotional(text: str) -> bool:
        return any(term in text for term in ["homepage", "profile", "link", "buy", "download", "official", "dm me", "promo"])

    @staticmethod
    def _status(forbidden_hits: list[str], community_only_risk: bool, risk_level: str) -> str:
        if forbidden_hits:
            return "rejected"
        if community_only_risk or risk_level == "high":
            return "review_required"
        return "safe_with_review"

    @staticmethod
    def _reason(forbidden_hits: list[str], community_only_risk: bool, rule: dict[str, Any]) -> str:
        if forbidden_hits:
            return f"Rejected because forbidden patterns were detected: {', '.join(forbidden_hits)}."
        if community_only_risk:
            return "Downgraded because community platforms cannot default to strong homepage promotion."
        return f"Allowed only with human review using cadence {rule['posting_cadence']} and safe CTA: {rule['safe_cta'][0]}."

    @staticmethod
    def _risk_review(reviews: list[dict[str, Any]], actions: list[dict[str, Any]]) -> dict[str, Any]:
        combined = reviews + actions
        return {
            "risk_review_ready": True,
            "total_items": len(combined),
            "review_required_count": len([item for item in combined if item.get("platform_survival_status") == "review_required"]),
            "rejected_count": len([item for item in combined if item.get("platform_survival_status") == "rejected"]),
            "safe_with_review_count": len([item for item in combined if item.get("platform_survival_status") == "safe_with_review"]),
            "reddit_strong_marketing_blocked": any(
                item.get("platform_survival_platform") == "Reddit" and item.get("default_strong_marketing_blocked")
                for item in combined
            ),
            "auto_publish_allowed": any(item.get("auto_publish_allowed") for item in combined),
            "auto_reply_allowed": any(item.get("auto_reply_allowed") for item in combined),
            "external_execution_allowed": any(item.get("external_execution_allowed") for item in combined),
            "write_api_called": any(item.get("write_api_called") or item.get("write_api_call_attempted") for item in combined),
        }

    @staticmethod
    def _summary(reviews: list[dict[str, Any]], actions: list[dict[str, Any]], risk_review: dict[str, Any]) -> dict[str, Any]:
        return {
            "platform_survival_rulebook_ready": True,
            "supported_platforms": SUPPORTED_PLATFORMS,
            "governed_review_item_count": len(reviews),
            "governed_external_action_count": len(actions),
            "review_required_count": risk_review["review_required_count"],
            "rejected_count": risk_review["rejected_count"],
            "reddit_strong_marketing_blocked": risk_review["reddit_strong_marketing_blocked"],
            "high_risk_downgraded_or_rejected": risk_review["review_required_count"] + risk_review["rejected_count"] > 0,
            "auto_publish_allowed": risk_review["auto_publish_allowed"],
            "auto_reply_allowed": risk_review["auto_reply_allowed"],
            "external_execution_allowed": risk_review["external_execution_allowed"],
            "write_api_called": risk_review["write_api_called"],
            "next_recommendation": "Use rulebook-governed review_required/rejected states before producing manual export packs or external action evidence.",
        }


if __name__ == "__main__":
    result = PlatformSurvivalRulebook().build()
    print(json.dumps({"status": result["status"], "summary": result["platformSurvivalRulebookSummary"]}, indent=2))
