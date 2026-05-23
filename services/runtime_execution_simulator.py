"""Safe local execution simulation for AGOS semi-autonomous runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.human_approval_orchestrator import HumanApprovalOrchestrator
from services.runtime_persistence import utc_now_iso
from services.runtime_planner import RuntimePlanner
from services.runtime_risk_prediction import RuntimeRiskPrediction


SIMULATED_ACTION_TYPES = {
    "today_content": "content_publish",
    "today_reply": "reply_action",
    "today_trend": "diffusion_action",
    "today_platform": "platform_operation",
}


class RuntimeExecutionSimulator:
    """Simulate what would happen if AGOS executed approved local runtime actions."""

    def __init__(self, root: str | Path = "runtime/execution_simulation") -> None:
        self.root = Path(root)
        self.report_path = self.root / "EXECUTION_SIMULATION_REPORT.json"
        self.scenarios_path = self.root / "execution_simulation_scenarios.json"
        self.feed_path = self.root / "execution_simulation_feed.json"

    def simulate(
        self,
        runtime_plan: dict[str, Any] | None = None,
        approval: dict[str, Any] | None = None,
        risk: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = runtime_plan if runtime_plan is not None else RuntimePlanner().state()
        approval_report = approval if approval is not None else HumanApprovalOrchestrator().state()
        risk_report = risk if risk is not None else RuntimeRiskPrediction().state()
        approval_by_target = {
            item.get("target_id"): item
            for item in approval_report.get("unifiedApprovalQueue", [])
            if item.get("queue_type") == "action"
        }
        scenarios = [
            self._scenario(index, item, approval_by_target.get(item.get("action_id")), risk_report)
            for index, item in enumerate(plan.get("todayOperationPlan", []), start=1)
        ]
        report = {
            "report_id": "EXECUTION_SIMULATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "simulated",
            "scope": "local_safe_runtime_execution_simulation_only",
            "executionSimulationScenarios": scenarios,
            "executionSimulationFeed": self._feed(scenarios),
            "executionSimulationSummary": {
                "total_scenarios": len(scenarios),
                "content_publish": len([item for item in scenarios if item["simulation_type"] == "content_publish"]),
                "reply_action": len([item for item in scenarios if item["simulation_type"] == "reply_action"]),
                "diffusion_action": len([item for item in scenarios if item["simulation_type"] == "diffusion_action"]),
                "platform_operation": len([item for item in scenarios if item["simulation_type"] == "platform_operation"]),
                "blocked_by_human_gate": len([item for item in scenarios if item["simulation_status"] == "blocked_by_human_gate"]),
                "ready_for_local_dry_run": len([item for item in scenarios if item["simulation_status"] == "ready_for_local_dry_run"]),
                "external_execution_enabled": False,
            },
            "safetyBoundary": "Simulation never posts, replies, logs in, registers accounts, calls platform APIs, or changes external state.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.simulate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.scenarios_path.write_text(json.dumps(report["executionSimulationScenarios"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["executionSimulationFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _scenario(index: int, plan_item: dict[str, Any], approval_item: dict[str, Any] | None, risk_report: dict[str, Any]) -> dict[str, Any]:
        action_type = plan_item.get("action_type", "runtime_action")
        simulation_type = SIMULATED_ACTION_TYPES.get(action_type, "platform_operation")
        approval_status = (approval_item or {}).get("status", plan_item.get("approval_state", "needs_human_approval"))
        approved = approval_status in {"approved", "modified"}
        risk_summary = risk_report.get("riskSummary", {})
        predicted = RuntimeExecutionSimulator._predicted_effect(simulation_type, plan_item, risk_summary)
        return {
            "simulation_id": f"SIM-{index:04d}",
            "simulation_type": simulation_type,
            "source_action_id": plan_item.get("action_id", ""),
            "planned_action": plan_item.get("planned_action", ""),
            "platform": plan_item.get("platform", "Local Runtime"),
            "market": plan_item.get("market", "local"),
            "personality": plan_item.get("personality", "trusted_guide"),
            "approval_status": approval_status,
            "simulation_status": "ready_for_local_dry_run" if approved else "blocked_by_human_gate",
            "what_would_happen": predicted["what_would_happen"],
            "expected_positive_signal": predicted["expected_positive_signal"],
            "expected_negative_signal": predicted["expected_negative_signal"],
            "risk_if_executed": risk_summary.get("overall_risk", "medium"),
            "highest_risk": risk_summary.get("highest_risk", "unknown"),
            "required_before_real_execution": [
                "human approval",
                "runtime risk review",
                "manual platform operation outside AGOS if needed",
            ],
            "external_execution": False,
            "execution_boundary": "simulation only; no external action",
        }

    @staticmethod
    def _predicted_effect(simulation_type: str, plan_item: dict[str, Any], risk_summary: dict[str, Any]) -> dict[str, str]:
        action = plan_item.get("planned_action", "runtime action")
        platform = plan_item.get("platform", "platform")
        common_risk = risk_summary.get("highest_risk", "repetition risk")
        effects = {
            "content_publish": {
                "what_would_happen": f"AGOS would prepare a local content publish draft for {platform}: {action}",
                "expected_positive_signal": "More durable saved content and clearer guidance demand signal.",
                "expected_negative_signal": f"Possible {common_risk} if the draft repeats the same hook or sounds promotional.",
            },
            "reply_action": {
                "what_would_happen": f"AGOS would prepare local reply drafts for {platform}: {action}",
                "expected_positive_signal": "Potential replies, likes, and human feedback on answer usefulness.",
                "expected_negative_signal": f"Possible {common_risk} if reply cadence is too high or platform tone is wrong.",
            },
            "diffusion_action": {
                "what_would_happen": f"AGOS would simulate spreading the trend angle across approved channels: {action}",
                "expected_positive_signal": "Trend reuse can reveal whether one pain point works across platforms.",
                "expected_negative_signal": f"Possible {common_risk} if cross-platform expansion happens before proof.",
            },
            "platform_operation": {
                "what_would_happen": f"AGOS would simulate changing platform focus for {platform}: {action}",
                "expected_positive_signal": "A tighter platform focus can improve learning quality and reduce scattered effort.",
                "expected_negative_signal": f"Possible {common_risk} if the platform focus overfits one short-term signal.",
            },
        }
        return effects.get(simulation_type, effects["platform_operation"])

    @staticmethod
    def _feed(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": utc_now_iso(),
                "simulation_id": item["simulation_id"],
                "type": item["simulation_type"],
                "platform": item["platform"],
                "status": item["simulation_status"],
                "what_would_happen": item["what_would_happen"],
                "risk_if_executed": item["risk_if_executed"],
                "external_execution": item["external_execution"],
            }
            for item in scenarios
        ]


if __name__ == "__main__":
    result = RuntimeExecutionSimulator().simulate()
    print(json.dumps({"status": result["status"], "scenarios": result["executionSimulationSummary"]["total_scenarios"]}, indent=2))
