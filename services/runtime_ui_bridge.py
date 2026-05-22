"""Bridge between local Runtime Engine JSON state and the control center UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.human_feedback_learning import HumanFeedbackLearning
from services.human_personality_training import HumanPersonalityTraining
from services.personality_drift_engine import PersonalityDriftEngine
from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.runtime_drift_monitor import RuntimeDriftMonitor
from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import RuntimePersistence
from services.runtime_strategy_personality import RuntimeStrategyPersonalityEngine


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
                "status": "needs_code_check" if state.get("current_error") else "clear",
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
            "opportunityRanking": [state["opportunity_score"]] if state.get("opportunity_score") else [],
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
        }


def export_default_ui_state(root: str | Path = "runtime/runtime_state") -> dict[str, Any]:
    persistence = RuntimePersistence(root)
    return RuntimeUIBridge(RuntimeEngine(persistence=persistence)).export_ui_state()
