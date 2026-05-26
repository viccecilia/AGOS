"""Draft helpful answers that softly guide users to a merchant homepage."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.opportunity_qualification_engine import OpportunityQualificationEngine
from services.runtime_persistence import utc_now_iso


DEFAULT_INPUT_PATH = Path("runtime/opportunity_qualification/qualified_opportunities.json")
DEFAULT_PROFILE_PATH = Path("runtime/merchant_promotion_workspace/merchant_profiles.json")
DEFAULT_OUTPUT_DIR = Path("runtime/answer_to_homepage_drafts")

SUPPORTED_PLATFORMS = ["Reddit", "TikTok", "Instagram", "X", "YouTube", "Threads", "SEO", "Xiaohongshu"]

PLATFORM_TONES = {
    "Reddit": "Specific, practical, transparent, no hard sell.",
    "TikTok": "Short hook, simple steps, emotional but not exaggerated.",
    "Instagram": "Light, visual, concise, route-planning friendly.",
    "X": "Direct, opinionated, compact, trend-aware.",
    "YouTube": "Structured explanation with clear planning takeaways.",
    "Threads": "Conversational, warm, quick to scan.",
    "SEO": "Search-friendly, evergreen, clear headings.",
    "Xiaohongshu": "Helpful lifestyle tone, practical Japan travel details, no overclaiming.",
    "Google Trends style sample": "Search-intent interpretation, cautious because data is sample-only.",
}


class AnswerToHomepageDraftEngine:
    """Generate human-reviewed answer drafts from qualified opportunities."""

    def __init__(
        self,
        input_path: str | Path = DEFAULT_INPUT_PATH,
        profile_path: str | Path = DEFAULT_PROFILE_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.input_path = Path(input_path)
        self.profile_path = Path(profile_path)
        self.output_dir = Path(output_dir)
        self.drafts_path = self.output_dir / "answer_drafts.json"
        self.variants_path = self.output_dir / "platform_draft_variants.json"
        self.risk_path = self.output_dir / "draft_risk_review.json"
        self.summary_path = self.output_dir / "answer_to_homepage_summary.json"

    def build(self) -> dict[str, Any]:
        opportunities = self._load_opportunities()
        profiles = self._load_profiles()
        profile_by_workspace = {item.get("workspace_id"): item for item in profiles}
        draftable = [item for item in opportunities if item.get("qualification_status") == "high_value"]
        drafts = [self._draft(index, item, profile_by_workspace.get(item.get("workspace_id"), {})) for index, item in enumerate(draftable, start=1)]
        variants = self._platform_variants(drafts)
        risk_review = self._risk_review(drafts)
        summary = self._summary(drafts, variants, risk_review)
        payload = {
            "report_id": "ANSWER_TO_HOMEPAGE_DRAFT_ENGINE",
            "created_at": utc_now_iso(),
            "status": "answer_to_homepage_drafts_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "supportedPlatforms": SUPPORTED_PLATFORMS,
            "answerDrafts": drafts,
            "platformDraftVariants": variants,
            "draftRiskReview": risk_review,
            "answerToHomepageSummary": summary,
            "safetyBoundary": "Drafts are local suggestions only. They require human review and cannot be auto-published, auto-replied, DM'd, posted, or sent through platform write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "ANSWER_TO_HOMEPAGE_DRAFT_ENGINE",
                "status": "answer_to_homepage_drafts_ready",
                "answerDrafts": json.loads(self.drafts_path.read_text(encoding="utf-8")) if self.drafts_path.exists() else [],
                "platformDraftVariants": json.loads(self.variants_path.read_text(encoding="utf-8")) if self.variants_path.exists() else [],
                "draftRiskReview": json.loads(self.risk_path.read_text(encoding="utf-8")) if self.risk_path.exists() else {},
                "answerToHomepageSummary": json.loads(self.summary_path.read_text(encoding="utf-8")),
            }
        return self.build()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_path.write_text(json.dumps(payload["answerDrafts"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.variants_path.write_text(json.dumps(payload["platformDraftVariants"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_path.write_text(json.dumps(payload["draftRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["answerToHomepageSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_opportunities(self) -> list[dict[str, Any]]:
        if not self.input_path.exists():
            OpportunityQualificationEngine().qualify()
        data = json.loads(self.input_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("qualified_opportunities.json must contain a list")
        return data

    def _load_profiles(self) -> list[dict[str, Any]]:
        if self.profile_path.exists():
            data = json.loads(self.profile_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        return []

    def _draft(self, index: int, opportunity: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        platform = opportunity.get("platform", "Reddit")
        homepage = profile.get("homepage_url", "pending_official_homepage")
        direct_answer = self._direct_answer(opportunity)
        helpful_steps = self._helpful_steps(opportunity)
        soft_cta = self._soft_cta(profile, opportunity)
        risk_notes = self._risk_notes(opportunity, profile)
        full_text = " ".join([direct_answer, " ".join(helpful_steps), soft_cta])
        forbidden = self._forbidden_claim_check(full_text, profile.get("forbidden_claims", []))
        return {
            "draft_id": f"HOME-DRAFT-{index:03d}",
            "opportunity_id": opportunity.get("opportunity_id", ""),
            "workspace_id": opportunity.get("workspace_id", ""),
            "merchant_name": opportunity.get("merchant_name", profile.get("merchant_name", "")),
            "platform": platform,
            "market": opportunity.get("market", ""),
            "direct_answer": direct_answer,
            "helpful_steps": helpful_steps,
            "soft_cta": soft_cta,
            "homepage_reference": homepage,
            "platform_tone": PLATFORM_TONES.get(platform, PLATFORM_TONES["Reddit"]),
            "risk_notes": risk_notes,
            "forbidden_claim_check": forbidden,
            "review_status": "needs_human_review",
            "auto_publish_allowed": False,
            "auto_reply_allowed": False,
            "hard_sell_risk": self._hard_sell_risk(soft_cta),
            "source_question": opportunity.get("question_text", ""),
            "qualification_score": opportunity.get("total_score", 0),
        }

    @staticmethod
    def _direct_answer(opportunity: dict[str, Any]) -> str:
        intent = opportunity.get("detected_intent", "")
        question = opportunity.get("question_text", "this Japan travel question")
        if "airport" in intent or "transfer" in intent:
            return f"For this situation, do not judge only by train price. With luggage, kids, late arrival, or a first Japan trip, compare the full route from arrival gate to hotel door: train changes, walking distance, last-train risk, and luggage handling."
        if "sightseeing" in intent or "route" in intent:
            return f"For this route question, the key is not whether the destination is possible, but whether the day still feels comfortable after transfers, walking time, crowds, and return timing."
        return f"This looks like a real planning question: {question} Start by separating what is uncertain, what must be booked, and what can stay flexible."

    @staticmethod
    def _helpful_steps(opportunity: dict[str, Any]) -> list[str]:
        pain_points = opportunity.get("pain_points", [])
        steps = [
            "List the arrival time, hotel area, group size, luggage count, and whether anyone needs walking support.",
            "Compare door-to-door time, not only station-to-station time.",
            "Keep a fallback option if the route depends on late trains, crowded buses, or several transfers.",
        ]
        if any("family" in item.lower() for item in pain_points):
            steps.append("For family travel, reduce transfer count before optimizing for the lowest fare.")
        if any("luggage" in item.lower() for item in pain_points):
            steps.append("For heavy luggage, check elevator access and walking distance before choosing public transport.")
        if any("elderly" in item.lower() for item in pain_points):
            steps.append("For elderly travelers, prioritize fewer stairs, shorter walking sections, and predictable pickup points.")
        return steps

    @staticmethod
    def _soft_cta(profile: dict[str, Any], opportunity: dict[str, Any]) -> str:
        merchant = profile.get("merchant_name", opportunity.get("merchant_name", "Japan AI Guide App"))
        return f"If you want a second check, use the {merchant} homepage as a planning reference, then manually confirm any booking, route, or pickup detail before acting."

    @staticmethod
    def _risk_notes(opportunity: dict[str, Any], profile: dict[str, Any]) -> list[str]:
        notes = [
            "Needs human review before publishing or replying.",
            "Keep CTA soft; answer the user first and avoid hard selling.",
            "Do not promise bookings, discounts, official status, or guaranteed transport availability.",
        ]
        if opportunity.get("sample_data_only"):
            notes.append("Source is sample/local/read-only intelligence; do not present it as verified live user demand.")
        if opportunity.get("platform") == "Google Trends style sample":
            notes.append("This is search-intent style input, not a direct user post.")
        return notes

    @staticmethod
    def _forbidden_claim_check(text: str, forbidden_claims: list[str]) -> dict[str, Any]:
        lowered = text.lower()
        hits = [claim for claim in forbidden_claims if claim.lower() in lowered]
        return {
            "status": "passed" if not hits else "blocked",
            "blocked_claims": hits,
            "checked_claims": forbidden_claims,
        }

    @staticmethod
    def _hard_sell_risk(soft_cta: str) -> str:
        hard_terms = ["buy now", "limited offer", "guaranteed", "must use", "best price"]
        return "medium" if any(term in soft_cta.lower() for term in hard_terms) else "low"

    @staticmethod
    def _platform_variants(drafts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        variants = []
        for draft in drafts:
            for platform in SUPPORTED_PLATFORMS:
                variants.append(
                    {
                        "variant_id": f"{draft['draft_id']}-{platform.upper().replace(' ', '-')}",
                        "draft_id": draft["draft_id"],
                        "platform": platform,
                        "platform_tone": PLATFORM_TONES.get(platform, PLATFORM_TONES["Reddit"]),
                        "opening_style": AnswerToHomepageDraftEngine._opening_style(platform),
                        "soft_cta": draft["soft_cta"],
                        "review_status": "needs_human_review",
                        "auto_publish_allowed": False,
                    }
                )
        return variants

    @staticmethod
    def _opening_style(platform: str) -> str:
        return {
            "Reddit": "Start with a direct answer and disclose tradeoffs.",
            "TikTok": "Use a short hook before the practical answer.",
            "Instagram": "Frame as a simple saveable travel tip.",
            "X": "Lead with a compact opinion and one key warning.",
            "YouTube": "Structure as a comment or script note with clear sections.",
            "Threads": "Keep it conversational and easy to reply to.",
            "SEO": "Use search-friendly heading and evergreen explanation.",
            "Xiaohongshu": "Use practical checklist style with soft tone.",
        }.get(platform, "Start with a helpful answer.")

    @staticmethod
    def _risk_review(drafts: list[dict[str, Any]]) -> dict[str, Any]:
        blocked = [draft for draft in drafts if draft["forbidden_claim_check"]["status"] != "passed"]
        return {
            "draft_count": len(drafts),
            "blocked_draft_ids": [draft["draft_id"] for draft in blocked],
            "forbidden_claims_passed": not blocked,
            "all_need_human_review": all(draft["review_status"] == "needs_human_review" for draft in drafts),
            "auto_publish_allowed": any(draft["auto_publish_allowed"] for draft in drafts),
            "hard_sell_risk_counts": dict(Counter(draft["hard_sell_risk"] for draft in drafts)),
        }

    @staticmethod
    def _summary(drafts: list[dict[str, Any]], variants: list[dict[str, Any]], risk_review: dict[str, Any]) -> dict[str, Any]:
        return {
            "answer_to_homepage_ready": True,
            "draft_count": len(drafts),
            "platform_variant_count": len(variants),
            "supported_platforms": SUPPORTED_PLATFORMS,
            "drafts_need_human_review": all(draft["review_status"] == "needs_human_review" for draft in drafts),
            "auto_publish_allowed": any(draft["auto_publish_allowed"] for draft in drafts),
            "forbidden_claims_passed": risk_review["forbidden_claims_passed"],
            "top_draft_ids": [draft["draft_id"] for draft in drafts[:5]],
            "recommended_next_round": "ROUND-GROWTH-PLUGIN-005 Human Review Draft Queue",
        }


if __name__ == "__main__":
    result = AnswerToHomepageDraftEngine().build()
    print(json.dumps({"status": result["status"], "summary": result["answerToHomepageSummary"]}, indent=2))
