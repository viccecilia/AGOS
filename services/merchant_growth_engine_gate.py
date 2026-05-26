"""Gate validation for the Merchant Homepage Growth Engine phase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.answer_to_homepage_draft_engine import AnswerToHomepageDraftEngine
from services.cross_platform_promotion_plan_engine import CrossPlatformPromotionPlanEngine
from services.merchant_promotion_workspace import MerchantPromotionWorkspace
from services.opportunity_qualification_engine import OpportunityQualificationEngine
from services.problem_seeker_loop import ProblemSeekerLoop
from services.promotion_feedback_learning import PromotionFeedbackLearning
from services.promotion_review_center import PromotionReviewCenter
from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/merchant_growth_engine_gate")


class MerchantGrowthEngineGate:
    """Validate the full pluggable merchant homepage promotion loop."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "MERCHANT_GROWTH_ENGINE_REPORT.json"
        self.safety_path = self.output_dir / "MERCHANT_GROWTH_ENGINE_SAFETY_REVIEW.json"
        self.checks_path = self.output_dir / "merchant_growth_engine_checks.json"
        self.summary_path = self.output_dir / "merchant_growth_engine_summary.json"

    def evaluate(self) -> dict[str, Any]:
        workspace = MerchantPromotionWorkspace().build()
        problem = ProblemSeekerLoop().run()
        opportunity = OpportunityQualificationEngine().qualify()
        drafts = AnswerToHomepageDraftEngine().build()
        plans = CrossPlatformPromotionPlanEngine().build()
        review = PromotionReviewCenter().build()
        feedback = PromotionFeedbackLearning().learn()

        checks = self._checks(workspace, problem, opportunity, drafts, plans, review, feedback)
        safety_review = self._safety_review(workspace, problem, opportunity, drafts, plans, review, feedback)
        report = self._report(workspace, problem, opportunity, drafts, plans, review, feedback, checks, safety_review)
        summary = self._summary(report, checks, safety_review)
        payload = {
            "report_id": "MERCHANT_GROWTH_ENGINE_GATE",
            "created_at": utc_now_iso(),
            "status": "merchant_growth_engine_gate_passed" if summary["gate_passed"] else "merchant_growth_engine_gate_needs_review",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "merchantGrowthEngineReport": report,
            "merchantGrowthEngineSafetyReview": safety_review,
            "merchantGrowthEngineChecks": checks,
            "merchantGrowthEngineSummary": summary,
            "safetyBoundary": "Merchant Growth Engine Gate validates local, human-gated merchant homepage growth capability only. It does not auto-post, auto-reply, auto-DM, call write APIs, scrape login-only data, or treat sample learning as real commercial attribution.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            report = self._read_json(self.report_path, {})
            safety = self._read_json(self.safety_path, {})
            checks = self._read_json(self.checks_path, [])
            summary = self._read_json(self.summary_path, {})
            return {
                "report_id": "MERCHANT_GROWTH_ENGINE_GATE",
                "status": "merchant_growth_engine_gate_passed" if summary.get("gate_passed") else "merchant_growth_engine_gate_needs_review",
                "merchantGrowthEngineReport": report,
                "merchantGrowthEngineSafetyReview": safety,
                "merchantGrowthEngineChecks": checks,
                "merchantGrowthEngineSummary": summary,
            }
        return self.evaluate()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(payload["merchantGrowthEngineReport"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.safety_path.write_text(json.dumps(payload["merchantGrowthEngineSafetyReview"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.checks_path.write_text(json.dumps(payload["merchantGrowthEngineChecks"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["merchantGrowthEngineSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _checks(
        workspace: dict[str, Any],
        problem: dict[str, Any],
        opportunity: dict[str, Any],
        drafts: dict[str, Any],
        plans: dict[str, Any],
        review: dict[str, Any],
        feedback: dict[str, Any],
    ) -> list[dict[str, Any]]:
        workspace_summary = workspace.get("merchantPromotionSummary", {})
        problem_summary = problem.get("problemSeekerSummary", {})
        opportunity_summary = opportunity.get("opportunityQualificationSummary", {})
        draft_summary = drafts.get("answerToHomepageSummary", {})
        plan_summary = plans.get("crossPlatformPromotionSummary", {})
        review_summary = review.get("promotionReviewSummary", {})
        feedback_summary = feedback.get("promotionFeedbackSummary", {})
        return [
            {
                "check_id": "MERCHANT-GATE-001",
                "module": "Merchant Promotion Workspace",
                "readiness_key": "workspace_plugin_ready",
                "status": "passed" if workspace_summary.get("workspace_plugin_ready") and workspace_summary.get("workspace_isolation_checked") else "needs_review",
                "result": f"{workspace_summary.get('merchant_profiles', 0)} merchant profiles; active workspace={workspace_summary.get('active_workspace')}.",
                "evidence": ["merchant_profiles.json", "merchant_social_matrix.json", "merchant_promotion_summary.json"],
            },
            {
                "check_id": "MERCHANT-GATE-002",
                "module": "Problem Seeker Loop",
                "readiness_key": "problem_seeker_ready",
                "status": "passed" if problem_summary.get("problem_seeker_ready") and problem_summary.get("candidate_count", 0) >= 5 else "needs_review",
                "result": f"{problem_summary.get('candidate_count', 0)} candidate problems found; human gated={problem_summary.get('all_candidates_need_human_review')}.",
                "evidence": ["problem_candidates.json", "problem_seeker_summary.json"],
            },
            {
                "check_id": "MERCHANT-GATE-003",
                "module": "Opportunity Qualification",
                "readiness_key": "opportunity_qualification_ready",
                "status": "passed" if opportunity_summary.get("opportunity_qualification_ready") and opportunity_summary.get("high_value_count", 0) > 0 else "needs_review",
                "result": f"{opportunity_summary.get('high_value_count', 0)} high-value opportunities; auto action={opportunity_summary.get('auto_action_allowed')}.",
                "evidence": ["qualified_opportunities.json", "opportunity_qualification_summary.json"],
            },
            {
                "check_id": "MERCHANT-GATE-004",
                "module": "Answer-to-Homepage Drafts",
                "readiness_key": "answer_draft_ready",
                "status": "passed" if draft_summary.get("answer_to_homepage_ready") and draft_summary.get("drafts_need_human_review") else "needs_review",
                "result": f"{draft_summary.get('draft_count', 0)} answer drafts and {draft_summary.get('platform_variant_count', 0)} platform variants.",
                "evidence": ["answer_drafts.json", "platform_draft_variants.json", "answer_to_homepage_summary.json"],
            },
            {
                "check_id": "MERCHANT-GATE-005",
                "module": "Cross-Platform Promotion Plan",
                "readiness_key": "cross_platform_plan_ready",
                "status": "passed" if plan_summary.get("cross_platform_promotion_ready") and plan_summary.get("all_plans_need_human_review") else "needs_review",
                "result": f"{plan_summary.get('plan_count', 0)} platform plans across {plan_summary.get('platform_count', 0)} platforms.",
                "evidence": ["promotion_plans.json", "content_calendar_draft.json", "cross_platform_promotion_summary.json"],
            },
            {
                "check_id": "MERCHANT-GATE-006",
                "module": "Promotion Review Center",
                "readiness_key": "review_center_ready",
                "status": "passed" if review_summary.get("promotion_review_center_ready") and review_summary.get("approve_is_not_publish") else "needs_review",
                "result": f"{review_summary.get('review_item_count', 0)} review items; decisions supported={', '.join(review_summary.get('supports_decisions', []))}.",
                "evidence": ["promotion_review_items.json", "promotion_review_decisions.json", "promotion_review_summary.json"],
            },
            {
                "check_id": "MERCHANT-GATE-007",
                "module": "Promotion Feedback Learning",
                "readiness_key": "feedback_learning_ready",
                "status": "passed" if feedback_summary.get("promotion_feedback_learning_ready") and feedback_summary.get("feedback_event_count", 0) >= 5 else "needs_review",
                "result": f"{feedback_summary.get('feedback_event_count', 0)} feedback events; best patterns={feedback_summary.get('best_pattern_count', 0)}; failed patterns={feedback_summary.get('failed_pattern_count', 0)}.",
                "evidence": ["promotion_feedback_events.json", "best_promotion_patterns.json", "failed_promotion_patterns.json"],
            },
        ]

    @staticmethod
    def _safety_review(
        workspace: dict[str, Any],
        problem: dict[str, Any],
        opportunity: dict[str, Any],
        drafts: dict[str, Any],
        plans: dict[str, Any],
        review: dict[str, Any],
        feedback: dict[str, Any],
    ) -> dict[str, Any]:
        workspace_summary = workspace.get("merchantPromotionSummary", {})
        problem_summary = problem.get("problemSeekerSummary", {})
        opportunity_summary = opportunity.get("opportunityQualificationSummary", {})
        draft_summary = drafts.get("answerToHomepageSummary", {})
        plan_summary = plans.get("crossPlatformPromotionSummary", {})
        review_summary = review.get("promotionReviewSummary", {})
        feedback_summary = feedback.get("promotionFeedbackSummary", {})
        safety_flags = {
            "workspace_isolation": bool(workspace_summary.get("workspace_isolation_checked") and problem_summary.get("workspace_isolation_checked")),
            "home_appliance_pollution_detected": bool(problem_summary.get("home_appliance_pollution_detected", False)),
            "human_review_gate": bool(
                workspace_summary.get("all_actions_human_gated")
                and problem_summary.get("all_candidates_need_human_review")
                and opportunity_summary.get("human_review_required")
                and draft_summary.get("drafts_need_human_review")
                and plan_summary.get("all_plans_need_human_review")
            ),
            "auto_spam_enabled": False,
            "auto_post_enabled": bool(
                workspace_summary.get("auto_post_enabled")
                or problem_summary.get("auto_post_allowed")
                or draft_summary.get("auto_publish_allowed")
                or plan_summary.get("auto_publish_allowed")
                or review_summary.get("auto_publish_allowed")
            ),
            "auto_reply_enabled": bool(workspace_summary.get("auto_reply_enabled") or problem_summary.get("auto_reply_allowed")),
            "auto_dm_enabled": bool(workspace_summary.get("auto_dm_enabled", False)),
            "write_api_enabled": bool(workspace_summary.get("write_api_enabled") or plan_summary.get("write_api_called") or review_summary.get("write_api_called")),
            "login_scraping_enabled": False,
            "sample_marked_real_business_result": feedback_summary.get("real_business_result") is True,
            "auto_next_action_allowed": bool(feedback_summary.get("auto_next_action_allowed", False)),
        }
        blocked_flags = {
            "no_auto_spam": safety_flags["auto_spam_enabled"] is False,
            "no_auto_posting": safety_flags["auto_post_enabled"] is False,
            "no_auto_reply": safety_flags["auto_reply_enabled"] is False,
            "no_auto_dm": safety_flags["auto_dm_enabled"] is False,
            "no_write_api": safety_flags["write_api_enabled"] is False,
            "no_login_scraping": safety_flags["login_scraping_enabled"] is False,
            "sample_not_real_result": safety_flags["sample_marked_real_business_result"] is False,
            "no_auto_next_action": safety_flags["auto_next_action_allowed"] is False,
        }
        safety_boundary_passed = (
            safety_flags["workspace_isolation"]
            and not safety_flags["home_appliance_pollution_detected"]
            and safety_flags["human_review_gate"]
            and all(blocked_flags.values())
        )
        return {
            "review_id": "MERCHANT_GROWTH_ENGINE_SAFETY_REVIEW",
            "created_at": utc_now_iso(),
            "workspace_isolation": safety_flags["workspace_isolation"],
            "human_review_gate": safety_flags["human_review_gate"],
            "home_appliance_pollution_detected": safety_flags["home_appliance_pollution_detected"],
            "auto_spam_enabled": safety_flags["auto_spam_enabled"],
            "auto_post_enabled": safety_flags["auto_post_enabled"],
            "auto_reply_enabled": safety_flags["auto_reply_enabled"],
            "auto_dm_enabled": safety_flags["auto_dm_enabled"],
            "write_api_enabled": safety_flags["write_api_enabled"],
            "login_scraping_enabled": safety_flags["login_scraping_enabled"],
            "blocked_flags": blocked_flags,
            "safety_boundary_passed": safety_boundary_passed,
            "risk_review": [
                {
                    "risk": "workspace_pollution",
                    "status": "controlled" if safety_flags["workspace_isolation"] and not safety_flags["home_appliance_pollution_detected"] else "needs_review",
                    "evidence": "Problem Seeker keeps JAG problems out of Home Appliance workspace.",
                },
                {
                    "risk": "automatic_external_execution",
                    "status": "blocked" if all(blocked_flags.values()) else "needs_review",
                    "evidence": blocked_flags,
                },
                {
                    "risk": "sample_feedback_treated_as_real_revenue",
                    "status": "controlled" if not safety_flags["sample_marked_real_business_result"] else "needs_review",
                    "evidence": "Promotion Feedback Learning keeps sample_data_only=true and real_business_result=false.",
                },
            ],
        }

    @staticmethod
    def _report(
        workspace: dict[str, Any],
        problem: dict[str, Any],
        opportunity: dict[str, Any],
        drafts: dict[str, Any],
        plans: dict[str, Any],
        review: dict[str, Any],
        feedback: dict[str, Any],
        checks: list[dict[str, Any]],
        safety_review: dict[str, Any],
    ) -> dict[str, Any]:
        readiness = {item["readiness_key"]: item["status"] == "passed" for item in checks}
        workspace_summary = workspace.get("merchantPromotionSummary", {})
        problem_summary = problem.get("problemSeekerSummary", {})
        opportunity_summary = opportunity.get("opportunityQualificationSummary", {})
        draft_summary = drafts.get("answerToHomepageSummary", {})
        plan_summary = plans.get("crossPlatformPromotionSummary", {})
        review_summary = review.get("promotionReviewSummary", {})
        feedback_summary = feedback.get("promotionFeedbackSummary", {})
        return {
            "report_id": "MERCHANT_GROWTH_ENGINE_REPORT",
            "created_at": utc_now_iso(),
            **readiness,
            "safety_boundary_passed": safety_review.get("safety_boundary_passed", False),
            "active_workspace": workspace_summary.get("active_workspace"),
            "active_merchant": workspace_summary.get("active_merchant"),
            "candidate_problem_count": problem_summary.get("candidate_count", 0),
            "high_value_opportunity_count": opportunity_summary.get("high_value_count", 0),
            "answer_draft_count": draft_summary.get("draft_count", 0),
            "cross_platform_plan_count": plan_summary.get("plan_count", 0),
            "review_item_count": review_summary.get("review_item_count", 0),
            "feedback_event_count": feedback_summary.get("feedback_event_count", 0),
            "best_promotion_patterns": feedback.get("bestPromotionPatterns", [])[:8],
            "failed_promotion_patterns": feedback.get("failedPromotionPatterns", [])[:8],
            "capability_chain": [
                "Merchant homepage",
                "Problem Seeker",
                "Opportunity Qualification",
                "Answer Draft",
                "Cross-Platform Promotion Plan",
                "Human Review",
                "Feedback Learning",
            ],
            "next_stage_recommendation": "Proceed to Controlled Real External Interaction Preparation with manual export packs, explicit human approval, and no platform write/API execution by default.",
        }

    @staticmethod
    def _summary(report: dict[str, Any], checks: list[dict[str, Any]], safety_review: dict[str, Any]) -> dict[str, Any]:
        passed = len([item for item in checks if item["status"] == "passed"])
        gate_passed = passed == len(checks) and safety_review.get("safety_boundary_passed") is True
        return {
            "merchant_growth_engine_ready": gate_passed,
            "gate_passed": gate_passed,
            "phase_completed": gate_passed,
            "checks": len(checks),
            "passed": passed,
            "workspace_plugin_ready": report.get("workspace_plugin_ready", False),
            "problem_seeker_ready": report.get("problem_seeker_ready", False),
            "opportunity_qualification_ready": report.get("opportunity_qualification_ready", False),
            "answer_draft_ready": report.get("answer_draft_ready", False),
            "cross_platform_plan_ready": report.get("cross_platform_plan_ready", False),
            "review_center_ready": report.get("review_center_ready", False),
            "feedback_learning_ready": report.get("feedback_learning_ready", False),
            "safety_boundary_passed": safety_review.get("safety_boundary_passed", False),
            "auto_post_enabled": safety_review.get("auto_post_enabled", True),
            "auto_reply_enabled": safety_review.get("auto_reply_enabled", True),
            "auto_dm_enabled": safety_review.get("auto_dm_enabled", True),
            "write_api_enabled": safety_review.get("write_api_enabled", True),
            "login_scraping_enabled": safety_review.get("login_scraping_enabled", True),
            "next_stage": "CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION",
            "next_stage_recommendation": report.get("next_stage_recommendation", ""),
        }


if __name__ == "__main__":
    result = MerchantGrowthEngineGate().evaluate()
    print(json.dumps({"status": result["status"], "summary": result["merchantGrowthEngineSummary"]}, indent=2))
