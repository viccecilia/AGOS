"""Opportunity scoring for AGOS Runtime Training."""

from __future__ import annotations

from dataclasses import dataclass


DIMENSIONS = [
    "pain_strength",
    "engagement_potential",
    "content_potential",
    "reply_potential",
    "conversion_potential",
    "cross_platform_potential",
]


@dataclass(frozen=True)
class OpportunityScore:
    question_id: str
    total_score: float
    verdict: str
    dimensions: dict[str, float]
    reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "total_score": self.total_score,
            "verdict": self.verdict,
            "dimensions": self.dimensions,
            "reasons": self.reasons,
        }


class OpportunityScoringEngine:
    def score(self, question: dict) -> OpportunityScore:
        text = f"{question.get('question_text', '')} {' '.join(question.get('pain_points', []))}".lower()
        dimensions = {key: 0.0 for key in DIMENSIONS}
        reasons: list[str] = []

        if any(token in text for token in ["lost", "confused", "anxiety", "迷路", "焦虑", "help"]):
            dimensions["pain_strength"] = 0.85
            reasons.append("痛点强：用户有明确焦虑或求助信号")
        if any(token in text for token in ["tokyo", "train", "station", "route", "transport", "车站", "交通"]):
            dimensions["engagement_potential"] = 0.78
            dimensions["content_potential"] = 0.82
            reasons.append("内容潜力高：交通和路线问题适合多平台解释")
        if "?" in question.get("question_text", "") or "怎么办" in question.get("question_text", ""):
            dimensions["reply_potential"] = 0.76
            reasons.append("回复潜力高：问题可直接给出帮助型答案")
        if question.get("market") in {"Japan", "US", "Europe", "Korea", "Taiwan"}:
            dimensions["conversion_potential"] = 0.55
        if len(question.get("platforms", [])) >= 2 or question.get("platform") in {"reddit", "tiktok", "instagram", "seo"}:
            dimensions["cross_platform_potential"] = 0.68

        total = round(sum(dimensions.values()) / len(DIMENSIONS), 4)
        if total >= 0.68:
            verdict = "high_value"
        elif total >= 0.42:
            verdict = "medium_value"
        else:
            verdict = "low_value"
            reasons.append("不建议立即运营：痛点、互动或转化信号不足")
        return OpportunityScore(str(question.get("question_id", "unknown")), total, verdict, dimensions, reasons)

    def rank(self, questions: list[dict]) -> list[dict]:
        return sorted([self.score(item).to_dict() for item in questions], key=lambda item: item["total_score"], reverse=True)
