"""Runtime memory deposit writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


MEMORY_LIBRARIES = [
    "Question Inbox",
    "Pain Point Library",
    "Answer Branch Library",
    "Learning Events",
    "Workspace Memory",
    "Industry Pack Memory",
    "Strategy Memory",
]


class RuntimeMemoryDeposit:
    def __init__(self, root: str | Path = "runtime/runtime_state") -> None:
        self.root = Path(root) / "memory_deposits"

    def deposit(self, workspace: str, library: str, content: dict[str, Any], reason: str = "") -> dict[str, Any]:
        if library not in MEMORY_LIBRARIES:
            raise ValueError(f"Unknown memory library: {library}")
        payload = {
            "deposit_id": f"{workspace}_{library.lower().replace(' ', '_')}_{utc_now_iso().replace(':', '-')}",
            "workspace": workspace,
            "library": library,
            "content": content,
            "reason": reason,
            "created_at": utc_now_iso(),
        }
        path = self.root / workspace / f"{payload['deposit_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return payload

    def deposit_runtime_result(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        workspace = state.get("workspace", "jag_app_growth")
        cycle = state.get("cycle", "CYCLE-001")
        stage = state.get("current_stage", "Scout")
        base = {"cycle": cycle, "stage": stage, "runtime_status": state.get("status")}
        return [
            self.deposit(workspace, "Question Inbox", {**base, "signal": "runtime question candidate"}, "Runtime cycle captured candidate question context."),
            self.deposit(workspace, "Pain Point Library", {**base, "pain_point": "Tokyo transport anxiety"}, "Runtime detected a pain cluster."),
            self.deposit(workspace, "Answer Branch Library", {**base, "branch": "helpful rescue answer"}, "Runtime prepared answer branch direction."),
            self.deposit(workspace, "Learning Events", {**base, "learning": "sample data must not become real feedback"}, "Runtime recorded learning boundary."),
            self.deposit(workspace, "Workspace Memory", {**base, "workspace_scope": workspace}, "Runtime preserved workspace scope."),
            self.deposit(workspace, "Industry Pack Memory", {**base, "industry_pack": state.get("industry_pack")}, "Runtime preserved industry pack scope."),
            self.deposit(workspace, "Strategy Memory", {**base, "strategy": "rescue-first helpful answer"}, "Runtime deposited strategy direction."),
        ]

    def list(self, workspace: str | None = None) -> list[dict[str, Any]]:
        root = self.root / workspace if workspace else self.root
        if not root.exists():
            return []
        return sorted(
            [json.loads(path.read_text(encoding="utf-8")) for path in root.rglob("*.json")],
            key=lambda item: item["created_at"],
        )
