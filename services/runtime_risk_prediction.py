"""Runtime risk prediction for AGOS semi-autonomous runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.runtime_planner import RuntimePlanner


class RuntimeRiskPrediction:
    """Predict risk in a local runtime action plan."""

    def __init__(self, root: str | Path = "runtime/runtime_risk") -> None:
        self.root = Path(root)
        self.report_path = self.root / "RUNTIME_RISK_REPORT.json"
        self.feed_path = self.root / "runtime_risk_feed.json"
        self.matrix_path = self.root / "runtime_risk_matrix.json"

    def predict(self) -> dict[str, Any]:
        plan = RuntimePlanner().state()
        items = plan.get("todayOperationPlan", [])
        risk_rows = [
            self._risk("spam risk", self._spam_score(items), "Too many reply-like actions or repeated platform activity can look spammy."),
            self._risk("platform risk", self._platform_score(items), "Platform-specific actions require review before any external execution."),
            self._risk("drift risk", self._drift_score(items), "Plan can drift from trusted guide personality if market or tone changes too fast."),
            self._risk("over-marketing risk", self._marketing_score(items), "Promotional wording or platform pushing can weaken trust."),
            self._risk("repetition risk", self._repetition_score(items), "Repeating the same hook, platform, or content format can reduce learning quality."),
        ]
        report = {
            "report_id": "RUNTIME_RISK_REPORT",
            "created_at": utc_now_iso(),
            "status": "risk_predicted",
            "scope": "local_runtime_risk_prediction_only",
            "runtimeRiskMatrix": risk_rows,
            "runtimeRiskFeed": self._feed(risk_rows),
            "riskSummary": {
                "overall_risk": self._overall(risk_rows),
                "highest_risk": max(risk_rows, key=lambda item: item["score"])["risk_type"] if risk_rows else "none",
                "requires_human_review": True,
                "planned_actions_checked": len(items),
            },
            "safetyBoundary": "Risk prediction does not execute external actions.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.predict()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["runtimeRiskFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(json.dumps(report["runtimeRiskMatrix"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _risk(risk_type: str, score: float, reason: str) -> dict[str, Any]:
        return {
            "risk_type": risk_type,
            "score": round(score, 3),
            "level": RuntimeRiskPrediction._level(score),
            "reason": reason,
            "mitigation": RuntimeRiskPrediction._mitigation(risk_type),
            "status": "needs_human_review" if score >= 0.45 else "watch",
        }

    @staticmethod
    def _spam_score(items: list[dict[str, Any]]) -> float:
        replies = len([item for item in items if item.get("action_type") == "today_reply"])
        return min(0.25 + replies * 0.2 + len(items) * 0.03, 0.9)

    @staticmethod
    def _platform_score(items: list[dict[str, Any]]) -> float:
        platforms = {str(item.get("platform", "")).lower() for item in items}
        return min(0.25 + len(platforms) * 0.12, 0.8)

    @staticmethod
    def _drift_score(items: list[dict[str, Any]]) -> float:
        non_japan = len([item for item in items if item.get("market") != "Japan"])
        not_approved = len([item for item in items if item.get("approval_state") == "needs_human_approval"])
        return min(0.2 + non_japan * 0.2 + not_approved * 0.08, 0.9)

    @staticmethod
    def _marketing_score(items: list[dict[str, Any]]) -> float:
        text = " ".join(item.get("planned_action", "").lower() for item in items)
        promo_words = ["promote", "push", "viral", "sell", "conversion"]
        hits = len([word for word in promo_words if word in text])
        return min(0.2 + hits * 0.12, 0.75)

    @staticmethod
    def _repetition_score(items: list[dict[str, Any]]) -> float:
        platforms = [str(item.get("platform", "")).lower() for item in items]
        repeated = len(platforms) - len(set(platforms))
        return min(0.25 + repeated * 0.12, 0.85)

    @staticmethod
    def _feed(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "risk_type": item["risk_type"],
                "level": item["level"],
                "score": item["score"],
                "reason": item["reason"],
                "mitigation": item["mitigation"],
                "status": item["status"],
            }
            for item in rows
        ]

    @staticmethod
    def _level(score: float) -> str:
        if score >= 0.7:
            return "high"
        if score >= 0.45:
            return "medium"
        return "low"

    @staticmethod
    def _overall(rows: list[dict[str, Any]]) -> str:
        max_score = max([item["score"] for item in rows] or [0])
        return RuntimeRiskPrediction._level(max_score)

    @staticmethod
    def _mitigation(risk_type: str) -> str:
        return {
            "spam risk": "Limit frequency and require human approval before external replies.",
            "platform risk": "Keep platform-specific actions as local plans until reviewed.",
            "drift risk": "Keep trusted guide personality and avoid sudden market shifts.",
            "over-marketing risk": "Remove promotional phrasing and keep practical help first.",
            "repetition risk": "Vary hooks, formats, and platforms across cycles.",
        }[risk_type]


if __name__ == "__main__":
    result = RuntimeRiskPrediction().predict()
    print(json.dumps({"status": result["status"], "overall": result["riskSummary"]["overall_risk"]}, indent=2))
