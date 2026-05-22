"""Human feedback memory for Runtime Review and Correction decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class HumanFeedbackLearning:
    def __init__(self, root: str | Path = "runtime/review_sessions") -> None:
        self.root = Path(root)
        self.review_decisions_path = self.root / "review_decisions.json"
        self.correction_decisions_path = self.root / "correction_decisions.json"
        self.modified_outputs_path = self.root / "human_modified_outputs.json"
        self.preference_memory_path = self.root / "human_preference_memory.json"

    def record_review_decision(self, review: dict[str, Any], decision: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        details = details or {}
        payload = {
            "decision_id": f"decision_{utc_now_iso().replace(':', '-')}",
            "review_id": review.get("review_id"),
            "workspace": review.get("workspace", "JAG-LAB"),
            "cycle": review.get("cycle", "JAG-LAB-CYCLE-0001"),
            "target_type": review.get("target_type", "strategy"),
            "decision": decision,
            "reason": details.get("reason", ""),
            "human_modified_version": details.get("human_modified_version", ""),
            "ai_output": review.get("content", {}),
            "created_at": utc_now_iso(),
        }
        self._append_json(self.review_decisions_path, payload)
        if decision == "modify":
            self._append_json(
                self.modified_outputs_path,
                {
                    "review_id": payload["review_id"],
                    "workspace": payload["workspace"],
                    "target_type": payload["target_type"],
                    "human_modified_version": payload["human_modified_version"],
                    "created_at": payload["created_at"],
                },
            )
        self._update_memory(payload)
        return payload

    def record_correction(self, correction: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        payload = {
            "correction_id": correction.get("correction_id"),
            "workspace": context.get("workspace", "JAG-LAB"),
            "industry_pack": context.get("industry_pack", "Travel Pack / Lab"),
            "affected_runtime_stage": context.get("affected_runtime_stage", "Human Review"),
            "correction_type": context.get("correction_type", correction.get("target_type", "learning")),
            "target_id": correction.get("target_id", "unknown"),
            "correction_reason": context.get("correction_reason", correction.get("reason", "")),
            "created_at": correction.get("created_at", utc_now_iso()),
            "status": correction.get("status", "rejected"),
        }
        self._append_json(self.correction_decisions_path, payload)
        self._update_memory({"decision": "correct", "target_type": payload["correction_type"], "reason": payload["correction_reason"]})
        return payload

    def summary(self) -> dict[str, Any]:
        memory = self._load_object(self.preference_memory_path)
        decisions = self._load_list(self.review_decisions_path)
        corrections = self._load_list(self.correction_decisions_path)
        today = utc_now_iso()[:10]
        decisions_today = [item for item in decisions if str(item.get("created_at", "")).startswith(today)]
        return {
            "humanDecisionsToday": len(decisions_today),
            "topCorrectedMistakes": memory.get("top_corrected_mistakes", []),
            "mostRejectedStrategy": self._top_key(memory.get("rejected", {})),
            "mostApprovedReplyStyle": self._top_key(memory.get("approved", {})),
            "correctionHistory": corrections[-20:],
            "humanPreferenceMemory": memory,
        }

    def _update_memory(self, decision: dict[str, Any]) -> None:
        memory = self._load_object(self.preference_memory_path)
        memory.setdefault("approved", {})
        memory.setdefault("rejected", {})
        memory.setdefault("modified", {})
        memory.setdefault("corrected", {})
        memory.setdefault("top_corrected_mistakes", [])
        bucket_name = {
            "approve": "approved",
            "approved": "approved",
            "reject": "rejected",
            "rejected": "rejected",
            "modify": "modified",
            "modified": "modified",
            "correct": "corrected",
        }.get(decision.get("decision"), "corrected")
        target_type = decision.get("target_type", "unknown")
        bucket = memory[bucket_name]
        bucket[target_type] = int(bucket.get(target_type, 0)) + 1
        if bucket_name in {"rejected", "corrected"}:
            reason = decision.get("reason") or decision.get("correction_reason") or ""
            mistake = {"target_type": target_type, "reason": reason, "count": bucket[target_type]}
            memory["top_corrected_mistakes"] = [mistake] + [
                item for item in memory["top_corrected_mistakes"] if item.get("target_type") != target_type
            ]
            memory["top_corrected_mistakes"] = memory["top_corrected_mistakes"][:10]
        memory["updated_at"] = utc_now_iso()
        self.root.mkdir(parents=True, exist_ok=True)
        self.preference_memory_path.write_text(json.dumps(memory, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _append_json(self, path: Path, payload: dict[str, Any]) -> None:
        items = self._load_list(path)
        items.append(payload)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _top_key(values: dict[str, Any]) -> str:
        if not values:
            return "none"
        return max(values.items(), key=lambda item: int(item[1]))[0]

    @staticmethod
    def _load_list(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_object(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
