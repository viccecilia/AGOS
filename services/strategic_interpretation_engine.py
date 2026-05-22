"""Strategic interpretation for AGOS Scout Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.heat_detection_engine import HeatDetectionEngine
from services.runtime_persistence import utc_now_iso


class StrategicInterpretationEngine:
    """Explain why hot trends matter and how AGOS should respond."""

    def __init__(self, root: str | Path = "runtime/strategic_interpretation") -> None:
        self.root = Path(root)
        self.report_path = self.root / "STRATEGIC_INTERPRETATION_REPORT.json"
        self.interpretations_path = self.root / "strategic_interpretations.json"
        self.feed_path = self.root / "strategic_feed.json"

    def interpret(self, opportunity_ranking: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        heat_report = HeatDetectionEngine().state()
        ranking = opportunity_ranking or heat_report.get("opportunityRanking", [])
        interpretations = [self._interpret_signal(signal) for signal in ranking]
        strategic_feed = self._build_feed(interpretations)
        report = {
            "report_id": "STRATEGIC_INTERPRETATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_only_no_external_platform_access",
            "interpretationDimensions": [
                "why_trend_matters",
                "risk",
                "opportunity",
                "content_direction",
                "reply_direction",
                "platform_direction",
            ],
            "strategicInterpretations": interpretations,
            "strategicFeed": strategic_feed,
            "strategicSummary": {
                "total_interpretations": len(interpretations),
                "requires_human_review": len([item for item in interpretations if item["review_required"]]),
                "top_strategy": interpretations[0]["strategy_id"] if interpretations else "none",
                "top_focus": interpretations[0]["cluster_name"] if interpretations else "none",
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.interpret()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.interpretations_path.write_text(json.dumps(report["strategicInterpretations"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["strategicFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _interpret_signal(signal: dict[str, Any]) -> dict[str, Any]:
        cluster_name = signal.get("cluster_name", "Unknown trend")
        platforms = signal.get("platforms", [])
        heat_level = signal.get("heat_level", "watch")
        score = float(signal.get("opportunity_score", 0))
        risk = StrategicInterpretationEngine._risk_for(signal)
        opportunity = StrategicInterpretationEngine._opportunity_for(signal)
        return {
            "strategy_id": "strategy_" + signal.get("signal_id", "unknown").replace("heat_", ""),
            "signal_id": signal.get("signal_id", "unknown"),
            "cluster_name": cluster_name,
            "rank": signal.get("rank", 0),
            "heat_level": heat_level,
            "opportunity_score": score,
            "why_trend_matters": StrategicInterpretationEngine._why_matters(signal),
            "risk": risk,
            "opportunity": opportunity,
            "content_direction": StrategicInterpretationEngine._content_direction_for(signal),
            "reply_direction": StrategicInterpretationEngine._reply_direction_for(signal),
            "platform_direction": StrategicInterpretationEngine._platform_direction_for(platforms, heat_level),
            "review_required": heat_level in {"hot", "warming"} or risk["level"] != "low",
            "recommended_next_step": StrategicInterpretationEngine._recommended_next_step(heat_level, risk["level"]),
            "status": "interpreted",
        }

    @staticmethod
    def _why_matters(signal: dict[str, Any]) -> str:
        signals = ", ".join(signal.get("detectedSignals", []))
        return (
            f"{signal.get('cluster_name', 'This trend')} matters because AGOS detected {signals} "
            f"with opportunity score {signal.get('opportunity_score', 0)}. It indicates a repeated pain point "
            "that can be answered, turned into content, and monitored safely before any real platform action."
        )

    @staticmethod
    def _risk_for(signal: dict[str, Any]) -> dict[str, Any]:
        cluster_name = signal.get("cluster_name", "").lower()
        heat_level = signal.get("heat_level", "watch")
        risks = ["sample_data_only"]
        level = "low"
        if heat_level == "hot":
            risks.extend(["overreacting_to_local_sample", "needs_human_review_before_action"])
            level = "medium"
        if "transport" in cluster_name or "rainy" in cluster_name:
            risks.append("travel_advice_accuracy_risk")
        if len(signal.get("platforms", [])) <= 1:
            risks.append("single_platform_bias")
        return {
            "level": level,
            "items": risks,
            "mitigation": "Keep the action local, create drafts only, and require human review before external use.",
        }

    @staticmethod
    def _opportunity_for(signal: dict[str, Any]) -> dict[str, Any]:
        if signal.get("heat_level") == "hot":
            return {
                "level": "high",
                "summary": "Strong candidate for human-reviewed reply branch and content strategy.",
            }
        if signal.get("heat_level") == "warming":
            return {
                "level": "medium",
                "summary": "Candidate for draft strategy and one more monitoring cycle.",
            }
        return {
            "level": "watch",
            "summary": "Keep in watchlist until stronger evidence appears.",
        }

    @staticmethod
    def _content_direction_for(signal: dict[str, Any]) -> str:
        name = signal.get("cluster_name", "").lower()
        if "transport" in name:
            return "Create practical route-confidence content: station map explainer, transfer checklist, and first-time Tokyo transit guide."
        if "rainy" in name:
            return "Create weather-safe itinerary content: indoor route, food/shopping fallback, and rainy-day timing tips."
        if "air fryer" in name:
            return "Create maintenance content: quick cleaning steps, grease prevention, and mistake checklist."
        if "vacuum" in name:
            return "Create troubleshooting content: suction loss diagnosis, filter cleaning, and maintenance cadence."
        return "Create educational content that explains the pain point and gives a safe next step."

    @staticmethod
    def _reply_direction_for(signal: dict[str, Any]) -> str:
        if signal.get("heat_level") == "hot":
            return "Draft a concise helpful reply with empathy, specific steps, and a soft CTA; require human approval."
        if signal.get("heat_level") == "warming":
            return "Draft answer variants, but hold posting until the signal repeats."
        return "Do not reply yet; collect more examples."

    @staticmethod
    def _platform_direction_for(platforms: list[str], heat_level: str) -> dict[str, str]:
        direction: dict[str, str] = {}
        for platform in platforms:
            if platform == "Reddit":
                direction[platform] = "Use detailed, non-promotional answers with firsthand-style reasoning."
            elif platform == "TikTok":
                direction[platform] = "Use short hook-first content that names the pain quickly."
            elif platform == "YouTube":
                direction[platform] = "Use explainer or checklist format with practical steps."
            elif platform == "Instagram":
                direction[platform] = "Use visual carousel or route card style."
            else:
                direction[platform] = "Use safe local draft only; validate platform tone before publishing."
        if not direction:
            direction["Local"] = "No platform action; keep interpretation in local memory."
        if heat_level == "watch":
            direction = {platform: "Monitor only; no external action." for platform in direction}
        return direction

    @staticmethod
    def _recommended_next_step(heat_level: str, risk_level: str) -> str:
        if heat_level == "hot" and risk_level != "high":
            return "Create human-reviewed strategy draft and answer branch; do not publish automatically."
        if heat_level == "warming":
            return "Prepare draft and wait for the next scout cycle."
        return "Keep monitoring and avoid content generation until evidence improves."

    @staticmethod
    def _build_feed(interpretations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        feed = []
        for item in interpretations:
            feed.append(
                {
                    "time": utc_now_iso(),
                    "type": "strategic_interpretation",
                    "cluster_name": item["cluster_name"],
                    "rank": item["rank"],
                    "heat_level": item["heat_level"],
                    "why": item["why_trend_matters"],
                    "risk_level": item["risk"]["level"],
                    "opportunity_level": item["opportunity"]["level"],
                    "content_direction": item["content_direction"],
                    "reply_direction": item["reply_direction"],
                    "status": item["status"],
                }
            )
        return feed


if __name__ == "__main__":
    result = StrategicInterpretationEngine().interpret()
    print(json.dumps({"status": result["status"], "items": len(result["strategicInterpretations"])}, indent=2))
