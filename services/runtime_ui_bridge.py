"""Bridge between local Runtime Engine JSON state and the control center UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.action_recommendation_engine import ActionRecommendationEngine
from services.action_queue_engine import ActionQueueEngine
from services.api_collection_review_and_correction import APICollectionReviewAndCorrection
from services.api_capability_registry import APICapabilityRegistry
from services.api_credential_setup_wizard import APICredentialSetupWizard
from services.api_rate_limit_guard import APIRateLimitGuard
from services.api_signal_normalization import APISignalNormalization
from services.api_scout_gate import APIScoutGate
from services.api_to_scout_pipeline import APIToScoutPipeline
from services.batch_human_review import BatchHumanReview
from services.batch_scout_runtime import BatchScoutRuntime
from services.batch_topic_clustering import BatchTopicClustering
from services.best_answer_learning_engine import BestAnswerLearningEngine
from services.autonomous_growth_preparation_gate import AutonomousGrowthPreparationGate
from services.collection_compliance_guard import CollectionComplianceGuard
from services.controlled_api_collection_gate import ControlledAPICollectionGate
from services.cross_platform_expansion_engine import CrossPlatformExpansionEngine
from services.daily_question_import_engine import DailyQuestionImportEngine
from services.daily_operations_report_engine import DailyOperationsReportEngine
from services.failure_analysis_engine import FailureAnalysisEngine
from services.growth_signal_correlation_engine import GrowthSignalCorrelationEngine
from services.external_action_sandbox import ExternalActionSandbox
from services.human_approval_orchestrator import HumanApprovalOrchestrator
from services.human_feedback_learning import HumanFeedbackLearning
from services.human_personality_training import HumanPersonalityTraining
from services.heat_detection_engine import HeatDetectionEngine
from services.intelligence_acceleration_gate import IntelligenceAccelerationGate
from services.long_term_strategy_memory import LongTermStrategyMemory
from services.live_collection_runner import LiveCollectionRunner
from services.live_data_import_to_memory import LiveDataImportToMemory
from services.live_data_normalization_pipeline import LiveDataNormalizationPipeline
from services.personality_drift_engine import PersonalityDriftEngine
from services.personality_isolation_engine import PersonalityIsolationEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.personality_evolution_gate import PersonalityEvolutionGate
from services.personality_review_session import PersonalityReviewSession
from services.platform_account_connection_center import PlatformAccountConnectionCenter
from services.platform_credential_vault import PlatformCredentialVault
from services.real_feedback_capture_engine import RealFeedbackCaptureEngine
from services.real_growth_validation_engine import RealGrowthValidationEngine
from services.real_reply_attempt_engine import RealReplyAttemptEngine
from services.read_only_trend_connector import ReadOnlyTrendConnector
from services.patrol_group_engine import PatrolGroupEngine
from services.keyword_expansion_engine import KeywordExpansionEngine
from services.runtime_drift_monitor import RuntimeDriftMonitor
from services.runtime_engine import RuntimeEngine
from services.runtime_correction_engine import RuntimeCorrectionEngine
from services.runtime_execution_simulator import RuntimeExecutionSimulator
from services.runtime_pattern_learning import RuntimePatternLearning
from services.runtime_persistence import RuntimePersistence
from services.runtime_planner import RuntimePlanner
from services.runtime_priority_engine import RuntimePriorityEngine
from services.runtime_replay_training import RuntimeReplayTraining
from services.runtime_risk_prediction import RuntimeRiskPrediction
from services.runtime_strategy_simulation import RuntimeStrategySimulation
from services.runtime_strategy_personality import RuntimeStrategyPersonalityEngine
from services.semi_autonomous_runtime_gate import SemiAutonomousRuntimeGate
from services.strategic_interpretation_engine import StrategicInterpretationEngine
from services.runtime_trainer_dashboard import RuntimeTrainerDashboard
from services.strategy_evolution_engine import StrategyEvolutionEngine
from services.synthetic_feedback_training import SyntheticFeedbackTraining
from services.topic_discovery_engine import TopicDiscoveryEngine
from services.trend_clustering_engine import TrendClusteringEngine


class RuntimeUIBridge:
    def __init__(self, engine: RuntimeEngine | None = None) -> None:
        self.engine = engine or RuntimeEngine()

    def handle_action(self, action: str) -> dict[str, Any]:
        if action == "start":
            state = self.engine.start()
            # Move beyond Scout so the UI shows a real node transition.
            return self.engine.advance()
        if action == "stop":
            return self.engine.stop()
        if action == "advance":
            return self.engine.advance()
        if action == "state":
            return self.engine.current_state()
        raise ValueError(f"Unsupported runtime action: {action}")

    def export_ui_state(self) -> dict[str, Any]:
        state = self.engine.current_state()
        payload = self.to_war_room_growth(state)
        persistence = self.engine.persistence
        text = __import__("json").dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        persistence.ui_state_file.write_text(text, encoding="utf-8")
        docs_mirror = Path("docs/runtime/runtime_state/ui_state.json")
        docs_mirror.parent.mkdir(parents=True, exist_ok=True)
        docs_mirror.write_text(text, encoding="utf-8")
        return payload

    @staticmethod
    def to_war_room_growth(state: dict[str, Any]) -> dict[str, Any]:
        feedback_summary = HumanFeedbackLearning().summary()
        drift_summary = RuntimeDriftMonitor().summary()
        personality_status = PersonalityMemoryDeposit().status()
        personality_drift = PersonalityDriftEngine().summary()
        personality_isolation = PersonalityIsolationEngine().run_check()
        personality_review_session = PersonalityReviewSession().generate()
        personality_training = HumanPersonalityTraining().summary()
        current_event = state.get("current_event") or ""
        strategy_pain_point = current_event if current_event and not current_event.startswith("human_personality_") else "Tokyo transport anxiety"
        strategy_personality = RuntimeStrategyPersonalityEngine().build_all(
            {
                "workspace": state.get("workspace", "JAG-LAB"),
                "industry_pack": state.get("industry_pack", "Travel Pack / Lab"),
                "market": "Japan",
                "pain_point": strategy_pain_point,
            }
        )
        strategy_evolution = StrategyEvolutionEngine().evaluate()
        trainer_dashboard = RuntimeTrainerDashboard().build()
        personality_evolution_gate = PersonalityEvolutionGate().evaluate()
        patrol_groups = PatrolGroupEngine().build_all()
        keyword_expansion = KeywordExpansionEngine().build_from_patrol_groups()
        topic_discovery = TopicDiscoveryEngine().discover()
        trend_clustering = TrendClusteringEngine().cluster()
        heat_detection = HeatDetectionEngine().detect()
        strategic_interpretation = StrategicInterpretationEngine().interpret()
        cross_platform_expansion = CrossPlatformExpansionEngine().expand()
        daily_question_import = DailyQuestionImportEngine().import_today()
        real_reply_attempts = RealReplyAttemptEngine().generate_attempts(daily_question_import.get("dailyQuestions", []))
        real_feedback_capture = RealFeedbackCaptureEngine().capture()
        best_answer_learning = BestAnswerLearningEngine().learn()
        daily_operations_report = DailyOperationsReportEngine().generate()
        failure_analysis = FailureAnalysisEngine().analyze()
        real_growth_validation = RealGrowthValidationEngine().validate()
        long_term_strategy_memory = LongTermStrategyMemory().build()
        runtime_priority = RuntimePriorityEngine().evolve()
        growth_signal_correlation = GrowthSignalCorrelationEngine().correlate()
        runtime_strategy_simulation = RuntimeStrategySimulation().simulate()
        autonomous_growth_preparation_gate = AutonomousGrowthPreparationGate().evaluate()
        action_recommendations = ActionRecommendationEngine().recommend()
        action_queue = ActionQueueEngine().build_queue(action_recommendations.get("actionRecommendations", []))
        runtime_plan = RuntimePlanner().plan()
        runtime_risk = RuntimeRiskPrediction().predict()
        human_approval = HumanApprovalOrchestrator().orchestrate(
            review_queue=state.get("review_queue", []),
            action_queue=action_queue.get("actionQueue", []),
            correction_queue=RuntimeCorrectionEngine().list(),
        )
        execution_simulation = RuntimeExecutionSimulator().simulate(
            runtime_plan=runtime_plan,
            approval=human_approval,
            risk=runtime_risk,
        )
        semi_autonomous_runtime_gate = SemiAutonomousRuntimeGate().evaluate(
            action_recommendation=action_recommendations,
            runtime_plan=runtime_plan,
            human_approval=human_approval,
            risk_prediction=runtime_risk,
            runtime_simulation=execution_simulation,
        )
        api_capability_registry = APICapabilityRegistry().build()
        platform_credential_vault = PlatformCredentialVault().bootstrap_sample_status()
        platform_account_connections = PlatformAccountConnectionCenter().build(state.get("workspace", "JAG-LAB"))
        api_credential_setup_wizard = APICredentialSetupWizard().build(state.get("workspace", "JAG-LAB"))
        live_collection = LiveCollectionRunner().run(state.get("workspace", "JAG-LAB"))
        compliance_guard = CollectionComplianceGuard().evaluate()
        live_data_normalization = LiveDataNormalizationPipeline().normalize(live_collection.get("liveCollectionItems", []))
        live_memory_import = LiveDataImportToMemory().import_data(
            state.get("workspace", "JAG-LAB"),
            live_data_normalization.get("normalizedLiveData", []),
        )
        api_collection_review = APICollectionReviewAndCorrection().review(live_memory_import)
        controlled_api_collection_gate = ControlledAPICollectionGate().evaluate(state.get("workspace", "JAG-LAB"))
        read_only_trends = ReadOnlyTrendConnector().read_trends()
        api_rate_limit_guard = APIRateLimitGuard().evaluate()
        api_signal_normalization = APISignalNormalization().normalize(read_only_trends.get("platformTrends", []))
        api_to_scout_pipeline = APIToScoutPipeline().run(api_signal_normalization.get("normalizedSignals", []))
        api_scout_gate = APIScoutGate().evaluate()
        external_action_sandbox = ExternalActionSandbox().build(action_recommendations.get("actionRecommendations", []))
        batch_scout_runtime = BatchScoutRuntime().run()
        batch_topic_clustering = BatchTopicClustering().cluster(batch_scout_runtime.get("batchAnalysis", []))
        batch_human_review = BatchHumanReview().review(batch_topic_clustering.get("batchTrendClusters", []))
        runtime_pattern_learning = RuntimePatternLearning().learn(batch_human_review.get("batchReviewQueue", []))
        runtime_replay_training = RuntimeReplayTraining().replay()
        synthetic_feedback_training = SyntheticFeedbackTraining().generate(runtime_replay_training.get("replayMemory", []))
        intelligence_acceleration_gate = IntelligenceAccelerationGate().evaluate(
            {
                "batch_scout": batch_scout_runtime,
                "batch_clusters": batch_topic_clustering,
                "batch_review": batch_human_review,
                "pattern_learning": runtime_pattern_learning,
                "replay_training": runtime_replay_training,
                "synthetic_training": synthetic_feedback_training,
            }
        )
        status = state.get("status", "idle")
        runtime_status = {
            "idle": "STOPPED",
            "running": "RUNNING",
            "paused": "PAUSED",
            "stopped": "STOPPED",
            "needs_human_review": "PAUSED",
            "needs_code_check": "PAUSED",
            "needs_runtime_validation": "PAUSED",
        }.get(status, "STOPPED")
        base_corrections = [
            {
                "issue": "Human Review Gate",
                "status": "needs_human_review" if state.get("review_queue") else "clear",
                "severity": "high",
                "signal": f"{len(state.get('review_queue', []))} pending review items",
                "action": "Approve, reject, or modify before continuing.",
            },
            {
                "issue": "Code Check",
                "status": "needs_code_check",
                "severity": "medium",
                "signal": state.get("current_error") or "no current error",
                "action": "Run runtime smoke tests when errors appear.",
            },
            {
                "issue": "Runtime Validation",
                "status": "needs_runtime_validation",
                "severity": "medium",
                "signal": "Local runtime only; no platform automation.",
                "action": "Validate locally before any external integration.",
            },
        ]
        correction_center = list(state.get("mislearning_alerts", [])) + drift_summary.get("runtimeDriftEvents", []) + base_corrections
        review_queue = state.get("review_queue", [])
        return {
            "runtimeStatus": runtime_status,
            "current_runtime_stage": state.get("current_stage", "Scout"),
            "systemControl": {
                "status": runtime_status,
                "currentWorkspace": state.get("workspace", "jag_app_growth"),
                "currentIndustryPack": state.get("industry_pack", "Travel Pack"),
                "currentCycle": state.get("cycle", "CYCLE-0001"),
                "lastRunTime": state.get("updated_at", ""),
                "buttons": ["启动", "停止"],
            },
            "runtimePipeline": state.get("pipeline", []),
            "warRoomFeed": [
                {
                    "time": event.get("timestamp", "")[-14:-6],
                    "type": event.get("event", "runtime_event"),
                    "sourcePlatform": "Local Runtime",
                    "country": "local",
                    "language": "n/a",
                    "audience": state.get("workspace", "jag_app_growth"),
                    "emotion": "n/a",
                    "status": state.get("status", "idle"),
                    "aiAction": event.get("result", ""),
                    "why": event.get("result", ""),
                }
                for event in state.get("runtime_feed", [])
            ],
            "runtimeWorkspace": {
                "workspace": state.get("workspace", "jag_app_growth"),
                "industryPack": state.get("industry_pack", "Travel Pack"),
                "targetMarket": "local",
                "focusPlatforms": ["Local Runtime"],
                "focusPainPoint": state.get("current_event") or "runtime_loop",
                "todayGoal": "Run local Runtime Engine safely.",
                "riskStatus": state.get("status", "idle"),
                "workspaceStatus": state.get("status", "idle"),
            },
            "socialRuntimeMatrix": [],
            "correctionCenter": correction_center,
            "reviewQueue": review_queue,
            "runtimeQueue": state.get("runtime_queue", []),
            "learningDeposits": state.get("learning_deposits", []),
            "mislearningAlerts": state.get("mislearning_alerts", []),
            "runtimeDrift": "needs_human_review" if state.get("mislearning_alerts") else "clear",
            "platformStyleDrift": [
                item for item in state.get("mislearning_alerts", []) if "平台" in item.get("issue", "") or "Tone" in item.get("issue", "")
            ],
            "opportunityRanking": heat_detection.get("opportunityRanking", []),
            "runtimeIntelligenceFeed": state.get("runtime_intelligence", {}),
            "trainingExplanations": state.get("training_explanations", []),
            "runtimeReviewReport": state.get("runtime_review_report"),
            "runtimeDriftEvents": drift_summary.get("runtimeDriftEvents", []),
            "humanFeedbackSummary": feedback_summary,
            "correctionHistory": feedback_summary.get("correctionHistory", []),
            "humanPreferenceMemory": feedback_summary.get("humanPreferenceMemory", {}),
            "runtimeUiStats": {
                "pendingReviews": len(review_queue),
                "correctionAlerts": len(correction_center),
                "humanDecisionsToday": feedback_summary.get("humanDecisionsToday", 0),
                "topCorrectedMistakes": feedback_summary.get("topCorrectedMistakes", []),
                "mostRejectedStrategy": feedback_summary.get("mostRejectedStrategy", "none"),
                "mostApprovedReplyStyle": feedback_summary.get("mostApprovedReplyStyle", "none"),
            },
            "personalityStatus": personality_status,
            "humanPersonalityTraining": personality_training,
            "personalityDriftAlerts": personality_drift.get("personalityDriftAlerts", []),
            "personalityDriftStatus": personality_drift.get("personalityDriftStatus", "clear"),
            "personalityDriftReason": personality_drift.get("latestDriftReason", ""),
            "personalityIsolationReport": personality_isolation,
            "personalityIsolationFeed": [
                {
                    "dimension": key,
                    "status": personality_isolation.get(key, {}).get("status", "unknown"),
                    "scopes": personality_isolation.get(key, {}).get("scopes_checked", []),
                    "contexts_checked": personality_isolation.get(key, {}).get("contexts_checked", 0),
                    "violations": len(personality_isolation.get(key, {}).get("violations", [])),
                }
                for key in (
                    "workspacePersonalityPollution",
                    "marketPersonalityPollution",
                    "platformPersonalityPollution",
                )
            ],
            "personalityReviewSession": personality_review_session,
            "personalityReviewTrend": personality_review_session.get("personalityTrend", []),
            "personalityRuntimeFeed": [
                {
                    "type": "current_personality",
                    "summary": personality_status.get("currentPersonality", {}),
                    "status": "active",
                },
                {
                    "type": "best_personality",
                    "summary": personality_status.get("bestPersonality", {}),
                    "status": "approved",
                },
                {
                    "type": "failed_personality",
                    "summary": personality_status.get("failedPersonality", {}),
                    "status": personality_drift.get("personalityDriftStatus") if personality_drift.get("personalityDriftAlerts") else personality_status.get("personalityDrift", "clear"),
                },
            ],
            "strategyPersonality": strategy_personality,
            "strategyPersonalityFeed": strategy_personality.get("strategyPersonalityFeed", []),
            "strategyEvolution": strategy_evolution,
            "strategyEvolutionFeed": strategy_evolution.get("evolutionFeed", []),
            "runtimeTrainerDashboard": trainer_dashboard,
            "runtimeTrainerFeed": trainer_dashboard.get("recentLearning", []),
            "personalityEvolutionGate": personality_evolution_gate,
            "personalityEvolutionGateChecks": personality_evolution_gate.get("checks", []),
            "patrolGroups": patrol_groups,
            "activePatrolGroups": patrol_groups.get("activePatrolGroups", []),
            "keywordExpansion": keyword_expansion,
            "keywordExpansionFeed": keyword_expansion.get("keywordExpansions", []),
            "topicDiscovery": topic_discovery,
            "discoveredTopics": topic_discovery.get("discoveredTopics", []),
            "trendClustering": trend_clustering,
            "trendClusters": trend_clustering.get("trendClusters", []),
            "heatDetection": heat_detection,
            "heatSignals": heat_detection.get("heatSignals", []),
            "heatOpportunityRanking": heat_detection.get("opportunityRanking", []),
            "strategicInterpretation": strategic_interpretation,
            "strategicInterpretations": strategic_interpretation.get("strategicInterpretations", []),
            "strategicFeed": strategic_interpretation.get("strategicFeed", []),
            "crossPlatformExpansion": cross_platform_expansion,
            "expansionStrategies": cross_platform_expansion.get("expansionStrategies", []),
            "crossPlatformExpansionFeed": cross_platform_expansion.get("crossPlatformExpansionFeed", []),
            "dailyQuestionImport": daily_question_import,
            "dailyQuestions": daily_question_import.get("dailyQuestions", []),
            "dailyImportSummary": daily_question_import.get("dailyImportSummary", {}),
            "realReplyAttempts": real_reply_attempts,
            "replyAttempts": real_reply_attempts.get("replyAttempts", []),
            "replyReviewQueue": real_reply_attempts.get("replyReviewQueue", []),
            "replyAttemptSummary": real_reply_attempts.get("replyAttemptSummary", {}),
            "realFeedbackCapture": real_feedback_capture,
            "feedbackEvents": real_feedback_capture.get("feedbackEvents", []),
            "feedbackTimeline": real_feedback_capture.get("feedbackTimeline", []),
            "feedbackSummary": real_feedback_capture.get("feedbackSummary", {}),
            "bestAnswerLearning": best_answer_learning,
            "bestAnswerMemory": best_answer_learning.get("bestAnswerLearning", {}),
            "answerLearningTimeline": best_answer_learning.get("answerLearningTimeline", []),
            "dailyOperationsReport": daily_operations_report,
            "runtimeDailyReportFeed": daily_operations_report.get("runtimeDailyReportFeed", []),
            "dailyOperationsSummary": daily_operations_report.get("dailyOperationsSummary", {}),
            "failureAnalysis": failure_analysis,
            "failureItems": failure_analysis.get("failureItems", []),
            "failureTimeline": failure_analysis.get("failureTimeline", []),
            "failureSummary": failure_analysis.get("failureSummary", {}),
            "realGrowthValidation": real_growth_validation,
            "realGrowthValidationChecks": real_growth_validation.get("validationChecks", []),
            "runtimeIntelligenceReview": real_growth_validation.get("runtimeIntelligenceReview", {}),
            "realGrowthValidationSummary": real_growth_validation.get("realGrowthValidationSummary", {}),
            "longTermStrategyMemory": long_term_strategy_memory,
            "longTermEffectiveStrategies": long_term_strategy_memory.get("longTermEffectiveStrategies", []),
            "shortTermEffectiveStrategies": long_term_strategy_memory.get("shortTermEffectiveStrategies", []),
            "longTermFailedStrategies": long_term_strategy_memory.get("longTermFailedStrategies", []),
            "platformLongTermTrends": long_term_strategy_memory.get("platformLongTermTrends", []),
            "marketLongTermTrends": long_term_strategy_memory.get("marketLongTermTrends", []),
            "strategyMemoryTimeline": long_term_strategy_memory.get("strategyMemoryTimeline", []),
            "strategyHorizonClassification": long_term_strategy_memory.get("strategyHorizonClassification", {}),
            "runtimePriority": runtime_priority,
            "platformPriority": runtime_priority.get("platformPriority", []),
            "questionPriority": runtime_priority.get("questionPriority", []),
            "trendPriority": runtime_priority.get("trendPriority", []),
            "contentPriority": runtime_priority.get("contentPriority", []),
            "priorityEvolutionHistory": runtime_priority.get("priorityEvolutionHistory", []),
            "runtimePriorityFeed": runtime_priority.get("runtimePriorityFeed", []),
            "prioritySummary": runtime_priority.get("prioritySummary", {}),
            "growthSignalCorrelation": growth_signal_correlation,
            "signalCorrelationMatrix": growth_signal_correlation.get("signalCorrelationMatrix", {}),
            "growthSignalCorrelationFeed": growth_signal_correlation.get("growthSignalCorrelationFeed", []),
            "correlationSummary": growth_signal_correlation.get("correlationSummary", {}),
            "runtimeStrategySimulation": runtime_strategy_simulation,
            "strategySimulationScenarios": runtime_strategy_simulation.get("strategySimulationScenarios", []),
            "strategySimulationFeed": runtime_strategy_simulation.get("strategySimulationFeed", []),
            "simulationSummary": runtime_strategy_simulation.get("simulationSummary", {}),
            "autonomousGrowthPreparationGate": autonomous_growth_preparation_gate,
            "autonomousGrowthPreparationChecks": autonomous_growth_preparation_gate.get("checks", []),
            "autonomousGrowthPreparationCapability": autonomous_growth_preparation_gate.get("autonomousGrowthPreparationCapability", {}),
            "autonomousGrowthPreparationSummary": autonomous_growth_preparation_gate.get("autonomousGrowthPreparationSummary", {}),
            "autonomousRuntimeIntelligenceReview": autonomous_growth_preparation_gate.get("runtimeIntelligenceReview", {}),
            "actionRecommendationReport": action_recommendations,
            "actionRecommendations": action_recommendations.get("actionRecommendations", []),
            "actionRecommendationFeed": action_recommendations.get("actionRecommendationFeed", []),
            "recommendationSummary": action_recommendations.get("recommendationSummary", {}),
            "actionQueueReport": action_queue,
            "actionQueue": action_queue.get("actionQueue", []),
            "humanActionDecisions": action_queue.get("humanActionDecisions", []),
            "actionQueueFeed": action_queue.get("actionQueueFeed", []),
            "actionQueueSummary": action_queue.get("actionQueueSummary", {}),
            "runtimePlan": runtime_plan,
            "todayOperationPlan": runtime_plan.get("todayOperationPlan", []),
            "todayPlatformFocus": runtime_plan.get("todayPlatformFocus", {}),
            "todayContentRhythm": runtime_plan.get("todayContentRhythm", {}),
            "todayReplyPriority": runtime_plan.get("todayReplyPriority", {}),
            "runtimePlanFeed": runtime_plan.get("runtimePlanFeed", []),
            "runtimePlanSummary": runtime_plan.get("runtimePlanSummary", {}),
            "runtimeRiskPrediction": runtime_risk,
            "runtimeRiskMatrix": runtime_risk.get("runtimeRiskMatrix", []),
            "runtimeRiskFeed": runtime_risk.get("runtimeRiskFeed", []),
            "runtimeRiskSummary": runtime_risk.get("riskSummary", {}),
            "humanApprovalOrchestration": human_approval,
            "unifiedApprovalQueue": human_approval.get("unifiedApprovalQueue", []),
            "unifiedApprovalTimeline": human_approval.get("unifiedApprovalTimeline", []),
            "approvalSummary": human_approval.get("approvalSummary", {}),
            "executionSimulation": execution_simulation,
            "executionSimulationScenarios": execution_simulation.get("executionSimulationScenarios", []),
            "executionSimulationFeed": execution_simulation.get("executionSimulationFeed", []),
            "executionSimulationSummary": execution_simulation.get("executionSimulationSummary", {}),
            "semiAutonomousRuntimeGate": semi_autonomous_runtime_gate,
            "semiAutonomousRuntimeChecks": semi_autonomous_runtime_gate.get("checks", []),
            "semiAutonomousRuntimeCapability": semi_autonomous_runtime_gate.get("semiAutonomousRuntimeCapability", {}),
            "semiAutonomousRuntimeSummary": semi_autonomous_runtime_gate.get("semiAutonomousRuntimeSummary", {}),
            "runtimeIntelligenceGateReview": semi_autonomous_runtime_gate.get("runtimeIntelligenceGateReview", {}),
            "apiCapabilityRegistry": api_capability_registry,
            "platformApiRegistry": api_capability_registry.get("platformApiRegistry", []),
            "apiCapabilityFeed": api_capability_registry.get("apiCapabilityFeed", []),
            "apiRegistrySummary": api_capability_registry.get("apiRegistrySummary", {}),
            "platformCredentialVault": platform_credential_vault,
            "workspaceCredentialStatus": platform_credential_vault.get("workspaceCredentialStatus", []),
            "credentialVaultFeed": platform_credential_vault.get("credentialVaultFeed", []),
            "credentialVaultSummary": platform_credential_vault.get("credentialVaultSummary", {}),
            "platformAccountConnectionCenter": platform_account_connections,
            "platformConnections": platform_account_connections.get("platformConnections", []),
            "platformConnectionFeed": platform_account_connections.get("platformConnectionFeed", []),
            "platformConnectionSummary": platform_account_connections.get("platformConnectionSummary", {}),
            "apiCredentialSetupWizard": api_credential_setup_wizard,
            "credentialSetupSteps": api_credential_setup_wizard.get("credentialSetupSteps", []),
            "credentialSetupStatus": api_credential_setup_wizard.get("credentialSetupStatus", []),
            "credentialSetupFeed": api_credential_setup_wizard.get("credentialSetupFeed", []),
            "credentialSetupSummary": api_credential_setup_wizard.get("credentialSetupSummary", {}),
            "liveCollectionRunner": live_collection,
            "liveCollectionItems": live_collection.get("liveCollectionItems", []),
            "liveCollectionFeed": live_collection.get("liveCollectionFeed", []),
            "liveCollectionSummary": live_collection.get("liveCollectionSummary", {}),
            "liveCollectionPlatformCoverage": live_collection.get("platformCoverage", []),
            "collectionComplianceGuard": compliance_guard,
            "complianceRiskFeed": compliance_guard.get("complianceRiskFeed", []),
            "complianceGuardSummary": compliance_guard.get("complianceGuardSummary", {}),
            "liveDataNormalizationPipeline": live_data_normalization,
            "normalizedLiveData": live_data_normalization.get("normalizedLiveData", []),
            "normalizedLiveDataFeed": live_data_normalization.get("normalizedLiveDataFeed", []),
            "liveDataNormalizationSummary": live_data_normalization.get("liveDataNormalizationSummary", {}),
            "liveDataImportToMemory": live_memory_import,
            "questionInboxMemory": live_memory_import.get("questionInboxMemory", []),
            "painPointLibraryMemory": live_memory_import.get("painPointLibraryMemory", []),
            "patternMemoryImport": live_memory_import.get("patternMemoryImport", []),
            "trendClusterMemory": live_memory_import.get("trendClusterMemory", []),
            "scoutIntelligenceMemory": live_memory_import.get("scoutIntelligenceMemory", []),
            "memoryImportFeed": live_memory_import.get("memoryImportFeed", []),
            "memoryImportSummary": live_memory_import.get("memoryImportSummary", {}),
            "triggeredPatternLearningFromLiveData": live_memory_import.get("triggeredPatternLearning", {}),
            "triggeredReplayTrainingFromLiveData": live_memory_import.get("triggeredReplayTraining", {}),
            "triggeredIntelligenceRankingFromLiveData": live_memory_import.get("triggeredIntelligenceRanking", {}),
            "apiCollectionReviewAndCorrection": api_collection_review,
            "collectionReviewQueue": api_collection_review.get("collectionReviewQueue", []),
            "collectionReviewDecisions": api_collection_review.get("collectionReviewDecisions", []),
            "correctedCollectionIntelligence": api_collection_review.get("correctedCollectionIntelligence", []),
            "collectionCorrectionFeed": api_collection_review.get("collectionCorrectionFeed", []),
            "collectionReviewSummary": api_collection_review.get("collectionReviewSummary", {}),
            "controlledAPICollectionGate": controlled_api_collection_gate,
            "controlledAPICollectionChecks": controlled_api_collection_gate.get("controlledAPICollectionChecks", []),
            "platformIntelligenceSafetyReview": controlled_api_collection_gate.get("platformIntelligenceSafetyReview", {}),
            "controlledAPICollectionSummary": controlled_api_collection_gate.get("controlledAPICollectionSummary", {}),
            "readOnlyTrendConnector": read_only_trends,
            "platformTrends": read_only_trends.get("platformTrends", []),
            "platformTrendFeed": read_only_trends.get("platformTrendFeed", []),
            "trendConnectorSummary": read_only_trends.get("trendConnectorSummary", {}),
            "apiRateLimitGuard": api_rate_limit_guard,
            "apiRiskFeed": api_rate_limit_guard.get("apiRiskFeed", []),
            "apiUsageSummary": api_rate_limit_guard.get("apiUsageSummary", {}),
            "apiRiskSummary": api_rate_limit_guard.get("apiRiskSummary", {}),
            "apiSignalNormalization": api_signal_normalization,
            "normalizedSignals": api_signal_normalization.get("normalizedSignals", []),
            "apiNormalizedSignalFeed": api_signal_normalization.get("apiNormalizedSignalFeed", []),
            "normalizationSummary": api_signal_normalization.get("normalizationSummary", {}),
            "apiToScoutPipeline": api_to_scout_pipeline,
            "apiScoutFeed": api_to_scout_pipeline.get("apiScoutFeed", []),
            "apiScoutTrace": api_to_scout_pipeline.get("apiScoutTrace", []),
            "apiScoutPipelineSummary": api_to_scout_pipeline.get("apiScoutPipelineSummary", {}),
            "apiScoutGate": api_scout_gate,
            "apiScoutGateChecks": api_scout_gate.get("apiScoutGateChecks", []),
            "platformApiRiskReview": api_scout_gate.get("platformApiRiskReview", {}),
            "apiScoutGateSummary": api_scout_gate.get("apiScoutGateSummary", {}),
            "externalActionSandbox": external_action_sandbox,
            "externalActionQueue": external_action_sandbox.get("externalActionQueue", []),
            "externalActionFeed": external_action_sandbox.get("externalActionFeed", []),
            "externalActionSimulations": external_action_sandbox.get("externalActionSimulations", []),
            "externalActionSandboxSummary": external_action_sandbox.get("externalActionSandboxSummary", {}),
            "batchScoutRuntime": batch_scout_runtime,
            "batchScoutFeed": batch_scout_runtime.get("batchScoutFeed", []),
            "batchAnalysis": batch_scout_runtime.get("batchAnalysis", []),
            "batchPriorityRanking": batch_scout_runtime.get("batchPriorityRanking", []),
            "batchScoutSummary": batch_scout_runtime.get("batchScoutSummary", {}),
            "batchTopicClustering": batch_topic_clustering,
            "batchTrendClusters": batch_topic_clustering.get("batchTrendClusters", []),
            "batchClusterFeed": batch_topic_clustering.get("batchClusterFeed", []),
            "batchClusterSummary": batch_topic_clustering.get("batchClusterSummary", {}),
            "batchHumanReview": batch_human_review,
            "batchReviewQueue": batch_human_review.get("batchReviewQueue", []),
            "batchReviewDecisions": batch_human_review.get("batchReviewDecisions", []),
            "batchTrainingLabels": batch_human_review.get("batchTrainingLabels", []),
            "batchReviewFeed": batch_human_review.get("batchReviewFeed", []),
            "batchHumanReviewSummary": batch_human_review.get("batchHumanReviewSummary", {}),
            "runtimePatternLearning": runtime_pattern_learning,
            "patternMemory": runtime_pattern_learning.get("patternMemory", []),
            "runtimePatternFeed": runtime_pattern_learning.get("runtimePatternFeed", []),
            "patternLearningSummary": runtime_pattern_learning.get("patternLearningSummary", {}),
            "runtimeReplayTraining": runtime_replay_training,
            "replayTrainingItems": runtime_replay_training.get("replayTrainingItems", []),
            "replayMemory": runtime_replay_training.get("replayMemory", []),
            "runtimeReplayFeed": runtime_replay_training.get("runtimeReplayFeed", []),
            "replayTrainingSummary": runtime_replay_training.get("replayTrainingSummary", {}),
            "syntheticFeedbackTraining": synthetic_feedback_training,
            "syntheticTrainingDataset": synthetic_feedback_training.get("syntheticTrainingDataset", []),
            "syntheticTrainingFeed": synthetic_feedback_training.get("syntheticTrainingFeed", []),
            "syntheticTrainingSummary": synthetic_feedback_training.get("syntheticTrainingSummary", {}),
            "intelligenceAccelerationGate": intelligence_acceleration_gate,
            "intelligenceAccelerationChecks": intelligence_acceleration_gate.get("gateChecks", []),
            "runtimeIntelligenceEvolutionReview": intelligence_acceleration_gate.get("runtimeIntelligenceEvolutionReview", {}),
            "intelligenceAccelerationFeed": intelligence_acceleration_gate.get("intelligenceAccelerationFeed", []),
        }


def export_default_ui_state(root: str | Path = "runtime/runtime_state") -> dict[str, Any]:
    persistence = RuntimePersistence(root)
    return RuntimeUIBridge(RuntimeEngine(persistence=persistence)).export_ui_state()
