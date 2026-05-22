"""Persist approved and rejected personality signals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.personality_engine import PersonalityEngine
from services.runtime_persistence import utc_now_iso


class PersonalityMemoryDeposit:
    def __init__(self, root: str | Path = "runtime/personality", reviews_root: str | Path = "runtime/personality_reviews") -> None:
        self.root = Path(root)
        self.reviews_root = Path(reviews_root)
        self.memory_path = self.root / "personality_memory.json"

    def deposit(self, signal: dict[str, Any]) -> dict[str, Any]:
        memory = self.load()
        category = signal.get("category", "approved_personality")
        payload = {
            "personality_id": signal.get("personality_id", f"personality_{utc_now_iso().replace(':', '-')}"),
            "workspace": signal.get("workspace", "JAG-LAB"),
            "platform": signal.get("platform", "reddit"),
            "market": signal.get("market", "Japan"),
            "tone": signal.get("tone", "trusted_guide"),
            "style": signal.get("style", []),
            "reason": signal.get("reason", ""),
            "created_at": utc_now_iso(),
        }
        memory.setdefault(category, []).append(payload)
        if category in {"approved_personality", "best_personality", "approved_tone"}:
            memory["best_personality"] = payload
            memory.setdefault("best_tone", []).append(payload)
        if category in {"rejected_personality", "failed_personality", "rejected_tone"}:
            memory["failed_personality"] = payload
            memory.setdefault("rejected_tone", []).append(payload)
        memory["updated_at"] = utc_now_iso()
        self.root.mkdir(parents=True, exist_ok=True)
        self.memory_path.write_text(json.dumps(memory, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.write_review_report(memory)
        return payload

    def default_seed(self) -> dict[str, Any]:
        context = PersonalityEngine(self.root).build_context("JAG-LAB", "reddit", "Japan", "trusted_guide")
        self.deposit(
            {
                "category": "approved_personality",
                "workspace": "JAG-LAB",
                "platform": "reddit",
                "market": "Japan",
                "tone": "trusted_guide",
                "style": context["workspacePersonality"]["personality"],
                "reason": "JAG should sound real, credible, professional, guide-like, and non-promotional.",
            }
        )
        self.deposit(
            {
                "category": "rejected_personality",
                "workspace": "JAG-LAB",
                "platform": "tiktok",
                "market": "Japan",
                "tone": "aggressive_hook",
                "style": ["过度情绪", "硬广", "标题党"],
                "reason": "Aggressive emotional hook creates platform personality drift.",
            }
        )
        return self.load()

    def load(self) -> dict[str, Any]:
        if not self.memory_path.exists():
            return {
                "best_tone": [],
                "rejected_tone": [],
                "approved_personality": [],
                "rejected_personality": [],
            }
        return json.loads(self.memory_path.read_text(encoding="utf-8"))

    def status(self) -> dict[str, Any]:
        memory = self.load()
        if not memory.get("approved_personality"):
            memory = self.default_seed()
        current = PersonalityEngine(self.root).current_state()
        return {
            "currentPersonality": current,
            "bestPersonality": memory.get("best_personality") or {},
            "failedPersonality": memory.get("failed_personality") or {},
            "bestTone": memory.get("best_tone", [])[-5:],
            "rejectedTone": memory.get("rejected_tone", [])[-5:],
            "approvedPersonality": memory.get("approved_personality", [])[-5:],
            "rejectedPersonality": memory.get("rejected_personality", [])[-5:],
            "personalityDrift": "needs_human_review" if memory.get("failed_personality") else "clear",
        }

    def write_review_report(self, memory: dict[str, Any]) -> Path:
        self.reviews_root.mkdir(parents=True, exist_ok=True)
        path = self.reviews_root / "PERSONALITY_REVIEW_REPORT.json"
        report = {
            "created_at": utc_now_iso(),
            "best_personality": memory.get("best_personality", {}),
            "failed_personality": memory.get("failed_personality", {}),
            "approved_count": len(memory.get("approved_personality", [])),
            "rejected_count": len(memory.get("rejected_personality", [])),
        }
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return path
