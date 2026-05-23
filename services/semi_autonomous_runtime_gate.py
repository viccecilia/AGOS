"""Semi-autonomous runtime phase gate for AGOS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.action_recommendation_engine import ActionRecommendationEngine
from services.human_approval_orchestrator import HumanApprovalOrchestrator
from services.runtime_execution_simulator import RuntimeExecutionSimulator
from services.runtime_persistence import utc_now_iso
from services.runtime_planner import RuntimePlanner
from services.runtime_risk_prediction import RuntimeRiskPrediction


class SemiAutonomousRuntimeGate:
    """Validate whether AGOS has reached semi-autonomous runtime readiness."""

    def __init__(self, root: str | Path = "runtime/semi_autonomous_runtime_gate") -> None:
        self.root = Path(root)
        self.report_path = self.root / "SEMI_AUTONOMOUS_RUNTIME_REPORT.json"
        self.review_path = self.root / "RUNTIME_INTELLIGENCE_GATE_REVIEW.json"
        self.checks_path = self.root / "semi_autonomous_runtime_checks.json"

    def evaluate(
        self,
        action_recommendation: dict[str, Any] | None = None,
        runtime_plan: dict[str, Any] | None = None,
        human_approval: dict[str, Any] | None = None,
        risk_prediction: dict[str, Any] | None = None,
        runtime_simulation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        action = action_recommendation if action_recommendation is not None else ActionRecommendationEngine().state()
        plan = runtime_plan if runtime_plan is not None else RuntimePlanner().state()
        approval = human_approval if human_approval is not None else HumanApprovalOrchestrator().state()
        risk = risk_prediction if risk_prediction is not None else RuntimeRiskPrediction().state()
        simulation = runtime_simulation if runtime_simulation is not None else RuntimeExecutionSimulator().state()
        checks = [
            self._check_action_recommendation(action),
            self._check_runtime_planner(plan),
            self._check_human_approval(approval),
            self._check_risk_prediction(risk),
            self._check_runtime_simulation(simulation),
            self._check_external_execution_boundary(action, plan, approval, risk, simulation),
        ]
        blocked = [item for item in checks if item["status"] == "blocked"]
        warnings = [item for item in checks if item["status"] == "warning"]
        gate_decision = "blocked" if blocked else "passed_with_warnings" if warnings else "passed"
        review = self._runtime_intelligence_review(action, plan, approval, risk, simulation, gate_decision)
        report = {
            "report_id": "SEMI_AUTONOMOUS_RUNTIME_REPORT",
            "created_at": utc_now_iso(),
            "status": gate_decision,
            "scope": "semi_autonomous_runtime_phase_gate",
            "checks": checks,
            "semiAutonomousRuntimeCapability": {
                "can_recommend_actions": checks[0]["status"] in {"passed", "warning"},
                "can_plan_runtime": checks[1]["status"] in {"passed", "warning"},
                "can_unify_human_approval": checks[2]["status"] in {"passed", "warning"},
                "can_predict_risk": checks[3]["status"] in {"passed", "warning"},
                "can_simulate_execution": checks[4]["status"] in {"passed", "warning"},
                "external_execution_enabled": False,
                "ready_for_controlled_external_operations_preparation": gate_decision in {"passed", "passed_with_warnings"},
            },
            "semiAutonomousRuntimeSummary": {
                "gate_decision": gate_decision,
                "passed_checks": len([item for item in checks if item["status"] == "passed"]),
                "warning_checks": len(warnings),
                "blocked_checks": len(blocked),
                "next_stage": "Controlled External Operations Preparation Stage" if gate_decision in {"passed", "passed_with_warnings"} else "Fix blocked semi-autonomous runtime checks",
                "hard_boundary": "No real external execution is allowed at this gate.",
            },
            "runtimeIntelligenceGateReview": review,
            "safetyBoundary": "Gate review does not post, reply, log in, register accounts, call platform APIs, or change external state.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.review_path.write_text(json.dumps(report["runtimeIntelligenceGateReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(report["checks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _check_action_recommendation(action: dict[str, Any]) -> dict[str, Any]:
        count = len(action.get("actionRecommendations", []))
        return SemiAutonomousRuntimeGate._check(
            "Action Recommendation",
            "passed" if action.get("status") == "recommendations_ready" and count >= 4 else "blocked",
            f"{count} action recommendations available; status={action.get('status')}",
            "AGOS must recommend content, reply, platform, and trend actions before planning.",
        )

    @staticmethod
    def _check_runtime_planner(plan: dict[str, Any]) -> dict[str, Any]:
        planned = len(plan.get("todayOperationPlan", []))
        return SemiAutonomousRuntimeGate._check(
            "Runtime Planner",
            "passed" if planned >= 4 and plan.get("runtimePlanSummary", {}).get("pending_approval", 0) >= 0 else "blocked",
            f"{planned} local plan items available; status={plan.get('status')}",
            "AGOS must turn recommendations into a local daily runtime plan.",
        )

    @staticmethod
    def _check_human_approval(approval: dict[str, Any]) -> dict[str, Any]:
        summary = approval.get("approvalSummary", {})
        has_action_items = summary.get("action_queue_items", 0) >= 4
        return SemiAutonomousRuntimeGate._check(
            "Human Approval",
            "passed" if approval.get("status") == "active" and has_action_items else "blocked",
            f"Unified approval total={summary.get('total_items', 0)} action_items={summary.get('action_queue_items', 0)}",
            "AGOS must unify Review, Action, and Correction approval views.",
        )

    @staticmethod
    def _check_risk_prediction(risk: dict[str, Any]) -> dict[str, Any]:
        risk_types = {item.get("risk_type") for item in risk.get("runtimeRiskMatrix", [])}
        required = {"spam risk", "platform risk", "drift risk", "over-marketing risk", "repetition risk"}
        return SemiAutonomousRuntimeGate._check(
            "Risk Prediction",
            "passed" if risk.get("status") == "risk_predicted" and required.issubset(risk_types) else "blocked",
            f"risk_types={sorted(risk_types)} overall={risk.get('riskSummary', {}).get('overall_risk')}",
            "AGOS must predict key operational risks before any execution stage.",
        )

    @staticmethod
    def _check_runtime_simulation(simulation: dict[str, Any]) -> dict[str, Any]:
        summary = simulation.get("executionSimulationSummary", {})
        all_safe = summary.get("external_execution_enabled") is False
        scenarios = summary.get("total_scenarios", 0)
        return SemiAutonomousRuntimeGate._check(
            "Runtime Simulation",
            "passed" if simulation.get("status") == "simulated" and scenarios >= 4 and all_safe else "blocked",
            f"{scenarios} scenarios simulated; external_execution_enabled={summary.get('external_execution_enabled')}",
            "AGOS must simulate what would happen without touching external platforms.",
        )

    @staticmethod
    def _check_external_execution_boundary(*reports: dict[str, Any]) -> dict[str, Any]:
        text = json.dumps(reports, ensure_ascii=False).lower()
        dangerous = [
            '"external_execution_enabled": true',
            '"external_execution": true',
            "platform api call executed",
            "posted externally",
            "auto reply executed",
        ]
        blocked = any(token in text for token in dangerous)
        return SemiAutonomousRuntimeGate._check(
            "External Execution Boundary",
            "blocked" if blocked else "passed",
            "No external execution markers detected." if not blocked else "External execution marker detected.",
            "Semi-autonomous runtime must remain local, simulated, and human-gated.",
        )

    @staticmethod
    def _runtime_intelligence_review(
        action: dict[str, Any],
        plan: dict[str, Any],
        approval: dict[str, Any],
        risk: dict[str, Any],
        simulation: dict[str, Any],
        gate_decision: str,
    ) -> dict[str, Any]:
        return {
            "review_id": "RUNTIME_INTELLIGENCE_GATE_REVIEW",
            "created_at": utc_now_iso(),
            "gate_decision": gate_decision,
            "what_agos_can_do_now": [
                "recommend human-gated operating actions",
                "turn recommendations into a local daily runtime plan",
                "unify human approval views",
                "predict operational risk before execution",
                "simulate what would happen if actions were executed",
            ],
            "what_agos_still_cannot_do": [
                "post content automatically",
                "reply to real users automatically",
                "log in to social platforms",
                "register accounts",
                "call real platform APIs",
                "bypass human approval",
            ],
            "evidence": {
                "recommendations": len(action.get("actionRecommendations", [])),
                "planned_actions": len(plan.get("todayOperationPlan", [])),
                "unified_approval_items": approval.get("approvalSummary", {}).get("total_items", 0),
                "risk_rows": len(risk.get("runtimeRiskMatrix", [])),
                "simulation_scenarios": simulation.get("executionSimulationSummary", {}).get("total_scenarios", 0),
                "external_execution_enabled": False,
            },
            "next_stage": "Controlled External Operations Preparation Stage",
        }

    @staticmethod
    def _check(name: str, status: str, evidence: str, requirement: str) -> dict[str, Any]:
        return {
            "name": name,
            "status": status,
            "evidence": evidence,
            "requirement": requirement,
            "checked_at": utc_now_iso(),
        }


if __name__ == "__main__":
    result = SemiAutonomousRuntimeGate().evaluate()
    print(json.dumps({"status": result["status"], "next": result["semiAutonomousRuntimeSummary"]["next_stage"]}, indent=2))
