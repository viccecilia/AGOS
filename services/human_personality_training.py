"""Human training layer for AGOS operating personality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.personality_memory_deposit import PersonalityMemoryDeposit
from services.runtime_persistence import utc_now_iso


class HumanPersonalityTraining:
    def __init__(self, root: str | Path = "runtime/personality_training") -> None:
        self.root = Path(root)
        self.events_path = self.root / "human_personality_training_events.json"
        self.preference_path = self.root / "human_personality_preference_memory.json"
        self.deposit = PersonalityMemoryDeposit()

    def approve(self, personality: dict[str, Any]) -> dict[str, Any]:
        event = self._record("approve", personality)
        self.deposit.deposit({**personality, "category": "approved_personality", "reason": personality.get("reason", "Approved by human personality training.")})
        self._update_preference(event)
        return event

    def reject(self, personality: dict[str, Any]) -> dict[str, Any]:
        event = self._record("reject", personality)
        self.deposit.deposit({**personality, "category": "rejected_personality", "reason": personality.get("reason", "Rejected by human personality training.")})
        self._update_preference(event)
        return event

    def modify(self, personality: dict[str, Any], modified_personality: dict[str, Any]) -> dict[str, Any]:
        event = self._record("modify", personality, modified_personality)
        self.deposit.deposit(
            {
                **modified_personality,
                "category": "approved_personality",
                "reason": modified_personality.get("reason", "Human modified this personality and approved the modified version."),
            }
        )
        self._update_preference(event)
        return event

    def summary(self) -> dict[str, Any]:
        return {
            "events": self._load_list(self.events_path)[-20:],
            "preferenceMemory": self._load_object(self.preference_path),
        }

    def _record(self, decision: str, personality: dict[str, Any], modified_personality: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {
            "event_id": f"human_personality_{utc_now_iso().replace(':', '-')}",
            "decision": decision,
            "workspace": personality.get("workspace", "JAG-LAB"),
            "platform": personality.get("platform", "reddit"),
            "market": personality.get("market", "Japan"),
            "tone": personality.get("tone", "trusted_guide"),
            "style": personality.get("style", []),
            "reason": personality.get("reason", ""),
            "original_personality": personality,
            "modified_personality": modified_personality or {},
            "created_at": utc_now_iso(),
        }
        events = self._load_list(self.events_path)
        events.append(event)
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_path.write_text(json.dumps(events, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return event

    def _update_preference(self, event: dict[str, Any]) -> None:
        memory = self._load_object(self.preference_path)
        memory.setdefault("approved_personality", {})
        memory.setdefault("rejected_personality", {})
        memory.setdefault("modified_personality", {})
        bucket = {
            "approve": "approved_personality",
            "reject": "rejected_personality",
            "modify": "modified_personality",
        }[event["decision"]]
        key = f"{event['workspace']}::{event['platform']}::{event['tone']}"
        memory[bucket][key] = int(memory[bucket].get(key, 0)) + 1
        memory["last_decision"] = event
        memory["updated_at"] = utc_now_iso()
        self.root.mkdir(parents=True, exist_ok=True)
        self.preference_path.write_text(json.dumps(memory, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

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
