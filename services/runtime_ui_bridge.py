"""Bridge between local Runtime Engine JSON state and the control center UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.cross_platform_expansion_engine import CrossPlatformExpansionEngine
from services.daily_question_import_engine import DailyQuestionImportEngine
from services.human_feedback_learning import HumanFeedbackLearning
from services.human_personality_training import HumanPersonalityTraining
from services.heat_detection_engine import HeatDetectionEngine
from services.personality_drift_engine import PersonalityDriftEngine
from services.personality_isolation_engine import PersonalityIsolationEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.personality_evolution_gate import PersonalityEvolutionGate
from services.personality_review_session import PersonalityReviewSession
from services.real_reply_attempt_engine import RealReplyAttemptEngine
from services.patrol_group_engine import PatrolGroupEngine
from services.keyword_expansion_engine import KeywordExpansionEngine
from services.runtime_drift_monitor import RuntimeDriftMonitor
from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import RuntimePersistence
from services.runtime_strategy_personality import RuntimeStrategyPersonalityEngine
from services.strategic_interpretation_engine import StrategicInterpretationEngine
from services.runtime_trainer_dashboard import RuntimeTrainerDashboard
from services.strategy_evolution_engine import StrategyEvolutionEngine
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
        }


def export_default_ui_state(root: str | Path = "runtime/runtime_state") -> dict[str, Any]:
    persistence = RuntimePersistence(root)
    return RuntimeUIBridge(RuntimeEngine(persistence=persistence)).export_ui_state()
