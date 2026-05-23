"""External action sandbox for controlled operations preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.action_recommendation_engine import ActionRecommendationEngine
from services.runtime_risk_prediction import RuntimeRiskPrediction
from services.runtime_persistence import utc_now_iso


ACTION_STATUS = {
    "draft",
    "waiting_human_approval",
    "approved_for_manual_execution",
    "rejected",
    "cancelled",
    "simulated_only",
}

SUPPORTED_EXTERNAL_ACTIONS = {
    "external_reply",
    "external_content_publish",
    "external_trend_followup",
    "external_expansion_action",
}

FORBIDDEN_WRITE_ACTIONS = {
    "auto_post",
    "auto_reply",
    "auto_follow",
    "auto_dm",
    "auto_like",
    "auto_login",
    "auto_register",
    "write_api_call",
}


class ExternalActionSandbox:
    """Prepare and simulate external actions while keeping execution blocked."""

    def __init__(self, root: str | Path = "runtime/external_action_sandbox") -> None:
        self.root = Path(root)
        self.report_path = self.root / "EXTERNAL_ACTION_SANDBOX_REPORT.json"
        self.queue_path = self.root / "external_action_queue.json"
        self.feed_path = self.root / "external_action_feed.json"
        self.simulation_path = self.root / "external_action_simulations.json"

    def build(self, recommendations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_recommendations = recommendations
        if source_recommendations is None:
            source_recommendations = ActionRecommendationEngine().state().get("actionRecommendations", [])
        risk = RuntimeRiskPrediction().state()
        queue = [
            self._queue_item(index, recommendation, risk)
            for index, recommendation in enumerate(source_recommendations, start=1)
        ]
        simulations = [self._simulation(item) for item in queue]
        report = {
            "report_id": "EXTERNAL_ACTION_SANDBOX_REPORT",
            "created_at": utc_now_iso(),
            "status": "sandbox_ready",
            "scope": "controlled_external_action_preparation_only",
            "supportedExternalActions": sorted(SUPPORTED_EXTERNAL_ACTIONS),
            "forbiddenWriteActions": sorted(FORBIDDEN_WRITE_ACTIONS),
            "externalActionQueue": queue,
            "externalActionSimulations": simulations,
            "externalActionFeed": self._feed(queue),
            "externalActionSandboxSummary": {
                "total_actions": len(queue),
                "blocked_actions": len([item for item in queue if item["external_execution_allowed"] is False]),
                "waiting_human_approval": len([item for item in queue if item["status"] == "waiting_human_approval"]),
                "simulated_only": len([item for item in queue if item["simulation_status"] == "simulated_only"]),
                "write_api_calls_enabled": False,
                "external_execution_allowed": False,
                "human_gate_required": True,
            },
            "safetyBoundary": "Sandbox prepares and simulates external actions only. It does not post, reply, follow, DM, like, log in, register accounts, or call write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.build()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.queue_path.write_text(json.dumps(report["externalActionQueue"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["externalActionFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.simulation_path.write_text(json.dumps(report["externalActionSimulations"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _queue_item(index: int, recommendation: dict[str, Any], risk: dict[str, Any]) -> dict[str, Any]:
        action_type = ExternalActionSandbox._external_action_type(recommendation.get("action_type", "today_content"))
        risk_summary = risk.get("riskSummary", {})
        status = "waiting_human_approval"
        return {
            "external_action_id": f"EXT-ACTION-{index:04d}",
            "source_action_id": recommendation.get("action_id", f"REC-{index:04d}"),
            "external_action_type": action_type,
            "suggested_action": recommendation.get("recommendation", ""),
            "why_suggested": recommendation.get("why_recommended", ""),
            "target_platform": recommendation.get("recommended_platform", "unknown"),
            "target_market": recommendation.get("recommended_market", "unknown"),
            "risk_level": ExternalActionSandbox._risk_level(recommendation.get("risk_level", "medium"), risk_summary.get("overall_risk", "medium")),
            "risk_reason": risk_summary.get("highest_risk", "requires_human_review"),
            "status": status,
            "human_gate_status": "required",
            "external_execution_allowed": False,
            "blocked_reason": "External actions require human approval and manual execution. Automated write-side platform actions are disabled.",
            "simulation_status": "simulated_only",
            "write_api_call_attempted": False,
            "write_api_call_allowed": False,
            "forbidden_actions_blocked": sorted(FORBIDDEN_WRITE_ACTIONS),
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _external_action_type(action_type: str) -> str:
        mapping = {
            "today_reply": "external_reply",
            "today_content": "external_content_publish",
            "today_trend": "external_trend_followup",
            "today_platform": "external_expansion_action",
        }
        return mapping.get(action_type, "external_trend_followup")

    @staticmethod
    def _risk_level(action_risk: str, runtime_risk: str) -> str:
        levels = {"low": 1, "medium": 2, "high": 3}
        score = max(levels.get(action_risk, 2), levels.get(runtime_risk, 2))
        return {1: "low", 2: "medium", 3: "high"}[score]

    @staticmethod
    def _simulation(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "simulation_id": item["external_action_id"].replace("EXT-ACTION", "EXT-SIM"),
            "external_action_id": item["external_action_id"],
            "status": "simulated_only",
            "would_do": item["suggested_action"],
            "expected_result": "Human can review the suggested action and manually execute outside AGOS if approved.",
            "blocked_reason": item["blocked_reason"],
            "write_api_call_attempted": False,
            "external_execution_allowed": False,
            "created_at": utc_now_iso(),
        }

    @staticmethod
    def _feed(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["created_at"],
                "external_action_id": item["external_action_id"],
                "external_action_type": item["external_action_type"],
                "suggested_action": item["suggested_action"],
                "why_suggested": item["why_suggested"],
                "risk_level": item["risk_level"],
                "target_platform": item["target_platform"],
                "human_gate_status": item["human_gate_status"],
                "external_execution_allowed": item["external_execution_allowed"],
                "blocked_reason": item["blocked_reason"],
                "status": item["status"],
            }
            for item in queue
        ]


if __name__ == "__main__":
    result = ExternalActionSandbox().build()
    print(json.dumps({"status": result["status"], "actions": result["externalActionSandboxSummary"]["total_actions"]}, indent=2))
