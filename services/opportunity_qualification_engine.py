"""Opportunity qualification for merchant homepage promotion candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.problem_seeker_loop import ProblemSeekerLoop
from services.runtime_persistence import utc_now_iso


DEFAULT_INPUT_PATH = Path("runtime/problem_seeker_loop/problem_candidates.json")
DEFAULT_OUTPUT_DIR = Path("runtime/opportunity_qualification")


class OpportunityQualificationEngine:
    """Score problem candidates before they can become homepage promotion work."""

    def __init__(
        self,
        input_path: str | Path = DEFAULT_INPUT_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.qualified_path = self.output_dir / "qualified_opportunities.json"
        self.ranking_path = self.output_dir / "opportunity_ranking.json"
        self.risk_path = self.output_dir / "opportunity_risk_review.json"
        self.summary_path = self.output_dir / "opportunity_qualification_summary.json"

    def qualify(self) -> dict[str, Any]:
        candidates = self._load_candidates()
        opportunities = [self._opportunity(index, candidate) for index, candidate in enumerate(candidates, start=1)]
        ranking = sorted(opportunities, key=lambda item: (-item["total_score"], item["opportunity_id"]))
        risk_review = self._risk_review(opportunities)
        summary = self._summary(opportunities, risk_review)
        payload = {
            "report_id": "OPPORTUNITY_QUALIFICATION_ENGINE",
            "created_at": utc_now_iso(),
            "status": "opportunity_qualification_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "qualifiedOpportunities": opportunities,
            "opportunityRanking": ranking,
            "opportunityRiskReview": risk_review,
            "opportunityQualificationSummary": summary,
            "safetyBoundary": "Opportunity Qualification only scores local/read-only candidate problems. It does not generate replies, post, contact users, call write APIs, or execute promotion actions.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "OPPORTUNITY_QUALIFICATION_ENGINE",
                "status": "opportunity_qualification_ready",
                "qualifiedOpportunities": json.loads(self.qualified_path.read_text(encoding="utf-8")) if self.qualified_path.exists() else [],
                "opportunityRanking": json.loads(self.ranking_path.read_text(encoding="utf-8")) if self.ranking_path.exists() else [],
                "opportunityRiskReview": json.loads(self.risk_path.read_text(encoding="utf-8")) if self.risk_path.exists() else {},
                "opportunityQualificationSummary": json.loads(self.summary_path.read_text(encoding="utf-8")),
            }
        return self.qualify()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.qualified_path.write_text(json.dumps(payload["qualifiedOpportunities"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.ranking_path.write_text(json.dumps(payload["opportunityRanking"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.risk_path.write_text(json.dumps(payload["opportunityRiskReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["opportunityQualificationSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_candidates(self) -> list[dict[str, Any]]:
        if not self.input_path.exists():
            ProblemSeekerLoop().run()
        if not self.input_path.exists():
            return []
        data = json.loads(self.input_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("problem_candidates.json must contain a list")
        return data

    def _opportunity(self, index: int, candidate: dict[str, Any]) -> dict[str, Any]:
        breakdown = self._score_breakdown(candidate)
        total_score = self._total_score(breakdown)
        status = self._qualification_status(total_score, breakdown)
        return {
            "opportunity_id": f"HOME-OPP-{index:03d}",
            "problem_id": candidate.get("problem_id", ""),
            "workspace_id": candidate.get("workspace_id", ""),
            "merchant_name": candidate.get("merchant_name", ""),
            "platform": candidate.get("source_platform", ""),
            "market": candidate.get("market", ""),
            "question_text": candidate.get("question_text", ""),
            "score_breakdown": breakdown,
            "total_score": total_score,
            "qualification_status": status,
            "qualification_reason": self._qualification_reason(status, breakdown, candidate),
            "recommended_next_step": self._recommended_next_step(status),
            "human_review_required": True,
            "auto_action_allowed": False,
            "auto_reply_allowed": False,
            "auto_post_allowed": False,
            "sample_data_only": bool(candidate.get("sample_data_only", True)),
            "source_type": candidate.get("source_type", ""),
            "pain_points": candidate.get("pain_points", []),
            "detected_intent": candidate.get("detected_intent", ""),
        }

    def _score_breakdown(self, candidate: dict[str, Any]) -> dict[str, Any]:
        question = str(candidate.get("question_text", ""))
        text = " ".join(
            [
                question,
                str(candidate.get("detected_intent", "")),
                " ".join(candidate.get("pain_points", [])),
                str(candidate.get("homepage_fit_reason", "")),
            ]
        ).lower()
        pain_points = candidate.get("pain_points", [])
        candidate_score = int(candidate.get("candidate_score", 50) or 50)
        platform = candidate.get("source_platform", "")
        source_type = candidate.get("source_type", "")

        pain_strength = min(100, 35 + len(pain_points) * 12 + self._keyword_bonus(text, ["late", "luggage", "elderly", "family", "airport", "transfer", "confusing", "anxiety", "rush"]))
        homepage_fit = min(100, candidate_score)
        answerability = 82 if "?" in question or len(question) >= 40 else 62
        platform_suitability = 85 if platform in {"Reddit", "TikTok", "YouTube", "Xiaohongshu", "Threads", "Google Trends style sample"} else 60
        conversion_potential = min(100, 45 + self._keyword_bonus(text, ["airport", "private", "charter", "transfer", "hotel", "luggage", "elderly", "family", "route"]))
        brand_fit = min(100, 50 + self._keyword_bonus(text, ["japan", "tokyo", "kyoto", "fuji", "travel", "airport", "transport", "guide", "family"]))
        spam_risk = self._spam_risk(question, source_type, text)
        risk_level = self._risk_score(question, text, spam_risk)
        return {
            "pain_strength": pain_strength,
            "homepage_fit": homepage_fit,
            "answerability": answerability,
            "platform_suitability": platform_suitability,
            "conversion_potential": conversion_potential,
            "risk_level": risk_level,
            "spam_risk": spam_risk,
            "brand_fit": brand_fit,
        }

    @staticmethod
    def _keyword_bonus(text: str, keywords: list[str]) -> int:
        return sum(8 for keyword in keywords if keyword in text)

    @staticmethod
    def _spam_risk(question: str, source_type: str, text: str) -> int:
        risk = 12
        if source_type == "seasonal_trend_import_sample":
            risk += 12
        if any(term in text for term in ["discount", "guaranteed", "free", "official"]):
            risk += 25
        non_ascii_ratio = sum(1 for char in question if ord(char) > 127) / max(len(question), 1)
        replacement_like = question.count("・") + question.count("") + question.count("譏")
        if non_ascii_ratio > 0.75 and replacement_like >= 2:
            risk += 55
        return min(100, risk)

    @staticmethod
    def _risk_score(question: str, text: str, spam_risk: int) -> int:
        risk = spam_risk
        if len(question.strip()) < 28:
            risk += 15
        if any(term in text for term in ["spam", "fake", "scrape", "dm me"]):
            risk += 25
        return min(100, risk)

    @staticmethod
    def _total_score(breakdown: dict[str, int]) -> int:
        positive = (
            breakdown["pain_strength"] * 0.20
            + breakdown["homepage_fit"] * 0.22
            + breakdown["answerability"] * 0.15
            + breakdown["platform_suitability"] * 0.12
            + breakdown["conversion_potential"] * 0.16
            + breakdown["brand_fit"] * 0.15
        )
        penalty = breakdown["risk_level"] * 0.18 + breakdown["spam_risk"] * 0.12
        return max(0, min(100, round(positive - penalty)))

    @staticmethod
    def _qualification_status(total_score: int, breakdown: dict[str, int]) -> str:
        if breakdown["risk_level"] >= 72 or breakdown["spam_risk"] >= 70:
            return "unsafe"
        if total_score >= 72 and breakdown["homepage_fit"] >= 75 and breakdown["answerability"] >= 70:
            return "high_value"
        if total_score >= 50:
            return "monitor"
        return "low_value"

    @staticmethod
    def _qualification_reason(status: str, breakdown: dict[str, int], candidate: dict[str, Any]) -> str:
        if status == "unsafe":
            return "Risk or spam signal is too high for homepage promotion without manual correction."
        if status == "high_value":
            return "Strong pain, homepage fit, answerability, and conversion potential make this a good human-reviewed promotion opportunity."
        if status == "monitor":
            return "Useful signal, but score or confidence is not strong enough for immediate homepage promotion."
        return "Low score or weak brand fit; keep as learning signal but do not prioritize."

    @staticmethod
    def _recommended_next_step(status: str) -> str:
        return {
            "high_value": "send_to_human_review_for_answer_branch",
            "monitor": "monitor_and_collect_more_evidence",
            "low_value": "archive_as_low_value_signal",
            "unsafe": "block_auto_action_and_request_manual_correction",
        }[status]

    @staticmethod
    def _risk_review(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        unsafe = [item for item in opportunities if item["qualification_status"] == "unsafe"]
        return {
            "unsafe_count": len(unsafe),
            "unsafe_problem_ids": [item["problem_id"] for item in unsafe],
            "auto_action_allowed_for_unsafe": any(item["auto_action_allowed"] for item in unsafe),
            "all_actions_human_gated": all(item["human_review_required"] and not item["auto_action_allowed"] for item in opportunities),
            "risk_reasons": [
                {
                    "opportunity_id": item["opportunity_id"],
                    "problem_id": item["problem_id"],
                    "risk_level": item["score_breakdown"]["risk_level"],
                    "spam_risk": item["score_breakdown"]["spam_risk"],
                    "reason": item["qualification_reason"],
                }
                for item in unsafe
            ],
        }

    @staticmethod
    def _summary(opportunities: list[dict[str, Any]], risk_review: dict[str, Any]) -> dict[str, Any]:
        counts = Counter(item["qualification_status"] for item in opportunities)
        return {
            "opportunity_qualification_ready": True,
            "opportunity_count": len(opportunities),
            "high_value_count": counts.get("high_value", 0),
            "monitor_count": counts.get("monitor", 0),
            "low_value_count": counts.get("low_value", 0),
            "unsafe_count": counts.get("unsafe", 0),
            "status_counts": dict(counts),
            "top_opportunities": [item["opportunity_id"] for item in sorted(opportunities, key=lambda row: row["total_score"], reverse=True)[:5]],
            "human_review_required": all(item["human_review_required"] for item in opportunities),
            "auto_action_allowed": any(item["auto_action_allowed"] for item in opportunities),
            "unsafe_auto_action_allowed": risk_review["auto_action_allowed_for_unsafe"],
            "recommended_next_round": "ROUND-GROWTH-PLUGIN-004 Answer Branch Drafting Engine",
        }


if __name__ == "__main__":
    result = OpportunityQualificationEngine().qualify()
    print(json.dumps({"status": result["status"], "summary": result["opportunityQualificationSummary"]}, indent=2))
